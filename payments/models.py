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