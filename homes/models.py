"""
Home models - mainly for metadata storage
"""
import uuid
from django.db import models
from django.utils.timezone import now


class HomeMetadata(models.Model):
    """
    Stores metadata about homes from edge gateways.
    This is a read replica of edge home data for remote access.
    """
    id = models.UUIDField(primary_key=True, editable=False)  # Same as edge home_id
    gateway = models.OneToOneField(
        'gateways.Gateway',
        on_delete=models.CASCADE,
        related_name='home_metadata'
    )
    
    # Synced data from edge
    name = models.CharField(max_length=255)
    timezone = models.CharField(max_length=50, default='UTC')
    location_lat = models.FloatField(null=True, blank=True)
    location_lon = models.FloatField(null=True, blank=True)
    
    # Statistics (synced from edge)
    device_count = models.IntegerField(default=0)
    scene_count = models.IntegerField(default=0)
    automation_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    last_synced = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'home_metadata'
        verbose_name = 'Home Metadata'
        verbose_name_plural = 'Home Metadata'
        
    
    def __str__(self):
        return f"{self.name} ({self.id})"


class SyncedDevice(models.Model):
    """
    Mirror of a device/entity from the edge gateway.
    Synced via WebSocket when gateway connects.
    """
    home = models.ForeignKey(
        HomeMetadata, 
        on_delete=models.CASCADE, 
        related_name='devices'
    )
    edge_id = models.IntegerField(help_text="ID on the local gateway")
    
    name = models.CharField(max_length=255)
    entity_type = models.CharField(max_length=50)
    device_name = models.CharField(max_length=255, blank=True)
    
    state = models.JSONField(default=dict, blank=True)
    is_online = models.BooleanField(default=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        # Each ID is unique per home
        unique_together = ('home', 'edge_id')
        
    def __str__(self):
        return f"{self.name} ({self.entity_type})"
