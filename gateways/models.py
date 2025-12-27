"""
Gateway and Home Permission Models
"""
import uuid
import secrets
from django.db import models
from django.utils.timezone import now
from django.conf import settings


class Gateway(models.Model):
    """
    Represents an edge gateway (local Django instance).
    One gateway per physical location/home.
    """
    STATUS_CHOICES = [
        ('provisioning', 'Provisioning'),
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('revoked', 'Revoked'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    home_id = models.UUIDField(unique=True, db_index=True)  # home_id from edge
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='gateways'
    )
    
    # Authentication
    secret_hash = models.CharField(max_length=256)  # Hashed secret
    public_key = models.TextField(blank=True, null=True)  # Optional for signing
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='provisioning')
    is_active = models.BooleanField(default=True)
    
    # Metadata
    name = models.CharField(max_length=255, blank=True)  # User-friendly name
    version = models.CharField(max_length=50, blank=True)  # Edge software version
    last_seen = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'gateways'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Gateway {self.id} ({self.status})"
    
    @staticmethod
    def generate_secret():
        """Generate a secure random secret for gateway authentication."""
        return secrets.token_urlsafe(32)
    
    def is_online(self):
        """Check if gateway is currently online (seen within last 5 minutes)."""
        if not self.last_seen:
            return False
        from datetime import timedelta
        return (now() - self.last_seen) < timedelta(minutes=5)


class HomePermission(models.Model):
    """
    Multi-tenant access control.
    Defines which users can access which homes through the cloud.
    """
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('user', 'User'),
        ('viewer', 'Viewer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='home_permissions'
    )
    home_id = models.UUIDField(db_index=True)  # home_id from edge
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    
    created_at = models.DateTimeField(default=now)
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='granted_permissions'
    )
    
    class Meta:
        db_table = 'home_permissions'
        unique_together = ('user', 'home_id')
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.user.email} → Home {self.home_id} ({self.role})"
    
    def can_control(self):
        """Check if this permission allows device control."""
        return self.role in ['owner', 'admin', 'user']
    
    def can_manage(self):
        """Check if this permission allows home management."""
        return self.role in ['owner', 'admin']
