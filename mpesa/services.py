import time
import suds
import hashlib
import base64
import xml.etree.ElementTree as ET

import logging

logging.basicConfig(level=logging.WARN)
logging.getLogger('suds').setLevel(logging.WARN)


class PaymentService(object):

    wsdl = 'https://www.safaricom.co.ke/mpesa_online/lnmo_checkout_server.php?wsdl'
    demo = False
    demo_merchant_id = '898998'
    demo_timestamp = '20160510161908'
    demo_password = 'ZmRmZDYwYzIzZDQxZDc5ODYwMTIzYjUxNzNkZDMwMDRjNGRkZTY2ZDQ3ZTI0YjVjODc4ZTExNTNjMDA1YTcwNw=='

    def __init__(self, merchant_id='demo', merchant_passkey='demo', debug=False):
        if merchant_id == 'demo':
            self.demo = True
            self.merchant_id = self.demo_merchant_id
        else:
            self.merchant_id = merchant_id

        self.merchant_passkey = merchant_passkey
        self.debug = debug
        self.client = suds.client.Client(self.wsdl)

        # Make sure locations for methods are correctly set
        self.client.service.processCheckOut.method.location = self.wsdl
        self.client.service.confirmTransaction.method.location = self.wsdl
        self.client.service.LNMOResult.method.location = self.wsdl
        self.client.service.transactionStatusQuery.method.location = self.wsdl

    def _generate_password(self, timestamp):
        if self.demo:
            return self.demo_password
        key = "{0}{1}{2}".format(self.merchant_id, self.merchant_passkey, timestamp)
        return base64.b64encode(hashlib.sha256(key).hexdigest().upper())

    def _request_header(self, timestamp):
        data = self.client.factory.create('tns:CheckOutHeader')
        data.MERCHANT_ID = self.merchant_id
        data.TIMESTAMP = timestamp
        data.PASSWORD = self._generate_password(timestamp=timestamp)
        return data

    def confirm_transaction(self, transaction_id):
        if self.demo:
            timestamp = self.demo_timestamp
        else:
            timestamp = time.time()

        header = self._request_header(timestamp=timestamp)
        self.client.set_options(soapheaders=header)

        response = self.client.service.confirmTransaction(
            transaction_id
        )
        return response


    def transaction_status_query(self, transaction_id):
        if self.demo:
            timestamp = self.demo_timestamp
        else:
            timestamp = time.time()

        header = self._request_header(timestamp=timestamp)
        self.client.set_options(soapheaders=header)

        response = self.client.service.transactionStatusQuery(
            transaction_id
        )
        return response


    def checkout_request(self):
        merchant_transaction_id = 'order-9876-{0}'.format(time.time())
        reference_id = 'project-1234'
        msisdn = '254700000000'
        amount = 500
        enc_params = None
        callback_url = 'http://localhost:8000/payments_mpesa/status'
        callback_method = 'xml'
        if self.demo:
            timestamp = self.demo_timestamp
        else:
            timestamp = time.time()

        header = self._request_header(timestamp=timestamp)
        self.client.set_options(soapheaders=header)

        response = self.client.service.processCheckOut(
            merchant_transaction_id,
            reference_id,
            amount,
            msisdn,
            enc_params,
            callback_url,
            callback_method,
            timestamp
        )
        return response
