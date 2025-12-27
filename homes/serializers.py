from rest_framework import serializers
from .models import HomeMetadata, SyncedDevice

class SyncedDeviceSerializer(serializers.ModelSerializer):
    """Serializer for synced devices/entities"""
    id = serializers.IntegerField(source='edge_id', read_only=True)
    
    class Meta:
        model = SyncedDevice
        fields = ['id', 'name', 'entity_type', 'device_name', 'state', 'is_online']
