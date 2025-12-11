from django.db import models
from django.conf import settings
from django.utils import timezone

class UserLike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='likes_given')
    liked_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='likes_received')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_likes'
        unique_together = ['user', 'liked_user']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['liked_user', 'created_at']),
        ]

class UserDislike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dislikes_given')
    disliked_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dislikes_received')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_dislikes'
        unique_together = ['user', 'disliked_user']

class Match(models.Model):
    user1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='matches_initiated')
    user2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='matches_received')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'matches'
        unique_together = ['user1', 'user2']
        indexes = [
            models.Index(fields=['user1', 'is_active']),
            models.Index(fields=['user2', 'is_active']),
        ]

class UserView(models.Model):
    viewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='views_given')
    viewed_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='views_received')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_views'
        indexes = [
            models.Index(fields=['viewer', 'created_at']),
            models.Index(fields=['viewed_user', 'created_at']),
        ]