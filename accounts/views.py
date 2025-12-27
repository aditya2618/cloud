"""
Authentication views for user registration and login
"""
from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import get_user_model
from .serializers import UserRegistrationSerializer, UserSerializer, ChangePasswordSerializer
from .login_serializer import LoginSerializer, JWTResponseSerializer
from .jwt_utils import generate_access_token, generate_refresh_token, get_user_homes

User = get_user_model()


class LoginView(APIView):
    """
    Login endpoint with JWT containing home_ids.
    
    POST /api/auth/login
    Body: { "email": "user@example.com", "password": "pass" }
    Response: {
        "access": "jwt_token",
        "refresh": "refresh_token",
        "user": {...},
        "homes": ["uuid1", "uuid2", ...]
    }
    """
    permission_classes = (permissions.AllowAny,)
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        # Generate JWT tokens with custom claims
        access_token = generate_access_token(user)
        refresh_token = generate_refresh_token(user)
        homes = get_user_homes(user)
        
        response_data = {
            'access': access_token,
            'refresh': refresh_token,
            'user': UserSerializer(user).data,
            'homes': homes  # ⭐ List of accessible home_ids
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class RegisterView(generics.CreateAPIView):
    """
    User registration endpoint.
    
    POST /api/auth/register
    Body: { "email", "password", "password2", "first_name", "last_name" }
    """
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserRegistrationSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate JWT tokens using custom utilities (same as login)
        access_token = generate_access_token(user)
        refresh_token = generate_refresh_token(user)
        homes = get_user_homes(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'access': access_token,
            'refresh': refresh_token,
            'homes': homes,
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    """
    Logout endpoint (blacklist refresh token).
    
    POST /api/auth/logout
    Body: { "refresh": "refresh_token_string" }
    """
    permission_classes = (permissions.IsAuthenticated,)
    
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response(
                {"message": "Successfully logged out"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Get or update current user profile.
    
    GET /api/auth/profile
    PATCH /api/auth/profile
    """
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """
    Change password endpoint.
    
    POST /api/auth/change-password
    Body: { "old_password", "new_password", "new_password2" }
    """
    permission_classes = (permissions.IsAuthenticated,)
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            # Check old password
            if not request.user.check_password(serializer.data.get("old_password")):
                return Response(
                    {"old_password": ["Wrong password."]},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Set new password
            request.user.set_password(serializer.data.get("new_password"))
            request.user.save()
            
            return Response(
                {"message": "Password changed successfully"},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
