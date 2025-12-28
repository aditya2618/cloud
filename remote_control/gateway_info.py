"""
Gateway Info View
Provides gateway UUID lookup for mobile app cloud mode
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from gateways.models import HomePermission


@api_view(['GET'])
# @permission_classes([IsAuthenticated])  # TODO: Re-enable after testing
def get_user_gateways(request):
    """
    Get all gateways (homes) accessible by the current user.
    
    Returns list of homes with their gateway UUIDs for cloud access.
    
    GET /api/remote/gateways
    
    Response:
    [
        {
            "home_id": "uuid",  # Gateway UUID for cloud API
            "name": "My Home",  # Optional
            "role": "owner"
        }
    ]
    """
    # For testing: return all home permissions
    # TODO: Filter by request.user when authentication is re-enabled
    permissions = HomePermission.objects.all()
    
    gateways = []
    for perm in permissions:
        gateways.append({
            "home_id": str(perm.home_id),  # This is the gateway UUID
            "role": perm.role,
        })
    
    return Response(gateways)
