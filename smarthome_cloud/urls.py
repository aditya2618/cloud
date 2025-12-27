"""
Main URL configuration for smarthome_cloud project
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/auth/', include('accounts.urls')),
    path('api/gateways/', include('gateways.urls')),
    path('api/remote/', include('remote_control.urls')),
]
