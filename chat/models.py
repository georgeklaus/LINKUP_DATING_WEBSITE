from django.db import models
from django.conf import settings
from django.utils import timezone

class ChatRoom(models.Model):
    name = models.CharField(max_length=255, unique=True)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='chat_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'chat_rooms'
        indexes = [
            models.Index(fields=['name']),
        ]

class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'messages'
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['room', 'timestamp']),
            models.Index(fields=['sender', 'timestamp']),
        ]

class ChatCharge(models.Model):
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.IntegerField(default=0)
    charged_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'chat_charges'
        indexes = [
            models.Index(fields=['user', 'charged_at']),
        ]

class VideoCall(models.Model):
    caller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='outgoing_calls')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='incoming_calls')
    room_name = models.CharField(max_length=255, unique=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration = models.IntegerField(default=0)  # in seconds
    cost = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'video_calls'
        indexes = [
            models.Index(fields=['caller', 'started_at']),
            models.Index(fields=['receiver', 'started_at']),
        ]