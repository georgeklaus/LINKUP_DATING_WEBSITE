from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.utils import timezone

class CustomUser(AbstractUser):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    
    ORIENTATION_CHOICES = [
        ('straight', 'Straight'),
        ('gay', 'Gay'),
        ('lesbian', 'Lesbian'),
        ('bisexual', 'Bisexual'),
    ]
    
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    orientation = models.CharField(max_length=20, choices=ORIENTATION_CHOICES)
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', default='profiles/default.png')
    date_of_birth = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=100, blank=True)
    coins = models.IntegerField(default=0)
    is_online = models.BooleanField(default=False)
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['gender', 'orientation']),
            models.Index(fields=['is_online']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.username} ({self.get_gender_display()}, {self.orientation})"
    
    def add_coins(self, amount):
        """Add coins to user balance"""
        self.coins += amount
        self.save()
    
    def deduct_coins(self, amount):
        """Deduct coins from user balance"""
        if self.coins >= amount:
            self.coins -= amount
            self.save()
            return True
        return False
    
    def age(self):
        """Calculate user age from date of birth"""
        if self.date_of_birth:
            today = timezone.now().date()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    interests = models.TextField(blank=True)
    height = models.CharField(max_length=10, blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    education = models.CharField(max_length=100, blank=True)
    relationship_goals = models.CharField(max_length=100, blank=True)
    smoking_habits = models.CharField(max_length=50, blank=True)
    drinking_habits = models.CharField(max_length=50, blank=True)
    languages = models.CharField(max_length=200, blank=True)
    
    class Meta:
        db_table = 'user_profiles'
    
    def __str__(self):
        return f"{self.user.username}'s Profile"