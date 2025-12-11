from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('users/', include('users.urls', namespace='users')),
    path('posts/', include('posts.urls', namespace='posts')),
    path('chat/', include('chat.urls', namespace='chat')),
    path('payments/', include('payments.urls', namespace='payments')),
    path('matching/', include('matching.urls', namespace='matching')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)