from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from gateways.models import HomePermission
from .models import HomeMetadata, SyncedDevice
from .serializers import SyncedDeviceSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import uuid
import logging

logger = logging.getLogger(__name__)

class DeviceListView(APIView):
    """
    GET /api/homes/{home_id}/devices/
    Returns devices with entities from cache, triggers sync if stale
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, home_id):
        from .models import CachedEntity
        from .sync_service import HomeDataSyncService
        
        # Check permission
        permission = HomePermission.objects.filter(user=request.user, home_id=home_id).first()
        if not permission:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        
        gateway = permission.gateway
        
        # Get home metadata
        try:
            home = HomeMetadata.objects.get(gateway=gateway)
        except HomeMetadata.DoesNotExist:
            # Trigger initial sync
            HomeDataSyncService.request_sync(gateway)
            return Response([])  # Return empty for now, will populate after sync
        
        # Check if sync needed (stale data > 30s)
        if HomeDataSyncService.should_sync(home):
            HomeDataSyncService.request_sync(gateway)
        
        # Get cached entities and group by device
        entities = CachedEntity.objects.filter(home=home)
        
        devices = {}
        for entity in entities:
            dev_name = entity.device_name or 'Unknown Device'
            dev_id = entity.device_id or abs(hash(dev_name)) % 10000000
            
            if dev_name not in devices:
                devices[dev_name] = {
                    "id": dev_id,
                    "name": dev_name,
                    "node_name": entity.device_node_name or dev_name,
                    "is_online": True,  # Gateway is connected if we're here
                    "entities": []
                }
            
            # Add entity
            devices[dev_name]["entities"].append({
                "id": entity.edge_id,
                "name": entity.name,
                "entity_type": entity.entity_type,
                "subtype": entity.subtype,
                "state": entity.state,
                "capabilities": entity.capabilities,
                "unit": entity.unit,
                "is_controllable": entity.is_controllable,
                "location": entity.location,
            })
        
        return Response(list(devices.values()))


class DeviceControlView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, home_id, pk):
        # 1. Check Permission
        if not HomePermission.objects.filter(user=request.user, home_id=home_id).exists():
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        # 2. Get Device
        device = get_object_or_404(SyncedDevice, home__id=home_id, edge_id=pk)

        # 3. Construct Payload
        command = request.data.get("command")
        value = request.data.get("value")
        
        request_id = str(uuid.uuid4())
        
        # Payload matching cloud_client.py handle_control_command
        payload = {
            "type": "control_entity",
            "entity_id": device.edge_id,
            "command": command,
            "value": value,
            "request_id": request_id
        }

        # 4. Send to Gateway Channel
        channel_layer = get_channel_layer()
        group_name = f"gateway_{home_id}"
        
        logger.info(f"Sending command to {group_name}: {payload}")
        
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "proxy_command", 
                "data": payload
            }
        )

        return Response({"status": "sent", "request_id": request_id})


class EntitiesListView(APIView):
    """
    GET /api/remote/homes/{home_id}/entities/
    Returns all entities from cache, triggers sync if stale
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, home_id):
        from .models import CachedEntity
        from .sync_service import HomeDataSyncService
        
        # Check permission
        permission = HomePermission.objects.filter(user=request.user, home_id=home_id).first()
        if not permission:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        
        gateway = permission.gateway
        
        # Get home metadata
        try:
            home = HomeMetadata.objects.get(gateway=gateway)
        except HomeMetadata.DoesNotExist:
            # Trigger initial sync
            HomeDataSyncService.request_sync(gateway)
            return Response({
                "entities": [],
                "syncing": True,
                "message": "Initial sync in progress, please retry in a few seconds"
            })
        
        # Check if sync needed
        if HomeDataSyncService.should_sync(home):
            HomeDataSyncService.request_sync(gateway)
        
        # Return cached entities
        entities = CachedEntity.objects.filter(home=home).values(
            'edge_id', 'name', 'entity_type', 'subtype', 'state', 
            'capabilities', 'unit', 'is_controllable', 'device_id',
            'device_name', 'device_node_name', 'location', 'updated_at'
        )
        
        # Transform edge_id to id for frontend compatibility
        entities_list = []
        for e in entities:
            e['id'] = e.pop('edge_id')
            entities_list.append(e)
        
        return Response({
            "entities": entities_list,
            "last_synced": home.last_synced.isoformat() if home.last_synced else None,
            "syncing": False
        })


