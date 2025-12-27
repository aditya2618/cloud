"""
Django admin for gateways app
"""
from django.contrib import admin
from .models import Gateway, HomePermission


@admin.register(Gateway)
class GatewayAdmin(admin.ModelAdmin):
    """Admin for Gateway model."""
    list_display = ('id', 'home_id', 'owner', 'name', 'status', 'is_active', 'last_seen', 'created_at')
    list_filter = ('status', 'is_active', 'created_at')
    search_fields = ('id', 'home_id', 'name', 'owner__email')
    readonly_fields = ('id', 'home_id', 'secret_hash', 'created_at', 'updated_at', 'last_seen')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Gateway Info', {'fields': ('id', 'home_id', 'owner', 'name')}),
        ('Status', {'fields': ('status', 'is_active', 'last_seen')}),
        ('Security', {'fields': ('secret_hash', 'public_key')}),
        ('Metadata', {'fields': ('version', 'created_at', 'updated_at')}),
    )


@admin.register(HomePermission)
class HomePermissionAdmin(admin.ModelAdmin):
    """Admin for HomePermission model."""
    list_display = ('user', 'home_id', 'role', 'created_at', 'granted_by')
    list_filter = ('role', 'created_at')
    search_fields = ('user__email', 'home_id')
    readonly_fields = ('id', 'created_at')
    ordering = ('-created_at',)
