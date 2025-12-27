"""
Django admin for bridge app
"""
from django.contrib import admin
from .models import BridgeSession


@admin.register(BridgeSession)
class BridgeSessionAdmin(admin.ModelAdmin):
    """Admin for BridgeSession model."""
    list_display = ('gateway', 'ip_address', 'connected_at', 'last_ping', 'messages_sent', 'messages_received')
    list_filter = ('connected_at',)
    search_fields = ('gateway__id', 'gateway__home_id', 'ip_address')
    readonly_fields = ('id', 'gateway', 'channel_name', 'ip_address', 'connected_at', 'last_ping')
    ordering = ('-connected_at',)
