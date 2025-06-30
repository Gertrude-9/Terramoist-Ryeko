# urls.py
from django.urls import path
from . import views

app_name = 'fields'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    # urls.py
    path('fields/create/', views.field_create, name='field_create'),
    path('list/', views.field_list, name='field_list'),  
    path('field/<int:field_id>/', views.field_detail, name='field_detail'),
    path('api/sensor/<uuid:sensor_id>/readings/', views.sensor_readings_api, name='sensor_readings_api'),
    path('api/add-reading/', views.add_sensor_reading, name='add_sensor_reading'),
    path('alerts/', views.alerts_view, name='alerts'),
    path('alerts/<int:alert_id>/resolve/', views.resolve_alert, name='resolve_alert'),
    path('sensor-create/', views.sensor_create, name='sensor_create'),

    # New URLs for CRUD operations
  
    path('field/<int:field_id>/edit/', views.field_update, name='field_update'),
    path('field/<int:field_id>/delete/', views.field_delete, name='field_delete'),
    path('farms/<int:farm_id>/fields/create/', views.field_create, name='field_create'),
    # path('farms/<int:farm_id>/fields/<int:field_id>/sensors/add/', views.sensor_create, name='sensor_create'),
    # path('farms/<int:farm_id>/sensors/select-field/', views.sensor_select_field, name='sensor_select_field'),
    
   
    


]