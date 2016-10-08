from unittest import TestCase

from mpesa.services import PaymentService


class TestReponse(TestCase):

    def test_response(self):
        service = PaymentService(merchant_id=123, merchant_passkey='topsecret')
        file = open('mpesa/tests/files/response-success.xml')
        xml = file.read()
        data = service._parse_checkout_response(xml)
        self.assertEqual(data['description'], 'Success')
        self.assertEqual(data['mpesa_txn'], 'cce3d32e0159c1e62a9ec45b67676200')

    def test_request(self):
        service = PaymentService(merchant_id='demo', merchant_passkey='demo')
        response = service.checkout_request()
        self.assertEqual(response.DESCRIPTION, 'Success')
        self.assertEqual(response.RETURN_CODE, '00')
        self.assertEqual(response.CUST_MSG, ("To complete this transaction, enter your "
                                             "PIN on your handset. If you don't have a "
                                             "PIN, press 0 and follow the instructions."))
