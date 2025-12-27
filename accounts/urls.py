"""
URL configuration for accounts app
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),  # ⭐ Custom JWT with home_ids
    path('refresh/', TokenRefreshView.as_view(), name='refresh'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    
    # User profile
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
]
