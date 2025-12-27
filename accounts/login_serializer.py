"""
Login serializer with JWT response including home IDs
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from .jwt_utils import generate_access_token, generate_refresh_token, get_user_homes


class LoginSerializer(serializers.Serializer):
    """Login with email/password, returns JWT with home_ids"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            
            # Store user for later use
            data['user'] = user
            return data
        else:
            raise serializers.ValidationError('Must include email and password')


class JWTResponseSerializer(serializers.Serializer):
    """JWT response with custom claims"""
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = serializers.DictField()
    homes = serializers.ListField(child=serializers.CharField())
