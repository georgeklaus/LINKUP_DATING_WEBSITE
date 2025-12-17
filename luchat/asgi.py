import os

# Ensure settings are configured before importing Django/ app modules
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'luchat.settings')

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# Initialize Django ASGI application first (this loads app registry)
django_asgi_app = get_asgi_application()

# Now import routing which may import models/consumers safely
import chat.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chat.routing.websocket_urlpatterns
        )
    ),
})