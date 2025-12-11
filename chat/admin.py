from django.contrib import admin
from .models import ChatRoom, Message, ChatCharge, VideoCall

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    filter_horizontal = ('participants',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'room', 'content_preview', 'timestamp', 'is_read')
    list_filter = ('timestamp', 'is_read')
    
    def content_preview(self, obj):
        return obj.content[:30] + '...' if len(obj.content) > 30 else obj.content
    content_preview.short_description = 'Content'

@admin.register(ChatCharge)
class ChatChargeAdmin(admin.ModelAdmin):
    list_display = ('user', 'chat_room', 'amount', 'charged_at')
    list_filter = ('charged_at',)

@admin.register(VideoCall)
class VideoCallAdmin(admin.ModelAdmin):
    list_display = ('caller', 'receiver', 'room_name', 'started_at', 'duration', 'cost', 'is_active')
    list_filter = ('is_active', 'started_at')