class ScenesListView(APIView):
    """
    GET /api/remote/homes/{home_id}/scenes/
    Returns all scenes from cache
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, home_id):
        from .models import CachedScene
        from .sync_service import HomeDataSyncService
        
        permission = HomePermission.objects.filter(user=request.user, home_id=home_id).first()
        if not permission:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        
        gateway = permission.gateway
        
        try:
            home = HomeMetadata.objects.get(gateway=gateway)
        except HomeMetadata.DoesNotExist:
            HomeDataSyncService.request_sync(gateway)
            return Response({"scenes": [], "syncing": True})
        
        if HomeDataSyncService.should_sync(home):
            HomeDataSyncService.request_sync(gateway)
        
        scenes = CachedScene.objects.filter(home=home).values(
            'edge_id', 'name', 'actions', 'updated_at'
        )
        
        scenes_list = []
        for s in scenes:
            s['id'] = s.pop('edge_id')
            scenes_list.append(s)
        
        return Response({"scenes": scenes_list})


class AutomationsListView(APIView):
    """
    GET /api/remote/homes/{home_id}/automations/
    Returns all automations from cache
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, home_id):
        from .models import CachedAutomation
        from .sync_service import HomeDataSyncService
        
        permission = HomePermission.objects.filter(user=request.user, home_id=home_id).first()
        if not permission:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        
        gateway = permission.gateway
        
        try:
            home = HomeMetadata.objects.get(gateway=gateway)
        except HomeMetadata.DoesNotExist:
            HomeDataSyncService.request_sync(gateway)
            return Response({"automations": [], "syncing": True})
        
        if HomeDataSyncService.should_sync(home):
            HomeDataSyncService.request_sync(gateway)
        
        automations = CachedAutomation.objects.filter(home=home).values(
            'edge_id', 'name', 'enabled', 'trigger_logic', 
            'cooldown_seconds', 'triggers', 'actions', 'updated_at'
        )
        
        automations_list = []
        for a in automations:
            a['id'] = a.pop('edge_id')
            automations_list.append(a)
        
        return Response({"automations": automations_list})


class HomeDataView(APIView):
    """
    GET /api/remote/homes/{home_id}/data/
    Returns all home data (entities, scenes, automations) in one call
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, home_id):
        from .models import CachedEntity, CachedScene, CachedAutomation, CachedLocation
        from .sync_service import HomeDataSyncService
        
        permission = HomePermission.objects.filter(user=request.user, home_id=home_id).first()
        if not permission:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        
        gateway = permission.gateway
        
        try:
            home = HomeMetadata.objects.get(gateway=gateway)
        except HomeMetadata.DoesNotExist:
            HomeDataSyncService.request_sync(gateway)
            return Response({
                "home": None,
                "entities": [],
                "scenes": [],
                "automations": [],
                "locations": [],
                "syncing": True,
                "message": "Initial sync in progress"
            })
        
        if HomeDataSyncService.should_sync(home):
            HomeDataSyncService.request_sync(gateway)
        
        # Get all data
        entities = list(CachedEntity.objects.filter(home=home).values(
            'edge_id', 'name', 'entity_type', 'subtype', 'state', 
            'capabilities', 'unit', 'is_controllable', 'device_id',
            'device_name', 'device_node_name', 'location'
        ))
        
        scenes = list(CachedScene.objects.filter(home=home).values(
            'edge_id', 'name', 'actions'
        ))
        
        automations = list(CachedAutomation.objects.filter(home=home).values(
            'edge_id', 'name', 'enabled', 'trigger_logic', 
            'cooldown_seconds', 'triggers', 'actions'
        ))
        
        locations = list(CachedLocation.objects.filter(home=home).values(
            'edge_id', 'name', 'location_type'
        ))
        
        # Transform edge_id to id
        for e in entities:
            e['id'] = e.pop('edge_id')
        for s in scenes:
            s['id'] = s.pop('edge_id')
        for a in automations:
            a['id'] = a.pop('edge_id')
        for l in locations:
            l['id'] = l.pop('edge_id')
        
        return Response({
            "home": {
                "id": str(home.id),
                "name": home.name,
                "timezone": home.timezone
            },
            "entities": entities,
            "scenes": scenes,
            "automations": automations,
            "locations": locations,
            "last_synced": home.last_synced.isoformat() if home.last_synced else None,
            "syncing": False
        })
