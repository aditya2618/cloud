from django.urls import path
from . import views

urlpatterns = [
    # Existing device APIs
    path('<uuid:home_id>/devices/', views.DeviceListView.as_view(), name='device-list'),
    path('<uuid:home_id>/devices/<int:pk>/control/', views.DeviceControlView.as_view(), name='device-control'),
    
    # New data sync APIs - these mirror local server APIs
    path('<uuid:home_id>/entities/', views.EntitiesListView.as_view(), name='entities-list'),
    path('<uuid:home_id>/scenes/', views.ScenesListView.as_view(), name='scenes-list'),
    path('<uuid:home_id>/automations/', views.AutomationsListView.as_view(), name='automations-list'),
    path('<uuid:home_id>/data/', views.HomeDataView.as_view(), name='home-data'),
]

