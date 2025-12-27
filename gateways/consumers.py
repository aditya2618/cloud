"""
WebSocket Gateway Consumer
Handles WebSocket connections from local gateways
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.hashers import check_password
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


class GatewayConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for gateway connections.
    
    URL: ws://cloud/ws/gateway/?gateway_id=UUID&secret=SECRET
    """
    
    async def connect(self):
        """Handle gateway WebSocket connection"""
        # Get gateway credentials from query string
        query_params = dict(self.scope['query_string'].decode().split('&'))
        gateway_id = None
        secret = None
        
        for param in query_params:
            if '=' in param:
                key, value = param.split('=', 1)
                if key == 'gateway_id':
                    gateway_id = value
                elif key == 'secret':
                    secret = value
        
        if not gateway_id or not secret:
            logger.warning("❌ Gateway connection rejected: missing credentials")
            await self.close()
            return
        
        # Verify gateway credentials
        try:
            from gateways.models import Gateway
            gateway = await sync_to_async(Gateway.objects.get)(id=gateway_id)
            
            # Verify secret
            if not check_password(secret, gateway.secret_hash):
                logger.warning(f"❌ Gateway {gateway_id} rejected: invalid secret")
                await self.close()
                return
            
            # Store gateway info
            self.gateway_id = gateway_id
            self.home_id = str(gateway.home_id)
            self.group_name = f"gateway_{self.home_id}"
            
            # Add to channel group
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            
            # Update gateway status
            gateway.status = 'online'
            await sync_to_async(gateway.save)(update_fields=['status'])
            
            await self.accept()
            logger.info(f"✅ Gateway connected: {gateway_id} (home: {self.home_id})")
            
        except Exception as e:
            logger.error(f"❌ Gateway connection error: {e}")
            await self.close()
    
    async def disconnect(self, close_code):
        """Handle gateway disconnection"""
        if hasattr(self, 'gateway_id'):
            logger.info(f"❌ Gateway disconnected: {self.gateway_id}")
            
            # Update gateway status
            try:
                from gateways.models import Gateway
                gateway = await sync_to_async(Gateway.objects.get)(id=self.gateway_id)
                gateway.status = 'offline'
                await sync_to_async(gateway.save)(update_fields=['status'])
            except:
                pass
            
            # Remove from channel group
            if hasattr(self, 'group_name'):
                await self.channel_layer.group_discard(
                    self.group_name,
                    self.channel_name
                )
    
    async def receive(self, text_data):
        """Handle incoming message from gateway"""
        try:
            data = json.loads(text_data)
            msg_type = data.get('type')
            
            logger.info(f"☁️  Gateway message: {msg_type}")
            
            if msg_type == 'ping':
                # Respond to heartbeat
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
            
            elif msg_type == 'state_update':
                # Forward state update to clients
                await self.channel_layer.group_send(
                    f"home_{self.home_id}",
                    {
                        'type': 'entity_state_update',
                        'data': data
                    }
                )
            
        except json.JSONDecodeError:
            logger.error("☁️  Invalid JSON from gateway")
        except Exception as e:
            logger.error(f"☁️  Message handling error: {e}")
    
    async def proxy_command(self, event):
        """Forward command from client to gateway"""
        await self.send(text_data=json.dumps(event['data']))
