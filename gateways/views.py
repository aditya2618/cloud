"""
Gateway provisioning and management views
"""
from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.hashers import make_password, check_password
from .models import Gateway, HomePermission
from .pairing_codes import PairingCode
from .serializers import (
    GatewayProvisionSerializer,
    GatewaySerializer,
    GatewayProvisionResponseSerializer,
    HomePermissionSerializer
)
from .pairing_serializers import (
    PairingCodeRequestSerializer,
    PairingCodeResponseSerializer,
    CompletePairingSerializer,
    CompletePairingResponseSerializer
)


class PairingCodeRequestView(APIView):
    """
    Request a new pairing code for gateway registration.
    
    POST /api/gateways/request-pairing
    Body: { "home_name": "optional", "expiry_minutes": 10 }
    Response: { "code": "12345678", "expires_at": "...", "message": "..." }
    
    This is called from the mobile app when user wants to add a new gateway.
    """
    permission_classes = (permissions.IsAuthenticated,)
    
    def post(self, request):
        serializer = PairingCodeRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            home_name = serializer.validated_data.get('home_name', '')
            expiry_minutes = serializer.validated_data.get('expiry_minutes', 10)
            
            # Create pairing code
            pairing_code = PairingCode.create_for_user(
                user=request.user,
                home_name=home_name,
                expiry_minutes=expiry_minutes
            )
            
            response_data = {
                'code': pairing_code.code,
                'expires_at': pairing_code.expires_at,
                'message': f'Pairing code generated. Enter this code on your gateway within {expiry_minutes} minutes.'
            }
            
            response_serializer = PairingCodeResponseSerializer(data=response_data)
            response_serializer.is_valid()
            
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyPairingCodeView(APIView):
    """
    Verify if a pairing code is valid (for UI feedback).
    
    GET /api/gateways/verify-pairing/{code}
    Response: { "valid": true/false, "message": "..." }
    """
    permission_classes = (permissions.AllowAny,)  # No auth needed for verification
    
    def get(self, request, code):
        try:
            pairing_code = PairingCode.objects.get(code=code)
            
            if pairing_code.is_valid():
                return Response({
                    'valid': True,
                    'message': 'Pairing code is valid'
                })
            else:
                reason = 'already used' if pairing_code.is_used else 'expired'
                return Response({
                    'valid': False,
                    'message': f'Pairing code is {reason}'
                })
        except PairingCode.DoesNotExist:
            return Response({
                'valid': False,
                'message': 'Invalid pairing code'
            })


class CompletePairingView(APIView):
    """
    Complete gateway pairing (called by local gateway).
    
    POST /api/gateways/complete-pairing
    Body: {
        "pairing_code": "12345678",
        "gateway_uuid": "uuid-from-gateway",
        "home_id": "uuid-from-edge",
        "name": "My Home",
        "version": "1.0.0"
    }
    Response: {
        "gateway_id": "uuid",
        "home_id": "uuid", 
        "secret": "token",
        "message": "..."
    }
    """
    permission_classes = (permissions.AllowAny,)  # Gateway doesn't have auth yet
    
    def post(self, request):
        serializer = CompletePairingSerializer(data=request.data)
        
        if serializer.is_valid():
            code = serializer.validated_data['pairing_code']
            gateway_uuid = serializer.validated_data['gateway_uuid']
            gateway_name = serializer.validated_data.get('name', 'Smart Home Gateway')
            version = serializer.validated_data.get('version', '')
            
            # Validate pairing code
            try:
                pairing_code = PairingCode.objects.get(code=code)
                
                if not pairing_code.is_valid():
                    reason = 'already used' if pairing_code.is_used else 'expired'
                    return Response(
                        {'error': f'Pairing code is {reason}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Generate new home_id for this gateway
                import uuid
                home_id = uuid.uuid4()
                home_name = pairing_code.home_name or 'My Smart Home'
                
                # Generate secure secret for gateway authentication
                secret = Gateway.generate_secret()
                secret_hash = make_password(secret)
                
                # Create gateway registration
                gateway = Gateway.objects.create(
                    id=gateway_uuid,  # Use gateway's self-generated UUID
                    home_id=home_id,
                    owner=pairing_code.user,
                    name=gateway_name,
                    version=version,
                    secret_hash=secret_hash,
                    status='online'
                )
                
                # Create owner permission for this home
                HomePermission.objects.create(
                    user=pairing_code.user,
                    home_id=home_id,
                    role='owner',
                    granted_by=pairing_code.user
                )
                
                # Mark pairing code as used
                pairing_code.mark_used(gateway)
                
                response_data = {
                    'gateway_id': gateway.id,
                    'home_id': gateway.home_id,
                    'secret': secret,
                    'message': 'Gateway paired successfully! Store the secret securely.'
                }
                
                response_serializer = CompletePairingResponseSerializer(data=response_data)
                response_serializer.is_valid()
                
                return Response(
                    response_serializer.data,
                    status=status.HTTP_201_CREATED
                )
                
            except PairingCode.DoesNotExist:
                return Response(
                    {'error': 'Invalid pairing code'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GatewayProvisionView(APIView):
    """
    Gateway provisioning endpoint (LEGACY - use pairing code flow instead).
    
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
