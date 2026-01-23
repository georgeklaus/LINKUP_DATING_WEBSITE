from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/chat/(?P<room_name>[\w_-]+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'^ws/signaling/(?P<room_name>[\w_-]+)/$', consumers.SignalingConsumer.as_asgi()),
    re_path(r'^ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
    re_path(r'^ws/posts/$', consumers.PostsConsumer.as_asgi()),
]