import uuid
from django.db import models

class SensorType(models.Model):
    SENSOR_TYPES = [
        ('humidity', 'Humidity'),
        ('soil_moisture', 'Soil Moisture'),
        ('temperature', 'Temperature'),
    ]
    
    name = models.CharField(max_length=50, choices=SENSOR_TYPES, unique=True)
    unit = models.CharField(max_length=10)  # %, °C, etc.
    
    def __str__(self):
        return f"{self.get_name_display()} ({self.unit})"

class Sensor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Use string reference to avoid circular import with Field model
    field = models.ForeignKey('fields.Field', on_delete=models.CASCADE, related_name='sensors')

    name = models.CharField(max_length=100, blank=True, null=True, help_text="A unique name for the sensor")
    sensor_type = models.ForeignKey(SensorType, on_delete=models.CASCADE)
    
    latitude = models.DecimalField(max_digits=10, decimal_places=6, help_text="GPS latitude of sensor position") 
    longitude = models.DecimalField(max_digits=10, decimal_places=6, help_text="GPS longitude of sensor position") 
    
    depth = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, 
                                help_text="Depth of sensor installation (e.g., in cm or inches)")

    is_active = models.BooleanField(default=True)
    
    installation_date = models.DateTimeField(auto_now_add=True) 

    device_id = models.CharField(max_length=100, unique=True, null=True, blank=True,
                                 help_text="Unique identifier for the physical sensor device")

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Under Maintenance'),
        ('faulty', 'Faulty'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active',
                              help_text="Current operational status of the sensor")

    description = models.TextField(null=True, blank=True,
                                   help_text="Additional notes or description about the sensor")
    
    calibration_slope = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True,
                                           help_text="Slope value for sensor calibration (m in y=mx+c)")
    calibration_offset = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True,
                                            help_text="Offset value for sensor calibration (c in y=mx+c)")
    last_calibration = models.DateField(null=True, blank=True,
                                        help_text="Date of the last sensor calibration")

    reading_frequency = models.IntegerField(null=True, blank=True,
                                            help_text="Frequency of readings in minutes (e.g., 60 for hourly)")

    battery_level = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                        help_text="Current battery level (%)")

    min_threshold = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_threshold = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        unique_together = ['field', 'latitude', 'longitude'] 
        ordering = ['name', 'field']

    def __str__(self):
        return f"{self.name or self.sensor_type.name} - {self.field.name} ({self.latitude}, {self.longitude})"


