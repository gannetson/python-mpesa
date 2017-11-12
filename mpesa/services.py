import base64
import hashlib
import logging
import requests
import suds
import time

from django.utils.timezone import now

logging.basicConfig(level=logging.WARN)
logging.getLogger('suds').setLevel(logging.WARN)


class PaymentService(object):

    test_server = "https://sandbox.safaricom.co.ke"
    live_server = "https://api.safaricom.co.ke"

    server = live_server

    access_token_path = '/oauth/v1/generate?grant_type=client_credentials'
    process_request_path = '/mpesa/stkpush/v1/processrequest'
    query_request_path = '/mpesa/stkpushquery/v1/query'

    balance_request_path = '/mpesa/accountbalance/v1/query'

    test_shortcode = '174379'
    test_passphrase = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'

    live = False

    access_token = None

    code_mapping = {
        '1037': 'timout',
        '1001': 'started',
    }

    def __init__(self, consumer_key, consumer_password, shortcode=None, passphrase=None, live=False):
        self.consumer_key = consumer_key
        self.consumer_password = consumer_password
        self.live = live
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
        timestamp = now().strftime('%Y%m%d%H%M%S')
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
        import ipdb; ipdb.set_trace()
        response = requests.post(url, json=request, headers=headers)

        # SUCCESS example
        # u'CustomerMessage': u'Success. Request accepted for processing',
        # u'CheckoutRequestID': u'ws_CO_13102017145401020',
        # u'ResponseDescription': u'Success. Request accepted for processing',
        # u'MerchantRequestID': u'29122-733990-1',
        # u'ResponseCode': u'0'

        # ERROR example
        # u'errorCode': u'400.002.05',
        # u'errorMessage': u'Invalid Request Payload',
        # u'requestId': u'29128-733679-1'

        data = response.json()

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
        timestamp = now().strftime('%Y%m%d%H%M%S')
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
