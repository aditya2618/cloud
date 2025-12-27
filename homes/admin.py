"""
Django admin for homes app
"""
from django.contrib import admin
from .models import HomeMetadata


@admin.register(HomeMetadata)
class HomeMetadataAdmin(admin.ModelAdmin):
    """Admin for HomeMetadata model."""
    list_display = ('id', 'name', 'gateway', 'device_count', 'scene_count', 'automation_count', 'last_synced')
    list_filter = ('created_at', 'last_synced')
    search_fields = ('id', 'name', 'gateway__id')
    readonly_fields = ('id', 'created_at', 'updated_at', 'last_synced')
    ordering = ('-created_at',)
