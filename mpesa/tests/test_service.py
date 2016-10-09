import time
from unittest import TestCase

from mpesa.services import PaymentService


class TestRequests(TestCase):

    def test_live_request(self):
        service = PaymentService(merchant_id='demo', merchant_passkey='demo')
        response = service.checkout_request(
            merchant_transaction_id=time.time(), reference_id='project-X',
            msisdn='254700000000', amount=500, enc_params=None,
            callback_url='http://localhost:8000/mpesa/status'
        )

        self.assertEqual(response.DESCRIPTION, 'Success')
        self.assertEqual(response.RETURN_CODE, '00')
        self.assertEqual(response.CUST_MSG, ("To complete this transaction, enter your "
                                             "PIN on your handset. If you don't have a "
                                             "PIN, press 0 and follow the instructions."))

        transaction_id = response.TRX_ID

        # Check confirm transaction request too
        response = service.confirm_transaction(transaction_id)
        self.assertEqual(response.DESCRIPTION, 'Success')

        # Check transaction status
        response = service.transaction_status_query(transaction_id)
        self.assertEqual(response.TRX_STATUS, 'Pending')
        self.assertEqual(response.AMOUNT, '500')
        self.assertEqual(response.MSISDN, '254700000000')
