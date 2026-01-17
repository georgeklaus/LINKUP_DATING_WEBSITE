from django.urls import path
from . import views

app_name = 'matching'

urlpatterns = [
    path('discover/', views.discover, name='discover'),
    path('discover/filter/', views.discover_filter, name='discover_filter'),
    path('like/<str:username>/', views.like_user, name='like_user'),
    path('dislike/<str:username>/', views.dislike_user, name='dislike_user'),
    path('superlike/<str:username>/', views.superlike_user, name='superlike_user'),
    path('matches/', views.matches_list, name='matches_list'),
]