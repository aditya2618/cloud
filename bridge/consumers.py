"""
WebSocket Bridge Consumer (Cloud Server Side)

This consumer handles incoming WebSocket connections from edge gateways.
It authenticates gateways and relays commands from mobile apps to edge gateways.
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.hashers import check_password
from gateways.models import Gateway, HomePermission
from bridge.models import BridgeSession

logger = logging.getLogger('bridge')


class BridgeConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for edge gateway connections.
    
    Connection URL: wss://cloud.example.com/bridge/
    Auth: JWT in query string or header
    """
    
    async def connect(self):
        """
        Handle new gateway connection.
        Authenticate, register session, join gateway group.
        """
        logger.info("=== Bridge connect() called ===")
        
        # Extract authentication from query string
        query_string = self.scope.get("query_string", b"").decode()
        gateway_id = None
        secret = None
        
        # Parse gateway_id and secret from query string
        for param in query_string.split("&"):
            if param.startswith("gateway_id="):
                gateway_id = param.split("=")[1]
            elif param.startswith("secret="):
                secret = param.split("=")[1]
        
        if not gateway_id or not secret:
            logger.error("✗ Bridge auth failed: Missing gateway_id or secret")
            await self.close()
            return
        
        # Authenticate gateway
        try:
            gateway = await self.get_gateway(gateway_id)
            if not gateway or not await self.verify_secret(gateway, secret):
                logger.error(f"✗ Bridge auth failed: Invalid credentials for {gateway_id}")
                await self.close()
                return
            
            # Store gateway info
            self.gateway = gateway
            self.gateway_id = str(gateway.id)
            self.home_id = str(gateway.home_id)
            self.group_name = f"gateway_{self.gateway_id}"
            
            # Join gateway-specific group
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            
            # Create bridge session
            client_ip = self.scope.get('client', ['unknown', 0])[0]
            await self.create_session(gateway, client_ip)
            
            # Update gateway status
            await self.update_gateway_status(gateway, 'online')
            
            await self.accept()
            logger.info(f"✓ Bridge connected: {self.gateway_id} (home: {self.home_id})")
            
        except Exception as e:
            logger.error(f"✗ Bridge connection error: {e}")
            await self.close()
    
    async def disconnect(self, close_code):
        """
        Handle gateway disconnection.
        Clean up session, update status.
        """
        if hasattr(self, 'gateway_id'):
            # Leave group
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            
            # Delete session
            await self.delete_session()
            
            # Update gateway status to offline
            await self.update_gateway_status(self.gateway, 'offline')
            
            logger.info(f"✗ Bridge disconnected: {self.gateway_id}")
    
    async def receive(self, text_data):
        """
        Receive message from edge gateway.
        This could be:
        - ACK for a command
        - State update
        - Sync data
        - Heartbeat/ping
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            logger.debug(f"📥 Received from gateway {self.gateway_id}: {message_type}")
            
            if message_type == 'ping':
                # Heartbeat - update last_ping
                await self.update_session_ping()
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
            
            elif message_type == 'ack':
                # Command acknowledgment
                # TODO: Forward to requesting client if needed
                logger.info(f"✅ Command ACK from gateway {self.gateway_id}: {data.get('request_id')}")
            
            elif message_type == 'state':
                # State update from edge
                # TODO: Cache state for remote clients
                logger.debug(f"📊 State update from gateway {self.gateway_id}")
            
            elif message_type == 'sync':
                # Sync response (metadata, devices, etc.)
                # TODO: Store in cloud database
                logger.info(f"🔄 Sync data from gateway {self.gateway_id}")
            
        except json.JSONDecodeError:
            logger.error(f"✗ Invalid JSON from gateway {self.gateway_id}")
        except Exception as e:
            logger.error(f"✗ Error processing message from gateway {self.gateway_id}: {e}")
    
    
    async def send_command(self, event):
        """
        Send command to edge gateway.
        Called from remote control API via channel_layer.send().
        
        event = {
            'type': 'send_command',
            'command_id': 'uuid',
            'payload': {...}
        }
        """
        logger.info(f"📡 Sending command to gateway {self.gateway_id}: {event.get('command_id')}")
        
        # Send command to edge client
        await self.send(text_data=json.dumps({
            'type': 'command',
            'request_id': event.get('command_id'),
            'payload': event.get('payload')
        }))
    
    async def relay_command(self, event):
        """
        Relay command from cloud API to edge gateway.
        Called via channel layer group_send.
        """
        logger.info(f"📡 Relaying command to gateway {self.gateway_id}")
        await self.send(text_data=json.dumps(event['data']))
    
    
    # Database helper methods
    
    @database_sync_to_async
    def get_gateway(self, gateway_id):
        """Get gateway from database."""
        try:
            return Gateway.objects.get(id=gateway_id, is_active=True)
        except Gateway.DoesNotExist:
            return None
    
    @database_sync_to_async
    def verify_secret(self, gateway, secret):
        """Verify gateway secret."""
        return check_password(secret, gateway.secret_hash)
    
    @database_sync_to_async
    def create_session(self, gateway, ip_address):
        """Create bridge session record."""
        BridgeSession.objects.create(
            gateway=gateway,
            channel_name=self.channel_name,
            ip_address=ip_address
        )
    
    @database_sync_to_async
    def delete_session(self):
        """Delete bridge session record."""
        BridgeSession.objects.filter(channel_name=self.channel_name).delete()
    
    @database_sync_to_async
    def update_session_ping(self):
        """Update session last_ping timestamp."""
        session = BridgeSession.objects.filter(channel_name=self.channel_name).first()
        if session:
            session.update_ping()
    
    @database_sync_to_async
    def update_gateway_status(self, gateway, status):
        """Update gateway online/offline status."""
        from django.utils.timezone import now
        gateway.status = status
        gateway.last_seen = now()
        gateway.save(update_fields=['status', 'last_seen'])
