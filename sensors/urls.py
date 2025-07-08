from django.urls import path
from . import views

app_name = 'sensors'

urlpatterns = [
    # Class-based views
    path('', views.SensorListView.as_view(), name='sensor_list'),
    path('api/farms/', views.get_farms_and_fields, name='get_farms_and_fields'),
    path('create/', views.SensorCreateView.as_view(), name='sensor_create'),
    path('<uuid:pk>/', views.SensorDetailView.as_view(), name='sensor_detail'),
    path('<uuid:pk>/update/', views.SensorUpdateView.as_view(), name='sensor_update'),
    path('<uuid:pk>/delete/', views.SensorDeleteView.as_view(), name='sensor_delete'),
    
    
    # API endpoints
    path('types/<int:sensor_type_id>/', views.get_sensor_type_details, name='sensor_type_details'),
    path('<uuid:pk>/calibrate/', views.sensor_calibrate, name='sensor_calibrate'),
    path('<uuid:pk>/toggle-status/', views.sensor_toggle_status, name='sensor_toggle_status'),
]