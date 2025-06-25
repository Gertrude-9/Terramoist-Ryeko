from django.shortcuts import render
from django.views import View
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response  # ✅ Correct import
import requests
from django.conf import settings
from datetime import timedelta
from .models import Farm
# from .models import Sensor, SensorData  # Uncomment when ready

class SensorDashboardView(View):
    template_name = 'sensor_data.html'

    def get(self, request):
        farms = Farm.objects.filter(owner=request.user)
        # sensors = Sensor.objects.filter(farm__in=farms, is_active=True).prefetch_related('sensordata_set')  # commented out

        # for sensor in sensors:
        #     sensor.latest_data = sensor.sensordata_set.order_by('-timestamp').first()
        #     if sensor.sensor_type in ['TEMP', 'SOIL_TEMP']:
        #         sensor.unit = '°C'
        #     elif sensor.sensor_type == 'HUMID':
        #         sensor.unit = '%'
        #     elif sensor.sensor_type == 'RAIN':
        #         sensor.unit = 'mm'
        #     else:
        #         sensor.unit = ''

        context = {
            'farms': farms,
            # 'sensors': sensors
        }
        return render(request, self.template_name, context)


class WeatherDashboardView(View):
    template_name = 'weather_data.html'

    compass_directions = [
        "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
    ]
    icons = {
        'Clear': '☀️',
        'Clouds': '⛅',
        'Rain': '🌧️',
        'Drizzle': '🌦️',
        'Thunderstorm': '⛈️',
        'Snow': '❄️',
        'Mist': '🌫️'
    }

    def get(self, request, farm_id):
        try:
            farm = Farm.objects.get(id=farm_id, owner=request.user)

            api_key = settings.WEATHER_API_KEY
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={farm.latitude}&lon={farm.longitude}&appid={api_key}&units=metric"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()

                weather_data = {
                    'temperature': data['main']['temp'],
                    'condition': data['weather'][0]['main'],
                    'feels_like': data['main']['feels_like'],
                    'temp_max': data['main']['temp_max'],
                    'temp_min': data['main']['temp_min'],
                    'humidity': data['main']['humidity'],
                    'dew_point': round(data['main']['temp'] - (100 - data['main']['humidity']) / 5, 1),
                    'pressure': data['main']['pressure'],
                    'wind_speed': data['wind']['speed'] * 3.6,
                    'wind_direction': self.deg_to_compass(data['wind'].get('deg', 0)),
                    'wind_gust': data['wind'].get('gust', 0) * 3.6,
                    'visibility': data.get('visibility', 10000) / 1000,
                    'rainfall': data.get('rain', {}).get('1h', 0),
                    'rain_1h': data.get('rain', {}).get('1h', 0),
                    'uv_index': self.get_uv_index(farm.latitude, farm.longitude),
                    'pressure_trend': 'Steady'  # Placeholder
                }

                forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={farm.latitude}&lon={farm.longitude}&appid={api_key}&units=metric"
                forecast_response = requests.get(forecast_url, timeout=5)
                forecast = []

                if forecast_response.status_code == 200:
                    forecast_data = forecast_response.json()
                    for i in range(5):
                        day_data = forecast_data['list'][i * 8]
                        forecast.append({
                            'day': (timezone.now() + timedelta(days=i)).strftime('%a'),
                            'icon': self.get_weather_icon(day_data['weather'][0]['main']),
                            'temp_max': day_data['main']['temp_max'],
                            'temp_min': day_data['main']['temp_min']
                        })

                context = {
                    'farm': farm,
                    'weather_data': weather_data,
                    'forecast': forecast,
                    'chart_labels': [],  # Replace with actual sensor chart data if needed
                    'temperature_data': [],
                    'rainfall_data': []
                }

                return render(request, self.template_name, context)

            return render(request, self.template_name, {'error': 'Failed to fetch weather data'})

        except Farm.DoesNotExist:
            return render(request, self.template_name, {'error': "Farm not found or you don't have permission"})

    def deg_to_compass(self, degrees):
        val = int((degrees / 22.5) + 0.5)
        return self.compass_directions[val % 16]

    def get_weather_icon(self, condition):
        return self.icons.get(condition, '🌈')

    def get_uv_index(self, lat, lon):
        return 5  # Placeholder for UV index


class SensorDataAPIView(APIView):
    """
    API endpoint to get recent sensor data.
    """
    def get(self, request):
        now = timezone.now()
        dummy_data = [
            {"sensor_id": 1, "value": 25.4, "timestamp": now.isoformat()},
            {"sensor_id": 2, "value": 60, "timestamp": now.isoformat()},
        ]
        return Response({"data": dummy_data}, status=status.HTTP_200_OK)  # ✅ Corrected


class WeatherDataAPIView(APIView):
    """
    API endpoint to get weather data for a farm.
    """
    def get(self, request, farm_id=None):
        dummy_weather = {
            "temperature": 22.5,
            "condition": "Clear",
            "humidity": 55,
            "wind_speed": 12,
            "wind_direction": "NE",
            "rainfall": 0,
            "uv_index": 5,
        }
        return Response({"weather": dummy_weather}, status=status.HTTP_200_OK)  # ✅ Corrected
