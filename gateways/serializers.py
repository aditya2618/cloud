"""
Gateway serializers for provisioning and management
"""
from rest_framework import serializers
from .models import Gateway, HomePermission


class GatewayProvisionSerializer(serializers.Serializer):
    """Serializer for gateway provisioning request."""
    home_id = serializers.UUIDField(required=True)
    name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    
    def validate_home_id(self, value):
        """Ensure home_id is unique."""
        if Gateway.objects.filter(home_id=value).exists():
            raise serializers.ValidationError("A gateway is already registered for this home.")
        return value


class GatewaySerializer(serializers.ModelSerializer):
    """Serializer for gateway details."""
    is_online = serializers.SerializerMethodField()
    
    class Meta:
        model = Gateway
        fields = (
            'id', 'home_id', 'name', 'status', 'is_active', 
            'is_online', 'version', 'last_seen', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'last_seen')
        
    def get_is_online(self, obj):
        """Check if gateway is currently online."""
        return obj.is_online()


class GatewayProvisionResponseSerializer(serializers.Serializer):
    """Serializer for gateway provisioning response."""
    gateway_id = serializers.UUIDField()
    home_id = serializers.UUIDField()
    secret = serializers.CharField()
    message = serializers.CharField()


class HomePermissionSerializer(serializers.ModelSerializer):
    """Serializer for home permissions."""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = HomePermission
        fields = ('id', 'user', 'user_email', 'home_id', 'role', 'created_at', 'granted_by')
        read_only_fields = ('id', 'created_at', 'granted_by')
