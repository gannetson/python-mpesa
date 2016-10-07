from unittest import TestCase

from mpesa.services import PaymentService


class TestReponse(TestCase):
    def test_is_string(self):
        service = PaymentService(merchant_id=123, merchant_passkey='topsecret')
        file = open('mpesa/tests/files/response-success.xml')
        xml = file.read()
        data = service._parse_checkout_response(xml)
        self.assertEqual(data['description'], 'Success')
        self.assertEqual(data['mpesa_txn'], 'cce3d32e0159c1e62a9ec45b67676200')
