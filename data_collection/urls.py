# urls.py
from django.urls import path
from .views import SensorDataAPIView, WeatherDataAPIView

urlpatterns = [
    path('api/sensor-data/', SensorDataAPIView.as_view(), name='sensor-data'),
    path('api/weather-data/', WeatherDataAPIView.as_view(), name='weather-data'),
]