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
        user = self.scope.get('user')
        
        # 1. Try Token Authentication (if user is populated by TokenAuthMiddleware)
        if user and user.is_authenticated:
            try:
                # Find gateway for this user
                # We prioritize finding a gateway associated with the user's permissions
                # If home_id is in URL, we try to use it, but if it's numeric (local ID) or missing,
                # we just find the first available gateway for this user.
                
                from gateways.models import Gateway, HomePermission
                
                @sync_to_async
                def get_gateway_for_user(user_obj):
                    # Try to find a gateway this user has access to
                    permission = HomePermission.objects.filter(user=user_obj).first()
                    if permission:
                        return permission.gateway
                    # Fallback: check if user owns any home directly (if model supports it) or implies permission
                    return None

                gateway = await get_gateway_for_user(user)
                
                if gateway:
                    self.gateway_id = str(gateway.id)
                    # Use URL home_id if available, otherwise use gateway's home_id
                    url_home_id = self.scope['url_route']['kwargs'].get('home_id')
                    self.home_id = url_home_id if url_home_id else str(gateway.home_id)
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
                    logger.info(f"✅ Gateway connected via Token: {self.gateway_id} (home: {self.home_id})")
                    
                    # Request initial device sync
                    await self.send(text_data=json.dumps({
                        "type": "get_devices",
                        "request_id": "sync_on_connect"
                    }))
                    return
                else:
                    logger.warning(f"❌ User {user} has no associated gateway")
                    await self.close()
                    return
            except Exception as e:
                logger.error(f"❌ Token Auth Error: {e}")
                await self.close()
                return

        # 2. Key/Secret Authentication (Legacy/fallback)
        try:
            query_string = self.scope['query_string'].decode()
            if not query_string:
                await self.close()
                return
                
            query_params = dict(param.split('=', 1) for param in query_string.split('&') if '=' in param)
            gateway_id = query_params.get('gateway_id')
            secret = query_params.get('secret')
            
            if not gateway_id or not secret:
                logger.warning("❌ Gateway connection rejected: missing credentials")
                await self.close()
                return
            
            # Verify gateway credentials
            from gateways.models import Gateway
            try:
                gateway = await sync_to_async(Gateway.objects.get)(id=gateway_id)
            except Gateway.DoesNotExist:
                logger.warning(f"❌ Gateway {gateway_id} not found")
                await self.close()
                return
                
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
            
            # Request initial device sync
            await self.send(text_data=json.dumps({
                "type": "get_devices",
                "request_id": "sync_on_connect"
            }))
            
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
            
            # Reduce log noise for pings
            if msg_type != 'ping':
                logger.info(f"☁️  Gateway message: {msg_type}")
            
            if msg_type == 'ping':
                # Respond to heartbeat
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
            
            elif msg_type == 'state_update':
                # Update DB state and forward
                await self.update_entity_state(data)
                
                # Forward state update to clients
                await self.channel_layer.group_send(
                    f"home_{self.home_id}",
                    {
                        'type': 'entity_state_update',
                        'data': data
                    }
                )
                
            elif msg_type == 'devices_response':
                # Sync devices list to DB
                await self.sync_devices(data.get('devices', []))
            
            elif msg_type == 'ack':
                # Forward ack to clients if needed (omitted for now)
                pass
            
        except json.JSONDecodeError:
            logger.error("☁️  Invalid JSON from gateway")
        except Exception as e:
            logger.error(f"☁️  Message handling error: {e}")
    
    async def proxy_command(self, event):
        """Forward command from client to gateway"""
        await self.send(text_data=json.dumps(event['data']))

    async def sync_devices(self, devices):
        """Update synced devices in DB"""
        from homes.models import SyncedDevice, HomeMetadata
        from gateways.models import Gateway
        try:
            # Ensure HomeMetadata exists (create if missing)
            @sync_to_async
            def get_home_metadata():
                try:
                    return HomeMetadata.objects.get(id=self.home_id)
                except HomeMetadata.DoesNotExist:
                    logger.warning(f"⚠️ HomeMetadata missing for {self.home_id}, creating now...")
                    gateway = Gateway.objects.get(id=self.gateway_id)
                    return HomeMetadata.objects.create(
                        id=self.home_id,
                        gateway=gateway,
                        name=gateway.name or f"Home {self.home_id[:8]}"
                    )

            home = await get_home_metadata()
            
            @sync_to_async
            def save_all_devices(home_obj, device_list):
                valid_ids = []
                for d in device_list:
                    SyncedDevice.objects.update_or_create(
                        home=home_obj,
                        edge_id=d['id'],
                        defaults={
                            'name': d['name'],
                            'entity_type': d['entity_type'],
                            'device_name': d.get('device_name', ''),
                            'state': d.get('state', {}),
                            'is_online': True
                        }
                    )
                    valid_ids.append(d['id'])
                
                # Mark missing as offline
                SyncedDevice.objects.filter(home=home_obj).exclude(edge_id__in=valid_ids).update(is_online=False)

            await save_all_devices(home, devices)
            logger.info(f"✅ Synced {len(devices)} devices for home {self.home_id}")
            
        except Exception as e:
            logger.error(f"❌ Device sync error: {e}")

    async def update_entity_state(self, data):
        """Update single entity state in DB"""
        from homes.models import SyncedDevice
        try:
            entity_id = data.get('entity_id')
            state = data.get('state')
            
            if entity_id and state:
                @sync_to_async
                def update_db():
                    SyncedDevice.objects.filter(
                        home__id=self.home_id, 
                        edge_id=entity_id
                    ).update(state=state, is_online=True)
                
                await update_db()
        except Exception:
            pass
