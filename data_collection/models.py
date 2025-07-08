# models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from sensors.models import Sensor


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

class SensorReading(models.Model):
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, related_name='readings')
    value = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.sensor} - {self.value} at {self.timestamp}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Automatically check thresholds after saving a reading
        self.check_threshold_alerts()
    
    def check_threshold_alerts(self):
        # Import Alert here to avoid circular import issues
        from fields.models import Alert

        sensor = self.sensor
        if sensor.min_threshold is not None and self.value < sensor.min_threshold:
            Alert.objects.create(
                sensor=sensor,
                alert_type='low',
                message=f"{sensor.sensor_type.name} is below minimum threshold: {self.value} < {sensor.min_threshold}",
                reading_value=self.value
            )
        elif sensor.max_threshold is not None and self.value > sensor.max_threshold:
            Alert.objects.create(
                sensor=sensor,
                alert_type='high',
                message=f"{sensor.sensor_type.name} is above maximum threshold: {self.value} > {sensor.max_threshold}",
                reading_value=self.value
            )
