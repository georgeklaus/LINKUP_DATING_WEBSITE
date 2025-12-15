from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.chat_list, name='chat_list'),
    path('room/<str:username>/', views.chat_room, name='chat_room'),
    path('video-call/<str:username>/', views.start_video_call, name='start_video_call'),
    path('video-call-room/<str:room_name>/', views.video_call_room, name='video_call_room'),
    path('end-video-call/<str:room_name>/', views.end_video_call, name='end_video_call'),
    # Dev preview for chat room template
    path('dev/preview/<str:username>/', views.chat_room_preview, name='chat_room_preview'),
]