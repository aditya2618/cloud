"""
JWT Utilities for Production Cloud Architecture

Implements JWT with custom claims including accessible home_ids.
This follows industry standards (OAuth 2.0, Auth0, Firebase).
"""
import jwt
from datetime import timedelta
from django.conf import settings
from django.utils.timezone import now as django_now
from gateways.models import HomePermission


def get_user_homes(user):
    """
    Get list of home IDs that the user has access to.
    
    Args:
        user: CloudUser instance
    
    Returns:
        List of home_id UUIDs (as strings)
    """
    permissions = HomePermission.objects.filter(user=user)
    home_ids = [str(perm.home_id) for perm in permissions]
    return home_ids


def generate_access_token(user, expiry_minutes=15):
    """
    Generate JWT access token with custom claims.
    
    Claims include:
    - user_id: User's ID
    - email: User's email
    - homes: List of accessible home_ids
    - exp: Expiration timestamp
    - iat: Issued at timestamp
    
    Args:
        user: CloudUser instance
        expiry_minutes: Token validity duration (default 15 minutes)
    
    Returns:
        JWT token string
    """
    now = django_now()
    expiration = now + timedelta(minutes=expiry_minutes)
    
    payload = {
        'user_id': user.id,
        'email': user.email,
        'homes': get_user_homes(user),  # ⭐ KEY FEATURE: Home access list
        'iat': int(now.timestamp()),
        'exp': int(expiration.timestamp()),
        'token_type': 'access'
    }
    
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    return token


def generate_refresh_token(user, expiry_days=30):
    """
    Generate JWT refresh token.
    
    Refresh tokens are longer-lived and used to get new access tokens.
    
    Args:
        user: CloudUser instance
        expiry_days: Token validity duration (default 30 days)
    
    Returns:
        JWT token string
    """
    now = django_now()
    expiration = now + timedelta(days=expiry_days)
    
    payload = {
        'user_id': user.id,
        'email': user.email,
        'iat': int(now.timestamp()),
        'exp': int(expiration.timestamp()),
        'token_type': 'refresh'
    }
    
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    return token


def validate_token(token, expected_type='access'):
    """
    Validate and decode a JWT token.
    
    Args:
        token: JWT token string
        expected_type: Expected token type ('access' or 'refresh')
    
    Returns:
        Decoded payload dict if valid, None if invalid
    
    Raises:
        jwt.ExpiredSignatureError: If token is expired
        jwt.InvalidTokenError: If token is malformed
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        
        # Verify token type if expected
        if expected_type and payload.get('token_type') != expected_type:
            raise jwt.InvalidTokenError(f'Expected {expected_type} token')
        
        return payload
    except jwt.ExpiredSignatureError:
        raise
    except jwt.InvalidTokenError:
        raise


def refresh_access_token(refresh_token):
    """
    Generate a new access token using a valid refresh token.
    
    Args:
        refresh_token: Valid refresh token string
    
    Returns:
        New access token string
    
    Raises:
        jwt.ExpiredSignatureError: If refresh token is expired
        jwt.InvalidTokenError: If refresh token is malformed
    """
    from accounts.models import CloudUser
    
    # Validate refresh token
    payload = validate_token(refresh_token, expected_type='refresh')
    
    # Get user
    user = CloudUser.objects.get(id=payload['user_id'])
    
    # Generate new access token
    return generate_access_token(user)


def decode_token_safe(token):
    """
    Safely decode a token without raising exceptions.
    
    Args:
        token: JWT token string
    
    Returns:
        Tuple(payload dict or None, error string or None)
    """
    try:
        payload = validate_token(token)
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, 'Token expired'
    except jwt.InvalidTokenError as e:
        return None, str(e)
    except Exception as e:
        return None, f'Token validation error: {str(e)}'
