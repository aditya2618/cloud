"""
Gateway provisioning and management views
"""
from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.hashers import make_password
from .models import Gateway, HomePermission
from .serializers import (
    GatewayProvisionSerializer,
    GatewaySerializer,
    GatewayProvisionResponseSerializer,
    HomePermissionSerializer
)


class GatewayProvisionView(APIView):
    """
    Gateway provisioning endpoint.
    
    POST /api/gateways/provision
    Body: { "home_id": "uuid", "name": "optional_name" }
    Response: { "gateway_id", "home_id", "secret", "message" }
    
    This is called once per home during edge gateway setup.
    The returned secret must be stored securely on the edge gateway.
    """
    permission_classes = (permissions.IsAuthenticated,)
    
    def post(self, request):
        serializer = GatewayProvisionSerializer(data=request.data)
        
        if serializer.is_valid():
            home_id = serializer.validated_data['home_id']
            name = serializer.validated_data.get('name', f'Home {home_id}')
            
            # Generate secure secret
            secret = Gateway.generate_secret()
            secret_hash = make_password(secret)
            
            # Create gateway
            gateway = Gateway.objects.create(
                home_id=home_id,
                owner=request.user,
                name=name,
                secret_hash=secret_hash,
                status='online'
            )
            
            # Create owner permission
            HomePermission.objects.create(
                user=request.user,
                home_id=home_id,
                role='owner',
                granted_by=request.user
            )
            
            response_data = {
                'gateway_id': gateway.id,
                'home_id': gateway.home_id,
                'secret': secret,  # Only returned once!
                'message': 'Gateway provisioned successfully. Store the secret securely - it will not be shown again.'
            }
            
            response_serializer = GatewayProvisionResponseSerializer(data=response_data)
            response_serializer.is_valid()
            
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GatewayListView(generics.ListAPIView):
    """
    List all gateways owned by the current user.
    
    GET /api/gateways/
    """
    serializer_class = GatewaySerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        return Gateway.objects.filter(owner=self.request.user, is_active=True)


class GatewayDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get, update, or delete a specific gateway.
    
    GET /api/gateways/{id}/
    PATCH /api/gateways/{id}/
    DELETE /api/gateways/{id}/  (soft delete - sets is_active=False)
    """
    serializer_class = GatewaySerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        return Gateway.objects.filter(owner=self.request.user)
    
    def perform_destroy(self, instance):
        # Soft delete
        instance.is_active = False
        instance.status = 'revoked'
        instance.save()


class GatewayRevokeView(APIView):
    """
    Revoke gateway access (security measure).
    
    POST /api/gateways/{id}/revoke
    """
    permission_classes = (permissions.IsAuthenticated,)
    
    def post(self, request, pk):
        try:
            gateway = Gateway.objects.get(pk=pk, owner=request.user)
            gateway.status = 'revoked'
            gateway.is_active = False
            gateway.save()
            
            return Response(
                {"message": "Gateway revoked successfully"},
                status=status.HTTP_200_OK
            )
        except Gateway.DoesNotExist:
            return Response(
                {"error": "Gateway not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class HomePermissionListView(generics.ListCreateAPIView):
    """
    List or create home permissions (share home access).
    
    GET /api/homes/{home_id}/permissions/
    POST /api/homes/{home_id}/permissions/
    Body: { "user": "user_id", "role": "owner|admin|user|viewer" }
    """
    serializer_class = HomePermissionSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        home_id = self.kwargs['home_id']
        # Only show permissions if user has access to this home
        if not HomePermission.objects.filter(
            user=self.request.user,
            home_id=home_id
        ).exists():
            return HomePermission.objects.none()
        
        return HomePermission.objects.filter(home_id=home_id)
    
    def perform_create(self, serializer):
        home_id = self.kwargs['home_id']
        
        # Check if current user can manage this home
        user_permission = HomePermission.objects.filter(
            user=self.request.user,
            home_id=home_id
        ).first()
        
        if not user_permission or not user_permission.can_manage():
            raise permissions.PermissionDenied("You don't have permission to manage this home")
        
        serializer.save(home_id=home_id, granted_by=self.request.user)
