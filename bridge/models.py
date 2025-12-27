"""
Bridge Session Model for tracking WebSocket connections
"""
import uuid
from django.db import models
from django.utils.timezone import now


class BridgeSession(models.Model):
    """
    Tracks active WebSocket bridge connections from edge gateways.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gateway = models.ForeignKey(
        'gateways.Gateway',
        on_delete=models.CASCADE,
        related_name='bridge_sessions'
    )
    
    # Connection metadata
    channel_name = models.CharField(max_length=255, unique=True)  # Channels channel name
    ip_address = models.GenericIPAddressField()
    connected_at = models.DateTimeField(default=now)
    last_ping = models.DateTimeField(default=now)
    
    # Stats
    messages_sent = models.IntegerField(default=0)
    messages_received = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'bridge_sessions'
        ordering = ['-connected_at']
        
    def __str__(self):
        return f"Session {self.id} for Gateway {self.gateway_id}"
    
    def update_ping(self):
        """Update the last ping timestamp."""
        self.last_ping = now()
        self.save(update_fields=['last_ping'])
