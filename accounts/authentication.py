"""
Custom JWT Authentication for DRF views
"""
from rest_framework import authentication, exceptions
from django.contrib.auth import get_user_model
from .jwt_utils import validate_token
import jwt

User = get_user_model()


class JWTAuthentication(authentication.BaseAuthentication):
    """
    Custom JWT authentication for API views.
    
    Validates tokens created by our custom JWT utilities.
    """
    
    def authenticate(self, request):
        # Get authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            return None
        
        # Extract token
        token = auth_header.replace('Bearer ', '')
        
        try:
            # Validate and decode token
            payload = validate_token(token, expected_type='access')
            
            # Get user
            user_id = payload.get('user_id')
            if not user_id:
                raise exceptions.AuthenticationFailed('Invalid token payload')
            
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise exceptions.AuthenticationFailed('User not found')
            
            if not user.is_active:
                raise exceptions.AuthenticationFailed('User is inactive')
            
            # Return (user, None) - DRF expects a tuple
            return (user, None)
            
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError as e:
            raise exceptions.AuthenticationFailed(f'Invalid token: {str(e)}')
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Authentication failed: {str(e)}')
    
    def authenticate_header(self, request):
        """
        Return WWW-Authenticate header for failed auth.
        """
        return 'Bearer realm="api"'
