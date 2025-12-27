from django.urls import path
from . import views

urlpatterns = [
    path('<uuid:home_id>/devices/', views.DeviceListView.as_view(), name='device-list'),
    path('<uuid:home_id>/devices/<int:pk>/control/', views.DeviceControlView.as_view(), name='device-control'),
]
