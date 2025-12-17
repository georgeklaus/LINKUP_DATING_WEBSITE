#!/usr/bin/env python3
import os
import django
import json
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'luchat.settings')
django.setup()

# Allow the test client host used by Django tests
from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS += ['testserver']

from django.test import Client
from django.contrib.auth import get_user_model
from payments.models import CoinPackage, Transaction

User = get_user_model()

# Ensure a coin package exists
pkg, _ = CoinPackage.objects.get_or_create(amount=100, defaults={'coins':100,'description':'Test package'})

# Create users
user, _ = User.objects.get_or_create(username='pay_user')
user.set_password('testpass')
user.gender='M'
user.orientation='straight'
user.coins=0
user.save()

# Create Transaction with mpesa_code to simulate callback
merchant_id = f"TEST_MERCHANT_{uuid.uuid4().hex[:12]}"
transaction = Transaction.objects.create(
    user=user,
    package=pkg,
    mpesa_code=merchant_id,
    phone_number='0712345678',
    amount=pkg.amount,
    coins=pkg.coins,
    status='pending'
)

# Call mpesa_callback with success payload
c = Client()
payload = {
    'ResultCode': 0,
    'MerchantRequestID': merchant_id,
    'MpesaReceiptNumber': 'MPESA12345'
}
resp = c.post('/payments/mpesa-callback/', data=json.dumps(payload), content_type='application/json')
print('Callback status:', resp.status_code, resp.content)

# Reload transaction and user
transaction.refresh_from_db()
user.refresh_from_db()
print('Transaction status:', transaction.status)
print('User coins:', user.coins)
