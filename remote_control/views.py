"""
Remote Control API Views

Provides REST endpoints for controlling smart home devices remotely.
Commands are relayed through the WebSocket bridge to the edge gateway.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
from datetime import timedelta
import uuid

from gateways.models import Gateway, HomePermission
from bridge.models import BridgeSession


@api_view(['POST'])
@permission_classes([AllowAny])  # TODO: Re-enable IsAuthenticated after testing
def control_entity(request, home_id, entity_id):
    """
    Control a device entity remotely.
    
    POST /api/remote/homes/{home_id}/entities/{entity_id}/control
    
    Request body:
    {
        "command": "turn_on" | "turn_off" | "set_value",
        "value": <any> (optional, for set_value)
    }
    
    Response:
    {
        "status": "success" | "error",
        "message": "...",
        "command_id": "uuid"
    }
    """
    # For testing: skip user permission check if anonymous
    # TODO: Re-enable user check after implementing cloud auth
    if request.user.is_authenticated:
        try:
            permission = HomePermission.objects.get(
                user=request.user,
                home_id=home_id
            )
            gateway = permission.gateway
        except HomePermission.DoesNotExist:
            return Response(
                {"error": "You don't have permission to access this home"},
                status=status.HTTP_403_FORBIDDEN
            )
    else:
        # Anonymous access for testing - look up gateway directly
        try:
            gateway = Gateway.objects.get(home_id=home_id)
        except Gateway.DoesNotExist:
            return Response(
                {"error": "Gateway not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    # Get command from request
    command_type = request.data.get('command')
    command_value = request.data.get('value')
    
    if not command_type:
        return Response(
            {"error": "command is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        bridge_session = BridgeSession.objects.get(gateway=gateway)
    except BridgeSession.DoesNotExist:
        return Response(
            {"error": "Gateway is offline. Cannot control devices remotely."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    # Check if session is still active (last ping within 2 minutes)
    if bridge_session.last_ping:
        time_since_ping = timezone.now() - bridge_session.last_ping
        if time_since_ping > timedelta(minutes=2):
            return Response(
                {"error": "Gateway connection is stale. Please wait for reconnection."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
    
    # Generate command ID for tracking
    command_id = str(uuid.uuid4())
    
    # Send command through WebSocket bridge
    channel_layer = get_channel_layer()
    
    # Prepare command payload
    command_payload = {
        "entity_id": entity_id,
        "command": command_type
    }
    if command_value is not None:
        command_payload["value"] = command_value
    
    try:
        # Send to the specific gateway's channel
        async_to_sync(channel_layer.send)(
            bridge_session.channel_name,
            {
                "type": "send_command",
                "command_id": command_id,
                "payload": command_payload
            }
        )
        
        return Response({
            "status": "success",
            "message": "Command sent to gateway",
            "command_id": command_id,
            "entity_id": entity_id,
            "command": command_type
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"error": f"Failed to send command: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])  # TODO: Re-enable IsAuthenticated after testing
def run_scene(request, home_id, scene_id):
    """
    Run a scene remotely.
    
    POST /api/remote/homes/{home_id}/scenes/{scene_id}/run
    
    Response:
    {
        "status": "success" | "error",
        "message": "...",
        "command_id": "uuid"
    }
    """
    # For testing: skip user permission check if anonymous
    # TODO: Re-enable user check after implementing cloud auth
    if request.user.is_authenticated:
        try:
            permission = HomePermission.objects.get(
                user=request.user,
                home_id=home_id
            )
            gateway = permission.gateway
        except HomePermission.DoesNotExist:
            return Response(
                {"error": "You don't have permission to access this home"},
                status=status.HTTP_403_FORBIDDEN
            )
    else:
        # Anonymous access for testing - look up gateway directly
        try:
            gateway = Gateway.objects.get(home_id=home_id)
        except Gateway.DoesNotExist:
            return Response(
                {"error": "Gateway not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    try:
        bridge_session = BridgeSession.objects.get(gateway=gateway)
    except BridgeSession.DoesNotExist:
        return Response(
            {"error": "Gateway is offline. Cannot run scenes remotely."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    # Check session freshness
    if bridge_session.last_ping:
        time_since_ping = timezone.now() - bridge_session.last_ping
        if time_since_ping > timedelta(minutes=2):
            return Response(
                {"error": "Gateway connection is stale. Please wait for reconnection."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
    
    # Generate command ID
    command_id = str(uuid.uuid4())
    
    # Send scene command
    channel_layer = get_channel_layer()
    
    try:
        async_to_sync(channel_layer.send)(
            bridge_session.channel_name,
            {
                "type": "send_command",
                "command_id": command_id,
                "payload": {
                    "scene_id": scene_id,
                    "command": "run_scene"
                }
            }
        )
        
        return Response({
            "status": "success",
            "message": "Scene command sent to gateway",
            "command_id": command_id,
            "scene_id": scene_id
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"error": f"Failed to send command: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])  # TODO: Re-enable IsAuthenticated after testing
def get_gateway_status(request, home_id):
    """
    Get the current status of the gateway connection.
    
    GET /api/remote/homes/{home_id}/status
    
    Response:
    {
        "gateway_id": "uuid",
        "status": "online" | "offline" | "stale",
        "last_ping": "ISO timestamp",
        "connected_at": "ISO timestamp"
    }
    """
    # For testing: skip user permission check if anonymous
    # TODO: Re-enable user check after implementing cloud auth
    if request.user.is_authenticated:
        try:
            permission = HomePermission.objects.get(
                user=request.user,
                home_id=home_id
            )
            gateway = permission.gateway
        except HomePermission.DoesNotExist:
            return Response(
                {"error": "You don't have permission to access this home"},
                status=status.HTTP_403_FORBIDDEN
            )
    else:
        # Anonymous access for testing - look up gateway directly
        try:
            gateway = Gateway.objects.get(home_id=home_id)
        except Gateway.DoesNotExist:
            return Response(
                {"error": "Gateway not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    # Find active session
    try:
        bridge_session = BridgeSession.objects.get(gateway=gateway)
        
        # Determine status
        if bridge_session.last_ping:
            time_since_ping = timezone.now() - bridge_session.last_ping
            if time_since_ping > timedelta(minutes=2):
                session_status = "stale"
            else:
                session_status = "online"
        else:
            session_status = "online"  # Just connected, no ping yet
        
        return Response({
            "gateway_id": str(gateway.home_id),
            "status": session_status,
            "last_ping": bridge_session.last_ping.isoformat() if bridge_session.last_ping else None,
            "connected_at": bridge_session.connected_at.isoformat()
        })
        
    except BridgeSession.DoesNotExist:
        return Response({
            "gateway_id": str(gateway.home_id),
            "status": "offline",
            "last_ping": None,
            "connected_at": None
        })

