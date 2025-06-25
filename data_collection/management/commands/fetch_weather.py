# management/commands/fetch_weather.py
from django.core.management.base import BaseCommand
from django.conf import settings
from farms.models import Farm, Sensor, SensorData
import requests
from django.utils import timezone

class Command(BaseCommand):
    help = 'Fetches weather data for all farms'

    def handle(self, *args, **options):
        for farm in Farm.objects.all():
            try:
                api_key = settings.WEATHER_API_KEY
                url = f"https://api.openweathermap.org/data/2.5/weather?lat={farm.latitude}&lon={farm.longitude}&appid={api_key}&units=metric"
                
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    
                    # Get or create sensors
                    temp_sensor, _ = Sensor.objects.get_or_create(
                        farm=farm,
                        sensor_type='TEMP',
                        defaults={'sensor_id': f'TEMP_{farm.id}', 'location': 'Weather API'}
                    )
                    
                    humidity_sensor, _ = Sensor.objects.get_or_create(
                        farm=farm,
                        sensor_type='HUMID',
                        defaults={'sensor_id': f'HUMID_{farm.id}', 'location': 'Weather API'}
                    )
                    
                    rain_sensor, _ = Sensor.objects.get_or_create(
                        farm=farm,
                        sensor_type='RAIN',
                        defaults={'sensor_id': f'RAIN_{farm.id}', 'location': 'Weather API'}
                    )
                    
                    # Create sensor data
                    SensorData.objects.create(
                        sensor=temp_sensor,
                        value=data['main']['temp'],
                        is_api_data=True,
                        source='OpenWeatherMap'
                    )
                    
                    SensorData.objects.create(
                        sensor=humidity_sensor,
                        value=data['main']['humidity'],
                        is_api_data=True,
                        source='OpenWeatherMap'
                    )
                    
                    rainfall = data.get('rain', {}).get('1h', 0)
                    SensorData.objects.create(
                        sensor=rain_sensor,
                        value=rainfall,
                        is_api_data=True,
                        source='OpenWeatherMap'
                    )
                    
                    self.stdout.write(self.style.SUCCESS(f'Successfully fetched weather for {farm.name}'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error fetching weather for {farm.name}: {str(e)}'))