from datetime import datetime
import suds
import hashlib
import base64
import xml.etree.ElementTree as ET


class PaymentService(object):

    wsdl = 'https://www.safaricom.co.ke/mpesa_online/lnmo_checkout_server.php?wsdl'

    def __init__(self, merchant_id, merchant_passkey, debug=False):
        self.merchant_id = merchant_id
        self.merchant_passkey = merchant_passkey
        self.debug = debug
        self.client = suds.client.Client(self.wsdl)

        # Make sure locations for methods are correctly set
        self.client.service.processCheckOut.method.location = self.wsdl
        self.client.service.confirmTransaction.method.location = self.wsdl
        self.client.service.LNMOResult.method.location = self.wsdl
        self.client.service.transactionStatusQuery.method.location = self.wsdl

    def _make_password(self, timestamp):
        if not timestamp:
            timestamp = datetime.now()
        return base64.b64encode(hashlib.sha256(self.merchant_id + self.merchant_passkey + timestamp).hexdigest().upper())

    def _parse_checkout_response(self, xml):
        root = ET.fromstring(xml)
        ns = {
            'SOAP-ENV': "http://schemas.xmlsoap.org/soap/envelope/",
            'ns1': "tns:ns"
        }

        res = root.find(".//ns1:processCheckOutResponse", ns)
        print res.RETURN_CODE

        return {
            'code': int(res.RETURN_CODE),
            'description': res['DESCRIPTION'],
            'account': res['MSISDN'],
            'amount': res['AMOUNT'],
            'date': res['M-PESA_TRX_DATE'],
            'status': res['TRX_STATUS'],
            'mpesa_txn': res['TRX_ID'],
            'internal_txn': res['M-PESA_TRX_ID'],
            'transaction': res['MERCHANT_TRANSACTION_ID'],
            'details': res['ENC_PARAMS']
        }


    def _parse_payment_response(self, xml):
        root = ET.fromstring(xml)
        ns = {
            'SOAP-ENV': "http://schemas.xmlsoap.org/soap/envelope/",
            'ns1': "tns:ns"
        }

        res = root.find("ns1:ResultMsg", ns)

        return {
            'code': int(res['RETURN_CODE']),
            'description': res['DESCRIPTION'],
            'account': res['MSISDN'],
            'amount': res['AMOUNT'],
            'date': res['M-PESA_TRX_DATE'],
            'status': res['TRX_STATUS'],
            'mpesa_txn': res['TRX_ID'],
            'internal_txn': res['M-PESA_TRX_ID'],
            'transaction': res['MERCHANT_TRANSACTION_ID'],
            'details': res['ENC_PARAMS']
        }

    def _parseXMLResponse(self, op, xml):
        data = None
