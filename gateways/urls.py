"""
URL configuration for gateways app
"""
from django.urls import path
from . import views

app_name = 'gateways'

urlpatterns = [
    # Pairing code flow (NEW - Production ready)
    path('request-pairing/', views.PairingCodeRequestView.as_view(), name='request-pairing'),
    path('verify-pairing/<str:code>/', views.VerifyPairingCodeView.as_view(), name='verify-pairing'),
    path('complete-pairing/', views.CompletePairingView.as_view(), name='complete-pairing'),
    
    # Gateway management (LEGACY)
    path('provision/', views.GatewayProvisionView.as_view(), name='provision'),
    path('', views.GatewayListView.as_view(), name='list'),
    path('<uuid:pk>/', views.GatewayDetailView.as_view(), name='detail'),
    path('<uuid:pk>/revoke/', views.GatewayRevokeView.as_view(), name='revoke'),
    
    # Home permissions
    path('homes/<uuid:home_id>/permissions/', views.HomePermissionListView.as_view(), name='home-permissions'),
]
