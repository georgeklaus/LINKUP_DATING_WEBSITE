from django.db import models
from django.conf import settings
from django.utils import timezone

class CoinPackage(models.Model):
    amount = models.IntegerField(unique=True)
    coins = models.IntegerField()
    description = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'coin_packages'
        ordering = ['amount']
    
    def __str__(self):
        return f"{self.amount} KES = {self.coins} Coins"

class Transaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    package = models.ForeignKey(CoinPackage, on_delete=models.CASCADE)
    mpesa_code = models.CharField(max_length=50, blank=True)
    phone_number = models.CharField(max_length=15)
    amount = models.IntegerField()
    coins = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'transactions'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['status', 'created_at']),
        ]

class ProfileView(models.Model):
    viewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='viewed_profiles')
    viewed_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile_views')
    cost = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'profile_views'
        indexes = [
            models.Index(fields=['viewer', 'created_at']),
            models.Index(fields=['viewed_user', 'created_at']),
        ]


class RawWebhook(models.Model):
    """Store raw incoming webhook payloads for auditing, verification and replay.

    - `provider` is a short name like 'megapay' or 'mpesa'.
    - `provider_reference` is the provider's request id (MerchantRequestID / merchant_request_id).
    - `payload` stores the JSON body the provider POSTed.
    - `headers` stores relevant headers as JSON for debugging/verification.
    - `received_at` is when we received it.
    - `processed` indicates whether we've applied the webhook to a Transaction.
    - `transaction` optional FK to the `Transaction` that was matched/processed.
    """

    provider = models.CharField(max_length=50)
    provider_reference = models.CharField(max_length=100, blank=True, db_index=True)
    payload = models.JSONField()
    headers = models.JSONField(null=True, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    transaction = models.ForeignKey('Transaction', null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = 'raw_webhooks'
        indexes = [
            models.Index(fields=['provider', 'provider_reference']),
            models.Index(fields=['processed', 'received_at']),
        ]

    def __str__(self):
        return f"RawWebhook(provider={self.provider} ref={self.provider_reference} processed={self.processed})"