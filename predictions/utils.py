# utils.py
from django.core.management.base import BaseCommand
from django.utils import timezone
import random
from datetime import timedelta

from fields.models import Field
from predictions.models import SensorData

class Command(BaseCommand):
    """Management command to generate sample sensor data"""
    help = 'Generate sample sensor data for testing'
    
    def add_arguments(self, parser):
        parser.add_argument('--field-id', type=int, required=True)
        parser.add_argument('--days', type=int, default=30)
        parser.add_argument('--readings-per-day', type=int, default=24)
    
    def handle(self, *args, **options):
        field_id = options['field_id']
        days = options['days']
        readings_per_day = options['readings_per_day']
        
        field = Field.objects.get(id=field_id)
        
        # Generate data for the specified number of days
        for day in range(days):
            date = timezone.now() - timedelta(days=day)
            
            for hour in range(0, 24, 24//readings_per_day):
                timestamp = date.replace(hour=hour, minute=0, second=0, microsecond=0)
                
                # Generate realistic sensor data with some variation
                base_moisture = 30 + random.uniform(-15, 15)
                base_temp = 25 + random.uniform(-10, 15)
                base_humidity = 50 + random.uniform(-20, 20)
                
                # Add time-based variations
                if 6 <= hour <= 18:  # Daytime
                    base_temp += random.uniform(5, 10)
                    base_humidity -= random.uniform(5, 15)
                
                SensorData.objects.create(
                    field=field,
                    soil_moisture=max(0, min(100, base_moisture)),
                    temperature=max(-10, min(50, base_temp)),
                    humidity=max(0, min(100, base_humidity)),
                    timestamp=timestamp
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Generated {days * readings_per_day} sensor readings for field {field.name}')
        )