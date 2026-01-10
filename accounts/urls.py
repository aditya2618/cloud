"""
URL configuration for accounts app
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication - with trailing slash
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),  # ⭐ Custom JWT with home_ids
    path('refresh/', TokenRefreshView.as_view(), name='refresh'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    
    # Authentication - without trailing slash (for mobile app compatibility)
    path('register', views.RegisterView.as_view(), name='register-noslash'),
    path('login', views.LoginView.as_view(), name='login-noslash'),
    path('refresh', TokenRefreshView.as_view(), name='refresh-noslash'),
    path('logout', views.LogoutView.as_view(), name='logout-noslash'),
    
    # User profile
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('profile', views.UserProfileView.as_view(), name='profile-noslash'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('change-password', views.ChangePasswordView.as_view(), name='change-password-noslash'),
]

