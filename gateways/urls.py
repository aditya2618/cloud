"""
URL configuration for gateways app
"""
from django.urls import path
from . import views

app_name = 'gateways'

urlpatterns = [
    # Gateway management
    path('provision/', views.GatewayProvisionView.as_view(), name='provision'),
    path('', views.GatewayListView.as_view(), name='list'),
    path('<uuid:pk>/', views.GatewayDetailView.as_view(), name='detail'),
    path('<uuid:pk>/revoke/', views.GatewayRevokeView.as_view(), name='revoke'),
    
    # Home permissions
    path('homes/<uuid:home_id>/permissions/', views.HomePermissionListView.as_view(), name='home-permissions'),
]
