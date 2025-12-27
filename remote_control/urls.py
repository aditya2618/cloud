"""
Remote Control API URLs
"""
from django.urls import path
from . import views

urlpatterns = [
    # Device control
    path('homes/<uuid:home_id>/entities/<int:entity_id>/control', 
         views.control_entity, 
         name='remote-control-entity'),
    
    # Scene execution
    path('homes/<uuid:home_id>/scenes/<int:scene_id>/run', 
         views.run_scene, 
         name='remote-run-scene'),
    
    # Gateway status
    path('homes/<uuid:home_id>/status', 
         views.get_gateway_status, 
         name='remote-gateway-status'),
]
