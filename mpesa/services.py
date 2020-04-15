import base64
import hashlib
import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)


class PaymentService(object):

    test_server = "https://sandbox.safaricom.co.ke"
    live_server = "https://api.safaricom.co.ke"

    server = live_server

    access_token_path = '/oauth/v1/generate?grant_type=client_credentials'
    process_request_path = '/mpesa/stkpush/v1/processrequest'
    query_request_path = '/mpesa/stkpushquery/v1/query'
    transaction_status_path = '/mpesa/transactionstatus/v1/query'
    simulate_transaction_path = '/mpesa/c2b/v1/simulate'

    balance_request_path = '/mpesa/accountbalance/v1/query'

    test_shortcode = '174379'
    test_passphrase = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'

    live = False

    access_token = None

    code_mapping = {
        '1037': 'timout',
        '1001': 'started',
    }

    def __init__(self, consumer_key, consumer_password, shortcode=None, passphrase=None, live=False, debug=False):
        self.consumer_key = consumer_key
        self.consumer_password = consumer_password
        self.live = live
        self.debug = debug
        if debug:
            logger.debug('Initiated M-Pesa Payment Service')
        if not live:
            self.server = self.test_server
            self.shortcode = self.test_shortcode
            self.passphrase = self.test_passphrase
        else:
            self.shortcode = shortcode
            self.passphrase = passphrase

    def get_access_token(self):
        url = self.server + self.access_token_path
        response = requests.get(url, auth=(self.consumer_key, self.consumer_password))

        if response.status_code == 200:
            data = response.json()
            self.access_token = data['access_token']
            return self.access_token
        else:
            return None

    def _generate_password(self, timestamp):
        string = self.shortcode + self.passphrase + timestamp
        return string.decode('utf-8')

    def process_request(self, phone_number=None, amount=None,
                        callback_url=None, reference="", description=""):
        access_token = self.get_access_token()
        if not access_token:
            return {
                'response': {},
                'status': 'failed',
                'error': 'Could not get access token',
                'request_id': ''
            }

        headers = {"Authorization": "Bearer %s" % access_token}
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        request = {
            "BusinessShortCode": self.shortcode,
            "Password": self._generate_password(timestamp),
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": str(int(amount)),
            "PartyA": phone_number,
            "PartyB": str(self.shortcode),
            "PhoneNumber": phone_number,
            "CallBackURL": callback_url,
            "AccountReference": reference,
            "TransactionDesc": description
        }
        url = self.server + self.process_request_path
        response = requests.post(url, json=request, headers=headers)
        data = response.json()
        if self.debug:
            logging.debug('URL: {}'.format(url))
            logging.debug('Request payload:\n {}'.format(request))
            logging.debug('Response {}:\n {}'.format(response.status_code, data))

        if response.status_code == 200:
            return {
                'response': data,
                'status': 'Started',
                'request_id': data['CheckoutRequestID']
            }
        else:
            return {
                'response': data,
                'status': 'Failed',
                'error': data['errorMessage'],
                'request_id': data['requestId']
            }

    def query_request(self, request_id):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        access_token = self.get_access_token()
        if not access_token:
            return {
                'response': {},
                'status': 'Failed',
                'error': 'Could not get access token',
                'request_id': ''
            }

        headers = {"Authorization": "Bearer %s" % access_token}
        request = {
            "BusinessShortCode": self.shortcode,
            "Password": self._generate_password(timestamp),
            "Timestamp": timestamp,
            "CheckoutRequestID": request_id
        }
        url = self.server + self.query_request_path
        response = requests.post(url, json=request, headers=headers)

        data = response.json()

        if self.debug:
            logging.debug('URL: {}'.format(url))
            logging.debug('Request payload:\n {}'.format(request))
            logging.debug('Response {}:\n {}'.format(response.status_code, data))

        if response.status_code == 200:
            if data.get('errorCode', None):
                return {
                    'response': data,
                    'status': 'Started',
                    'error': data['errorMessage'],
                    'request_id': data['requestId']
                }

            if data.get('ResponseCode', None) == '0':
                return {
                    'response': data,
                    'status': 'Success',
                    'request_id': data['CheckoutRequestID']
                }
            return {
                'response': data,
                'status': 'Started',
                'request_id': data['CheckoutRequestID']
            }

        else:
            return {
                'response': data,
                'status': 'Failed',
                'error': data['errorMessage'],
                'request_id': data['requestId']
            }

    def transaction_status_request(self, phone_number, reference, result_url, timeout_url=None):
        if not timeout_url:
            timeout_url = result_url
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        access_token = self.get_access_token()
        password = self._generate_password(timestamp)

        if not access_token:
            return {
                'response': {},
                'status': 'failed',
                'error': 'Could not get access token',
                'request_id': ''
            }

        headers = {"Authorization": "Bearer %s" % access_token}
        request = {
            "CommandID": 'TransactionStatusQuery',
            "PartyA": self.shortcode,
            "IdentifierType": "4",
            "Remarks": "Payment for Twende ride",
            "Initiator": self.shortcode,
            "Timestamp": timestamp,
            "QueueTimeOutURL": timeout_url,
            "ResultURL": result_url,
            "SecurityCredential": password,
            "TransactionID": reference,
            "OriginalConversationID": '',
            "Occasion": '',
        }
        url = self.server + self.transaction_status_path
        response = requests.post(url, json=request, headers=headers)
        data = response.json()
        if self.debug:
            logging.debug('URL: {}'.format(url))
            logging.debug('Request payload:\n {}'.format(request))
            logging.debug('Response {}:\n {}'.format(response.status_code, data))

        if response.status_code == 200:
            if data.get('errorCode', None):
                return {
                    'response': data,
                    'status': 'Started',
                    'error': data['errorMessage'],
                    'request_id': data['requestId']
                }

            if data.get('ResponseCode', None) == '0':
                return {
                    'response': data,
                    'status': 'Success',
                    'request_id': data['CheckoutRequestID']
                }

        else:
            return {
                'response': data,
                'status': 'Failed',
                'error': data['Envelope']['Body']['Fault']['faultstring'],
            }

    def simulate_transaction(self, amount, phone_number, reference, shortcode=None):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        access_token = self.get_access_token()
        if not shortcode:
            shortcode = self.shortcode

        if not access_token:
            return {
                'response': {},
                'status': 'failed',
                'error': 'Could not get access token',
                'request_id': ''
            }

        headers = {"Authorization": "Bearer %s" % access_token}
        request = {
            "CommandID": 'CustomerPayBillOnline',
            "Amount": str(int(amount)),
            "Msisdn": phone_number,
            "BillRefNumber": reference,
            "ShortCode": shortcode
        }
        url = self.server + self.query_request_path
        response = requests.post(url, json=request, headers=headers)
        data = response.json()

        if self.debug:
            logging.debug('URL: {}'.format(url))
            logging.debug('Request payload:\n {}'.format(request))
            logging.debug('Response {}:\n {}'.format(response.status_code, data))

        if response.status_code == 200:
            status = 'started'
            if data['ResultCode'] == '1001':
                status = 'settled'
            return {
                'response': data,
                'status': status,
            }
        else:
            status = 'started'

            return {
                'response': data,
                'status': status,
                'error': data['errorMessage'],
            }
