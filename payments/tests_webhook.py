from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.conf import settings
import json

from .models import CoinPackage, Transaction, RawWebhook


class WebhookFlowTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='tester', password='pass')
        self.client = Client()
        self.client.login(username='tester', password='pass')

        # create coin package
        self.pkg = CoinPackage.objects.create(amount=100, coins=100, description='100KES')

    def test_initiate_and_stub_flow_creates_pending(self):
        resp = self.client.post(reverse('payments:buy_coins'), {
            'package': str(self.pkg.id),
            'phone_number': '254700000000'
        })
        # redirect to pending when using local stub OR success otherwise
        self.assertIn(resp.status_code, (302, 200))
        txn = Transaction.objects.order_by('-created_at').first()
        self.assertIsNotNone(txn)
        self.assertEqual(txn.status, 'pending')

    def test_callback_persists_rawwebhook_and_processes(self):
        # create pending txn with known mpesa_code
        txn = Transaction.objects.create(
            user=self.user, package=self.pkg, phone_number='254700000000', amount=100, coins=100, status='pending', mpesa_code='REF12345'
        )

        payload = {
            'ResultCode': 0,
            'MerchantRequestID': 'REF12345',
            'MpesaReceiptNumber': 'REC123'
        }

        resp = self.client.post(reverse('payments:mpesa_callback'), data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        # raw webhook persisted
        rw = RawWebhook.objects.filter(provider_reference='REF12345').first()
        self.assertIsNotNone(rw)
        self.assertTrue(rw.processed)

        # transaction completed and user credited
        txn.refresh_from_db()
        self.assertEqual(txn.status, 'completed')
        User = get_user_model()
        u = User.objects.get(pk=self.user.pk)
        self.assertGreaterEqual(u.coins, txn.coins)

    def test_idempotent_callback_does_not_double_credit(self):
        txn = Transaction.objects.create(
            user=self.user, package=self.pkg, phone_number='254700000000', amount=100, coins=100, status='pending', mpesa_code='REFIDEMP'
        )

        payload = {
            'ResultCode': 0,
            'MerchantRequestID': 'REFIDEMP',
            'MpesaReceiptNumber': 'RECXXX'
        }

        User = get_user_model()
        u_before = User.objects.get(pk=self.user.pk)
        initial_coins = u_before.coins

        # send callback twice
        for _ in range(2):
            resp = self.client.post(reverse('payments:mpesa_callback'), data=json.dumps(payload), content_type='application/json')
            self.assertEqual(resp.status_code, 200)

        txn.refresh_from_db()
        self.assertEqual(txn.status, 'completed')
        u_after = User.objects.get(pk=self.user.pk)
        self.assertEqual(u_after.coins, initial_coins + txn.coins)
