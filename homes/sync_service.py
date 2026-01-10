"""
Home Data Sync Service

Handles syncing data from local gateway to cloud cache via WebSocket bridge.
"""
import logging
from django.utils import timezone
from datetime import timedelta
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import uuid

from .models import HomeMetadata, CachedEntity, CachedScene, CachedAutomation, CachedLocation
from gateways.models import Gateway
from bridge.models import BridgeSession

logger = logging.getLogger('homes')

# Sync interval in seconds
SYNC_INTERVAL = 30


class HomeDataSyncService:
    """Service for syncing home data from local gateway to cloud cache"""
    
    @staticmethod
    def request_sync(gateway):
        """
        Request a full data sync from the local gateway.
        Returns a request_id that can be used to track the response.
        """
        request_id = str(uuid.uuid4())
        
        channel_layer = get_channel_layer()
        group_name = f"gateway_{gateway.id}"
        
        try:
            # Send sync request to gateway via WebSocket bridge
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "relay.command",
                    "data": {
                        "type": "get_home_data",
                        "request_id": request_id,
                    }
                }
            )
            logger.info(f"☁️  Requested home data sync from gateway {gateway.id}")
            return request_id
            
        except Exception as e:
            logger.error(f"☁️  Failed to request sync: {e}")
            return None
    
    @staticmethod
    def should_sync(home_metadata):
        """Check if we need to sync (last sync > SYNC_INTERVAL ago)"""
        if not home_metadata or not home_metadata.last_synced:
            return True
        
        time_since_sync = timezone.now() - home_metadata.last_synced
        return time_since_sync > timedelta(seconds=SYNC_INTERVAL)
    
    @staticmethod
    def process_sync_response(gateway, data):
        """
        Process sync response from local gateway.
        Updates all cached data.
        """
        try:
            # Get or create home metadata
            home_data = data.get('home', {})
            home_metadata, created = HomeMetadata.objects.get_or_create(
                gateway=gateway,
                defaults={
                    'id': gateway.home_id,
                    'name': home_data.get('name', 'Unknown Home'),
                    'timezone': home_data.get('timezone', 'UTC')
                }
            )
            
            if not created:
                home_metadata.name = home_data.get('name', home_metadata.name)
                home_metadata.timezone = home_data.get('timezone', home_metadata.timezone)
            
            # Sync entities
            entities_data = data.get('entities', [])
            HomeDataSyncService._sync_entities(home_metadata, entities_data)
            
            # Sync scenes
            scenes_data = data.get('scenes', [])
            HomeDataSyncService._sync_scenes(home_metadata, scenes_data)
            
            # Sync automations
            automations_data = data.get('automations', [])
            HomeDataSyncService._sync_automations(home_metadata, automations_data)
            
            # Sync locations
            locations_data = data.get('locations', [])
            HomeDataSyncService._sync_locations(home_metadata, locations_data)
            
            # Update sync timestamp and counts
            home_metadata.last_synced = timezone.now()
            home_metadata.device_count = len(entities_data)
            home_metadata.scene_count = len(scenes_data)
            home_metadata.automation_count = len(automations_data)
            home_metadata.save()
            
            logger.info(f"☁️  Synced home data: {len(entities_data)} entities, {len(scenes_data)} scenes, {len(automations_data)} automations")
            
            return True
            
        except Exception as e:
            logger.error(f"☁️  Failed to process sync response: {e}", exc_info=True)
            return False
    
    @staticmethod
    def _sync_entities(home_metadata, entities_data):
        """Sync entities to cache"""
        # Get existing cached entities
        existing_ids = set(CachedEntity.objects.filter(home=home_metadata).values_list('edge_id', flat=True))
        new_ids = set()
        
        for entity_data in entities_data:
            edge_id = entity_data['id']
            new_ids.add(edge_id)
            
            CachedEntity.objects.update_or_create(
                home=home_metadata,
                edge_id=edge_id,
                defaults={
                    'name': entity_data.get('name', ''),
                    'entity_type': entity_data.get('entity_type', ''),
                    'subtype': entity_data.get('subtype', ''),
                    'state': entity_data.get('state', {}),
                    'capabilities': entity_data.get('capabilities', {}),
                    'unit': entity_data.get('unit', ''),
                    'is_controllable': entity_data.get('is_controllable', False),
                    'device_id': entity_data.get('device_id'),
                    'device_name': entity_data.get('device_name', ''),
                    'device_node_name': entity_data.get('device_node_name', ''),
                    'location': entity_data.get('location', ''),
                    'state_topic': entity_data.get('state_topic', ''),
                    'command_topic': entity_data.get('command_topic', ''),
                }
            )
        
        # Remove entities that no longer exist
        removed_ids = existing_ids - new_ids
        if removed_ids:
            CachedEntity.objects.filter(home=home_metadata, edge_id__in=removed_ids).delete()
    
    @staticmethod
    def _sync_scenes(home_metadata, scenes_data):
        """Sync scenes to cache"""
        existing_ids = set(CachedScene.objects.filter(home=home_metadata).values_list('edge_id', flat=True))
        new_ids = set()
        
        for scene_data in scenes_data:
            edge_id = scene_data['id']
            new_ids.add(edge_id)
            
            CachedScene.objects.update_or_create(
                home=home_metadata,
                edge_id=edge_id,
                defaults={
                    'name': scene_data.get('name', ''),
                    'actions': scene_data.get('actions', []),
                }
            )
        
        removed_ids = existing_ids - new_ids
        if removed_ids:
            CachedScene.objects.filter(home=home_metadata, edge_id__in=removed_ids).delete()
    
    @staticmethod
    def _sync_automations(home_metadata, automations_data):
        """Sync automations to cache"""
        existing_ids = set(CachedAutomation.objects.filter(home=home_metadata).values_list('edge_id', flat=True))
        new_ids = set()
        
        for automation_data in automations_data:
            edge_id = automation_data['id']
            new_ids.add(edge_id)
            
            CachedAutomation.objects.update_or_create(
                home=home_metadata,
                edge_id=edge_id,
                defaults={
                    'name': automation_data.get('name', ''),
                    'enabled': automation_data.get('enabled', True),
                    'trigger_logic': automation_data.get('trigger_logic', 'AND'),
                    'cooldown_seconds': automation_data.get('cooldown_seconds', 60),
                    'triggers': automation_data.get('triggers', []),
                    'actions': automation_data.get('actions', []),
                }
            )
        
        removed_ids = existing_ids - new_ids
        if removed_ids:
            CachedAutomation.objects.filter(home=home_metadata, edge_id__in=removed_ids).delete()
    
    @staticmethod
    def _sync_locations(home_metadata, locations_data):
        """Sync locations to cache"""
        existing_ids = set(CachedLocation.objects.filter(home=home_metadata).values_list('edge_id', flat=True))
        new_ids = set()
        
        for loc_data in locations_data:
            edge_id = loc_data['id']
            new_ids.add(edge_id)
            
            CachedLocation.objects.update_or_create(
                home=home_metadata,
                edge_id=edge_id,
                defaults={
                    'name': loc_data.get('name', ''),
                    'location_type': loc_data.get('location_type', ''),
                }
            )
        
        removed_ids = existing_ids - new_ids
        if removed_ids:
            CachedLocation.objects.filter(home=home_metadata, edge_id__in=removed_ids).delete()
    
    @staticmethod
    def get_cached_entities(gateway):
        """Get cached entities for a gateway"""
        try:
            home = HomeMetadata.objects.get(gateway=gateway)
            return list(CachedEntity.objects.filter(home=home).values())
        except HomeMetadata.DoesNotExist:
            return []
    
    @staticmethod
    def get_cached_scenes(gateway):
        """Get cached scenes for a gateway"""
        try:
            home = HomeMetadata.objects.get(gateway=gateway)
            return list(CachedScene.objects.filter(home=home).values())
        except HomeMetadata.DoesNotExist:
            return []
    
    @staticmethod
    def get_cached_automations(gateway):
        """Get cached automations for a gateway"""
        try:
            home = HomeMetadata.objects.get(gateway=gateway)
            return list(CachedAutomation.objects.filter(home=home).values())
        except HomeMetadata.DoesNotExist:
            return []
    
    @staticmethod
    def update_entity_state(gateway, entity_id, state):
        """Update a single entity's state in the cache"""
        try:
            home = HomeMetadata.objects.get(gateway=gateway)
            entity = CachedEntity.objects.get(home=home, edge_id=entity_id)
            entity.state = state
            entity.save(update_fields=['state', 'updated_at'])
            return True
        except (HomeMetadata.DoesNotExist, CachedEntity.DoesNotExist):
            return False
