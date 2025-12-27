"""
WebSocket Consumer for Cloud Server
Proxies requests between mobile apps and local gateways
"""
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token


class GatewayConsumer(AsyncWebsocketConsumer):
    """
    Handles WebSocket connections from local gateways
    """
    
    async def connect(self):
        self.home_id = self.scope['url_route']['kwargs']['home_id']
        self.gateway_group = f'gateway_{self.home_id}'
        
        # Authenticate gateway
        token = self.scope['query_string'].decode().split('token=')[1] if b'token=' in self.scope['query_string'] else None
        
        if not token:
            await self.close()
            return
        
        user = await self.get_user_from_token(token)
        if not user:
            await self.close()
            return
        
        self.scope['user'] = user
        
        # Join gateway group
        await self.channel_layer.group_add(
            self.gateway_group,
            self.channel_name
        )
        
        await self.accept()
        print(f"✅ Gateway connected for home: {self.home_id}")
    
    async def disconnect(self, close_code):
        # Leave gateway group
        await self.channel_layer.group_discard(
            self.gateway_group,
            self.channel_name
        )
        print(f"❌ Gateway disconnected for home: {self.home_id}")
    
    async def receive(self, text_data):
        """Receive messages from gateway"""
        data = json.loads(text_data)
        print(f"📨 Gateway message: {data.get('type')}")
        
        # Forward to clients waiting for this data
        await self.channel_layer.group_send(
            f'client_{self.home_id}',
            {
                'type': 'gateway_response',
                'data': data
            }
        )

    async def proxy_request(self, event):
        """Forward request from client to gateway"""
        await self.send(text_data=json.dumps(event['data']))
    
    @database_sync_to_async
    def get_user_from_token(self, token_key):
        try:
            token = Token.objects.get(key=token_key)
            return token.user
        except Token.DoesNotExist:
            return None


class ClientConsumer(AsyncWebsocketConsumer):
    """
    Handles WebSocket connections from mobile apps
    Proxies device requests to local gateway
    """
    
    async def connect(self):
        self.home_id = self.scope['url_route']['kwargs']['home_id']
        self.client_group = f'client_{self.home_id}'
        self.gateway_group = f'gateway_{self.home_id}'
        
        # Authenticate client
        token = self.scope['query_string'].decode().split('token=')[1] if b'token=' in self.scope['query_string'] else None
        
        if not token:
            await self.close()
            return
        
        user = await self.get_user_from_token(token)
        if not user:
            await self.close()
            return
        
        self.scope['user'] = user
        
        # Join client group
        await self.channel_layer.group_add(
            self.client_group,
            self.channel_name
        )
        
        await self.accept()
        print(f"✅ Client connected for home: {self.home_id}")
    
    async def disconnect(self, close_code):
        # Leave client group
        await self.channel_layer.group_discard(
            self.client_group,
            self.channel_name
        )
        print(f"❌ Client disconnected for home: {self.home_id}")
    
    async def receive(self, text_data):
        """Receive requests from mobile app"""
        data = json.loads(text_data)
        request_type = data.get('type')
        request_id = data.get('request_id')
        
        print(f"📱 Client request: {request_type} (ID: {request_id})")
        
        if request_type == 'get_devices':
            # Forward request to gateway
            await self.channel_layer.group_send(
                self.gateway_group,
                {
                    'type': 'proxy_request',
                    'data': {
                        'type': 'get_devices',
                        'request_id': request_id,
                        'home_id': self.home_id
                    }
                }
            )
        elif request_type == 'control_entity':
            # Proxy entity control
            await self.channel_layer.group_send(
                self.gateway_group,
                {
                    'type': 'proxy_request',
                    'data': {
                        'type': 'control_entity',
                        'request_id': request_id,
                        'entity_id': data.get('entity_id'),
                        'command': data.get('command'),
                        'value': data.get('value')
                    }
                }
            )
    
    async def gateway_response(self, event):
        """Forward gateway response to client"""
        data = event['data']
        await self.send(text_data=json.dumps(data))
    
    async def proxy_request(self, event):
        """Send request to gateway"""
        await self.send(text_data=json.dumps(event['data']))
    
    @database_sync_to_async
    def get_user_from_token(self, token_key):
        try:
            token = Token.objects.get(key=token_key)
            return token.user
        except Token.DoesNotExist:
            return None
