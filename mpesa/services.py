import base64
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
    register_url_path = '/mpesa/c2b/v1/registerurl'

    test_shortcode = '174379'
    test_passphrase = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'

    live = False

    access_token = None

    code_mapping = {
        '1037': 'timeout',
        '1001': 'started',
        '1101': 'started',
    }

    def __init__(self, consumer_key, consumer_password, shortcode=None, passphrase=None, live=False, debug=False):
        self.consumer_key = consumer_key
        self.consumer_password = consumer_password
        self.live = live
        self.debug = debug
        if debug:
            logger.setLevel('DEBUG')
            logger.debug('Initiated M-Pesa Payment Service')
        if not live:
            self.server = self.test_server
            self.shortcode = self.test_shortcode
            self.passphrase = self.test_passphrase
        else:
            self.shortcode = shortcode
            self.passphrase = passphrase

    def get_mapped_status(self, code):
        try:
            return self.code_mapping[code]
        except KeyError:
            logger.warn('Could not map status code {}'.format(code))
            return 'unknown'

    def get_access_token(self):
        url = self.server + self.access_token_path
        response = requests.get(url, auth=(self.consumer_key, self.consumer_password))
        if self.debug:
            logger.debug('Getting access token')
            logger.debug('URL: {}'.format(url))
        if response.status_code == 200:
            data = response.json()
            self.access_token = data['access_token']
            return self.access_token
        else:
            return None

    def _generate_password(self, timestamp):
        string = self.shortcode + self.passphrase + timestamp
        return base64.b64encode(string)

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
            logging.debug('Response {}: {}'.format(response.status_code, data))

        if response.status_code == 200:
            return {
                'response': data,
                'status': 'started',
                'request_id': data['CheckoutRequestID']
            }
        else:
            return {
                'response': data,
                'status': 'failed',
                'error': data['errorMessage'],
                'request_id': data['requestId']
            }

    def query_request(self, request_id):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        access_token = self.get_access_token()
        if not access_token:
            return {
                'response': {},
                'status': 'failed',
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
            return {
                'response': data,
                'status': self.get_mapped_status(data['ResultCode']),
                'request_id': request_id
            }
        else:
            return {
                'response': data,
                'status': 'failed',
                'error': data['errorMessage'],
            }

    def transaction_status_request(self, phone_number, reference):
        access_token = self.get_access_token()

        if not access_token:
            return {
                'response': {},
                'status': 'failed',
                'error': 'Could not get access token',
                'request_id': reference
            }

        timeout_url = 'https://api.twende.co.ke/payments/update-timeout'
        result_url = 'https://api.twende.co.ke/payments/update-result'

        headers = {"Authorization": "Bearer %s" % access_token}
        request = {
            "CommandID": 'TransactionStatusQuery',
            "PartyA": phone_number,
            "IdentifierType": 'MSISDN',
            "Remarks": "Payment for Twende ride",
            "Initiator": self.shortcode,
            "SecurityCredential": '',
            "QueueTimeOutURL": timeout_url,
            "ResultURL": result_url,
            "TransactionID": reference,
            "OriginalConversationID": reference,
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
            status = 'started'
            if data['ResultCode'] == '1001':
                status = 'settled'
            return {
                'response': data,
                'status': status,
                'request_id': reference
            }
        else:
            status = 'started'

            return {
                'response': data,
                'status': status,
                'error': data['Envelope']['Body']['Fault']['faultstring'],
                'request_id': reference
            }

    def simulate_transaction(self, amount, phone_number, reference, shortcode=None):
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
            "CommandID": 'CustomerBuyGoodsOnline',
            "Amount": str(int(amount)),
            "Msisdn": phone_number,
            "BillRefNumber": reference,
            "ShortCode": shortcode
        }
        url = self.server + self.simulate_transaction_path
        response = requests.post(url, json=request, headers=headers)
        data = response.json()

        if self.debug:
            logging.debug('URL: {}'.format(url))
            logging.debug('Request payload:\n {}'.format(request))
            logging.debug('Response {}:\n {}'.format(response.status_code, data))

        if response.status_code == 200:
            return {
                'response': data,
                'status': 'pending',
            }
        else:
            return {
                'response': data,
                'status': 'failed',
                'error': data['errorMessage'],
            }

    def register_url(self, validation_url, confirmation_url=None, response_type="Completed", shortcode=None):
        access_token = self.get_access_token()
        if not confirmation_url:
            confirmation_url = validation_url
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
            "ValidationURL": validation_url,
            "ConfirmationURL": confirmation_url,
            "ResponseType": response_type,
            "ShortCode": shortcode
        }
        url = self.server + self.register_url_path
        response = requests.post(url, json=request, headers=headers)
        data = response.json()

        if self.debug:
            logging.debug('URL: {}'.format(url))
            logging.debug('Request payload:\n {}'.format(request))
            logging.debug('Response {}:\n {}'.format(response.status_code, data))

        if response.status_code == 200:
            return {
                'response': data,
                'status': 'ok',
            }
        else:
            return {
                'response': data,
                'status': 'failed',
                'error': data['errorMessage'],
            }
