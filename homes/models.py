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


class CachedEntity(models.Model):
    """
    Detailed entity cache including all control info.
    """
    home = models.ForeignKey(
        HomeMetadata, 
        on_delete=models.CASCADE, 
        related_name='entities'
    )
    edge_id = models.IntegerField(help_text="Entity ID on local server")
    
    name = models.CharField(max_length=255)
    entity_type = models.CharField(max_length=50)
    subtype = models.CharField(max_length=50, blank=True)
    
    state = models.JSONField(default=dict, blank=True)
    capabilities = models.JSONField(default=dict, blank=True)
    unit = models.CharField(max_length=20, blank=True)
    is_controllable = models.BooleanField(default=False)
    
    device_id = models.IntegerField(null=True, blank=True)
    device_name = models.CharField(max_length=255, blank=True)
    device_node_name = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    
    state_topic = models.CharField(max_length=500, blank=True)
    command_topic = models.CharField(max_length=500, blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('home', 'edge_id')
        verbose_name = 'Cached Entity'
        verbose_name_plural = 'Cached Entities'
        
    def __str__(self):
        return f"{self.name} ({self.entity_type})"


class CachedScene(models.Model):
    """
    Mirror of a scene from the edge gateway.
    """
    home = models.ForeignKey(
        HomeMetadata, 
        on_delete=models.CASCADE, 
        related_name='scenes'
    )
    edge_id = models.IntegerField(help_text="Scene ID on local server")
    
    name = models.CharField(max_length=255)
    actions = models.JSONField(default=list, help_text="List of scene actions")
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('home', 'edge_id')
        verbose_name = 'Cached Scene'
        verbose_name_plural = 'Cached Scenes'
        
    def __str__(self):
        return self.name


class CachedAutomation(models.Model):
    """
    Mirror of an automation from the edge gateway.
    """
    home = models.ForeignKey(
        HomeMetadata, 
        on_delete=models.CASCADE, 
        related_name='automations'
    )
    edge_id = models.IntegerField(help_text="Automation ID on local server")
    
    name = models.CharField(max_length=255)
    enabled = models.BooleanField(default=True)
    trigger_logic = models.CharField(max_length=3, default='AND')
    cooldown_seconds = models.IntegerField(default=60)
    
    triggers = models.JSONField(default=list)
    actions = models.JSONField(default=list)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('home', 'edge_id')
        verbose_name = 'Cached Automation'
        verbose_name_plural = 'Cached Automations'
        
    def __str__(self):
        return self.name


class CachedLocation(models.Model):
    """
    Mirror of a location/room from the edge gateway.
    """
    home = models.ForeignKey(
        HomeMetadata, 
        on_delete=models.CASCADE, 
        related_name='locations'
    )
    edge_id = models.IntegerField(help_text="Location ID on local server")
    
    name = models.CharField(max_length=255)
    location_type = models.CharField(max_length=50, blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('home', 'edge_id')
        verbose_name = 'Cached Location'
        verbose_name_plural = 'Cached Locations'
        
    def __str__(self):
        return self.name
