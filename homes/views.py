from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from gateways.models import HomePermission
from .models import HomeMetadata, SyncedDevice
from .serializers import SyncedDeviceSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import uuid
import logging

logger = logging.getLogger(__name__)

class DeviceListView(generics.ListAPIView):
    serializer_class = SyncedDeviceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        home_id = self.kwargs['home_id']
        # Verify permission
        if not HomePermission.objects.filter(user=self.request.user, home_id=home_id).exists():
            return SyncedDevice.objects.none()
        return SyncedDevice.objects.filter(home__id=home_id)


class DeviceControlView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, home_id, pk):
        # 1. Check Permission
        if not HomePermission.objects.filter(user=request.user, home_id=home_id).exists():
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        # 2. Get Device
        device = get_object_or_404(SyncedDevice, home__id=home_id, edge_id=pk)

        # 3. Construct Payload
        command = request.data.get("command")
        value = request.data.get("value")
        
        request_id = str(uuid.uuid4())
        
        # Payload matching cloud_client.py handle_control_command
        payload = {
            "type": "control_entity",
            "entity_id": device.edge_id,
            "command": command,
            "value": value,
            "request_id": request_id
        }

        # 4. Send to Gateway Channel
        channel_layer = get_channel_layer()
        group_name = f"gateway_{home_id}"
        
        logger.info(f"Sending command to {group_name}: {payload}")
        
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "proxy_command", 
                "data": payload
            }
        )

        return Response({"status": "sent", "request_id": request_id})
