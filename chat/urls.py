from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.chat_list, name='chat_list'),
    path('room/<str:username>/', views.chat_room, name='chat_room'),
    path('video-call/<str:username>/', views.start_video_call, name='start_video_call'),
]