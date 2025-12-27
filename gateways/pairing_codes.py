"""
Pairing Code System for Secure Gateway Registration

Industry-standard pairing flow:
1. User requests pairing code in mobile app
2. Cloud generates 8-digit code (10-minute expiry)
3. User enters code on local gateway web UI
4. Gateway submits UUID + pairing code to cloud
5. Cloud validates and creates gateway registration
"""
import secrets
import string
from datetime import timedelta
from django.db import models
from django.utils.timezone import now
from django.conf import settings


class PairingCode(models.Model):
    """
    Temporary pairing codes for gateway registration.
    Similar to how smart home devices pair with apps.
    """
    code = models.CharField(max_length=8, unique=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pairing_codes'
    )
    home_name = models.CharField(max_length=255, blank=True, help_text="Optional name for the home")
    
    # Status tracking
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    gateway = models.ForeignKey(
        'Gateway',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pairing_code_used'
    )
    
    # Timestamps
    created_at = models.DateTimeField(default=now)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'pairing_codes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code', 'is_used']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Code {self.code} ({'used' if self.is_used else 'active'})"
    
    def is_valid(self):
        """Check if code is still valid (not used, not expired)."""
        if self.is_used:
            return False
        if now() > self.expires_at:
            return False
        return True
    
    def mark_used(self, gateway):
        """Mark this code as used by a gateway."""
        self.is_used = True
        self.used_at = now()
        self.gateway = gateway
        self.save(update_fields=['is_used', 'used_at', 'gateway'])
    
    @staticmethod
    def generate_code(length=8):
        """
        Generate a secure random pairing code.
        
        Format: 8 digits (e.g., 12345678)
        Similar to PIN codes on smart devices.
        """
        # Use digits only for easier manual entry
        digits = string.digits
        code = ''.join(secrets.choice(digits) for _ in range(length))
        return code
    
    @staticmethod
    def create_for_user(user, home_name='', expiry_minutes=10):
        """
        Create a new pairing code for a user.
        
        Args:
            user: The user requesting the pairing code
            home_name: Optional name for the home being paired
            expiry_minutes: How long the code is valid (default 10 min)
        
        Returns:
            PairingCode instance
        """
        # Generate unique code
        while True:
            code = PairingCode.generate_code()
            if not PairingCode.objects.filter(code=code).exists():
                break
        
        # Create pairing code
        pairing_code = PairingCode.objects.create(
            code=code,
            user=user,
            home_name=home_name,
            expires_at=now() + timedelta(minutes=expiry_minutes)
        )
        
        return pairing_code
    
    @staticmethod
    def cleanup_expired():
        """
        Delete expired pairing codes.
        Should be run periodically (e.g., celery task).
        """
        expired_count = PairingCode.objects.filter(
            expires_at__lt=now(),
            is_used=False
        ).delete()[0]
        return expired_count
