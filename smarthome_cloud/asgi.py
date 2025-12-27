"""
ASGI config for smarthome_cloud project.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smarthome_cloud.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

# Import consumers after Django is initialized
from bridge.consumers import BridgeConsumer
from smarthome_cloud.consumers import GatewayConsumer, ClientConsumer

websocket_urlpatterns = [
    path('bridge/', BridgeConsumer.as_asgi()),
    path('ws/gateway/<str:home_id>/', GatewayConsumer.as_asgi()),
    path('ws/client/<str:home_id>/', ClientConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
