"""
ASGI routing configuration for WebSocket connections
"""
from django.urls import re_path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from smarthome_cloud.consumers import ClientConsumer
from gateways.consumers import GatewayConsumer

websocket_urlpatterns = [
    # Client WebSocket (mobile/web apps)
    re_path(r'ws/home/(?P<home_id>\d+)/$', ClientConsumer.as_asgi()),
    
    # Gateway WebSocket (local gateways)
    re_path(r'ws/gateway/(?:(?P<home_id>[a-zA-Z0-9-]+)/)?$', GatewayConsumer.as_asgi()),
]

from smarthome_cloud.middleware import TokenAuthMiddleware

application = ProtocolTypeRouter({
    'websocket': TokenAuthMiddleware(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
