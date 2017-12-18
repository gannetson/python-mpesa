import os
from unittest import TestCase

from mpesa.services import PaymentService


class TestRequests(TestCase):

    def setUp(self):
        key = os.environ.get('MPESA_CONSUMER_KEY')
        password = os.environ.get('MPESA_CONSUMER_SECRET')
        self.service = PaymentService(consumer_key=key,
                                 consumer_password=password,
                                 live=False,
                                 debug=True)

    def test_sandbox_illegal_amounts(self):

        response = self.service.process_request(
            phone_number='254700000000',
            amount=500000000000,
            callback_url='http://my-callback.com/mpesa/status',
            reference='order-1234-az',
            description='payment for order'
        )

        self.assertEqual(response['status'], 'failed')
        self.assertEqual(response['error'],
                         'Bad Request - Invalid Amount')

        response = self.service.process_request(
            phone_number='254700000000',
            amount=-500,
            callback_url='http://my-callback.com/mpesa/status',
            reference='order-1234-az',
            description='payment for order'
        )

        self.assertEqual(response['status'], 'failed')
        self.assertEqual(response['error'],
                         'Bad Request - Invalid Amount')

    def test_sandbox_illegal_properties(self):

        response = self.service.process_request(
            phone_number='2547000000',
            amount=500,
            callback_url='http://my-callback.com/mpesa/status',
            reference='order-1234-az',
            description='Some description'
        )

        self.assertEqual(response['status'], 'failed')
        self.assertEqual(response['error'],
                         'Bad Request - Invalid Party B')

        response = self.service.process_request(
            phone_number='254700000000',
            amount=500,
            callback_url='http://my-callback.com/mpesa/status',
            reference='order-1234-az',
            description='very very long description. very very long description. '
                        'very very long description. very very long description. '
                        'very very long description. very very long description. '
                        'very very long description. very very long description. '
                        'very very long description. very very long description.'
        )

        self.assertEqual(response['status'], 'failed')
        self.assertEqual(response['error'],
                         'Bad Request - Invalid Remarks')

        response = self.service.process_request(
            phone_number='254700000000',
            amount=500,
            callback_url='',
            reference='order-1234-az',
            description='Some description.'
        )

        self.assertEqual(response['status'], 'failed')
        self.assertEqual(response['error'],
                         'Bad Request - Invalid ResultURL')

    def test_sandbox_successful_request(self):

        response = self.service.process_request(
            phone_number='254700000000',
            amount=500,
            callback_url='http://my-callback.com/mpesa/status',
            reference='order-1234-az',
            description='payment for order'
        )

        self.assertEqual(response['status'], 'started')
        self.assertEqual(response['response']['CustomerMessage'],
                         'Success. Request accepted for processing')
        self.assertEqual(response['response']['ResponseCode'], '0')

        transaction_id = response['request_id']

        # Check transaction status
        response = self.service.query_request(transaction_id)
        self.assertEqual(response['response']['ResponseDescription'],
                         'The service request has been accepted successsfully')
        self.assertEqual(response['response']['CheckoutRequestID'], transaction_id)
        self.assertEqual(response['response']['ResponseCode'], '0')
        self.assertEqual(response['response']['ResultCode'], '1101')
        self.assertEqual(response['status'], 'started')

        # Register url
        response = self.service.register_url(validation_url='http://mp.requestcatcher.com/')
        self.assertEqual(response['status'], 'ok')

        # Simulate payment
        response = self.service.simulate_transaction(amount=500,
                                                phone_number='254700000000',
                                                reference=transaction_id)
        self.assertEqual(response['response']['ResponseDescription'],
                         'Accept the service request successfully.')
        self.assertEqual(response['status'], 'pending')

        # Check confirm transaction again. It should be successful now.
        response = self.service.query_request(transaction_id)
        self.assertEqual(response['response']['ResponseDescription'],
                         'The service request has been accepted successsfully')
        self.assertEqual(response['response']['CheckoutRequestID'], transaction_id)
        self.assertEqual(response['response']['ResponseCode'], '0')
        self.assertEqual(response['response']['ResultCode'], '1101')
        self.assertEqual(response['status'], 'started')
