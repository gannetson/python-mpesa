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

    def _parse_checkout_response(self, xml):
        root = ET.fromstring(xml)
        ns = {
            'SOAP-ENV': "http://schemas.xmlsoap.org/soap/envelope/",
            'ns1': "tns:ns"
        }

        res = root.find(".//ns1:processCheckOutResponse", ns)

        return {
            'code': int(res.findtext('RETURN_CODE')),
            'description': res.findtext('DESCRIPTION'),
            'account': res.findtext('MSISDN'),
            'amount': res.findtext('AMOUNT'),
            'date': res.findtext('M-PESA_TRX_DATE'),
            'status': res.findtext('TRX_STATUS'),
            'mpesa_txn': res.findtext('TRX_ID'),
            'internal_txn': res.findtext('M-PESA_TRX_ID'),
            'transaction': res.findtext('MERCHANT_TRANSACTION_ID'),
            'details': res.findtext('ENC_PARAMS')
        }

    def _parse_payment_response(self, xml):
        root = ET.fromstring(xml)
        ns = {
            'SOAP-ENV': "http://schemas.xmlsoap.org/soap/envelope/",
            'ns1': "tns:ns"
        }

        res = root.find("ns1:ResultMsg", ns)

        return {
            'code': int(res.findtext('RETURN_CODE')),
            'description': res.findtext('DESCRIPTION'),
            'account': res.findtext('MSISDN'),
            'amount': res.findtext('AMOUNT'),
            'date': res.findtext('M-PESA_TRX_DATE'),
            'status': res.findtext('TRX_STATUS'),
            'mpesa_txn': res.findtext('TRX_ID'),
            'internal_txn': res.findtext('M-PESA_TRX_ID'),
            'transaction': res.findtext('MERCHANT_TRANSACTION_ID'),
            'details': res.findtext('ENC_PARAMS')
        }

    def _request_header(self, timestamp):
        data = self.client.factory.create('tns:CheckOutHeader')
        data.MERCHANT_ID = self.merchant_id
        data.TIMESTAMP = timestamp
        data.PASSWORD = self._generate_password(timestamp=timestamp)
        return data

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
