"""
Pairing Code Serializers for Gateway Registration
"""
from rest_framework import serializers
from .pairing_codes import PairingCode
from .models import Gateway


class PairingCodeRequestSerializer(serializers.Serializer):
    """Request a new pairing code"""
    home_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    expiry_minutes = serializers.IntegerField(min_value=5, max_value=60, default=10)


class PairingCodeResponseSerializer(serializers.Serializer):
    """Pairing code response (8-digit code)"""
    code = serializers.CharField()
    expires_at = serializers.DateTimeField()
    message = serializers.CharField()


class CompletePairingSerializer(serializers.Serializer):
    """Gateway submits UUID + pairing code to complete registration"""
    pairing_code = serializers.CharField(max_length=8)
    gateway_uuid = serializers.UUIDField()
    home_id = serializers.UUIDField()
    name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    version = serializers.CharField(max_length=50, required=False, allow_blank=True)


class CompletePairingResponseSerializer(serializers.Serializer):
    """Response after successful pairing"""
    gateway_id = serializers.UUIDField()
    home_id = serializers.UUIDField()
    secret = serializers.CharField()
    message = serializers.CharField()
