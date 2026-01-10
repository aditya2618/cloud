"""
Login serializer with JWT response including home IDs
"""
from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    """Login with email OR username/password, returns JWT with home_ids"""
    email = serializers.CharField()  # Changed from EmailField to CharField to accept username too
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        identifier = data.get('email')  # Could be email or username
        password = data.get('password')
        
        if identifier and password:
            # Try to authenticate with identifier as username first
            user = authenticate(username=identifier, password=password)
            
            # If that fails, try to find user by email and authenticate
            if not user:
                try:
                    user_obj = User.objects.get(email=identifier)
                    user = authenticate(username=user_obj.email, password=password)
                except User.DoesNotExist:
                    pass
            
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            
            # Store user for later use
            data['user'] = user
            return data
        else:
            raise serializers.ValidationError('Must include email/username and password')


class JWTResponseSerializer(serializers.Serializer):
    """JWT response with custom claims"""
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = serializers.DictField()
    homes = serializers.ListField(child=serializers.CharField())

