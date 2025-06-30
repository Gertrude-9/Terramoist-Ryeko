# models.py
from django.db import models
from django.contrib.auth import get_user_model

from django.conf import settings

User = get_user_model()

class Farm(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='data_collection_farms')
    size = models.DecimalField(max_digits=10, decimal_places=2)  # in hectares
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Sensor(models.Model):
    SENSOR_TYPES = [
        ('SOIL', 'Soil Moisture'),
        ('TEMP', 'Temperature'),
        ('HUMID', 'Humidity'),
        ('RAIN', 'Rainfall'),
    ]
    
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='sensors')
    sensor_id = models.CharField(max_length=50, unique=True)
    sensor_type = models.CharField(max_length=10, choices=SENSOR_TYPES)
    location = models.CharField(max_length=100)  # Location within the farm
    last_active = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.get_sensor_type_display()} - {self.sensor_id}"

class SensorData(models.Model):
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, related_name='readings')
    timestamp = models.DateTimeField(auto_now_add=True)
    value = models.FloatField()
    
    # For weather API data
    is_api_data = models.BooleanField(default=False)
    source = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['sensor', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.sensor} - {self.value} at {self.timestamp}"