# fields/models.py

from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

class Farm(models.Model):
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='fields_farms')
    location = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Field(models.Model):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='fields')
    name = models.CharField(max_length=200)
    area = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                               help_text="Field area in hectares")
    crop_type = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, 
                                   help_text="GPS latitude coordinate")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True,
                                    help_text="GPS longitude coordinate")
    SOIL_TYPE_CHOICES = [
        ('SANDY', 'Sandy'),
        ('CLAY', 'Clay'),
        ('LOAM', 'Loam'),
        ('SILT', 'Silt'),
        ('PEAT', 'Peat'),
        ('CHALKY', 'Chalky'),
    ]
    soil_type = models.CharField(max_length=50, choices=SOIL_TYPE_CHOICES, null=True, blank=True,
                                 help_text="Predominant soil type in this field")
    # Added fields to resolve the FieldError
    planting_date = models.DateField(null=True, blank=True, help_text="Date when crops were planted in this field")
    geometry = models.TextField(null=True, blank=True, help_text="GeoJSON or other spatial data representing the field boundary")
    description = models.TextField(null=True, blank=True,
                                   help_text="Additional notes or description about this field")
    
    IRRIGATION_SYSTEM_CHOICES = [
        ('DRIP', 'Drip Irrigation'),
        ('SPRINKLER', 'Sprinkler System'),
        ('FLOOD', 'Flood Irrigation'),
        ('NONE', 'None'),
    ]
    irrigation_system = models.CharField(max_length=50, choices=IRRIGATION_SYSTEM_CHOICES, null=True, blank=True,
                                         help_text="Type of irrigation system used")
    is_active = models.BooleanField(default=True,
                                    help_text="Check if this field is currently active for monitoring")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.farm.name} - {self.name}"

    class Meta:
        unique_together = ('farm', 'name')


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
    
    # Renamed from 'field' to 'farm_field' for clarity if needed, but keeping 'field' to match form request
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='sensors')
    
    name = models.CharField(max_length=100, blank=True, null=True, help_text="A unique name for the sensor") # Added
    sensor_type = models.ForeignKey(SensorType, on_delete=models.CASCADE)
    
    # Renamed from position_x, position_y to latitude, longitude to match form request
    latitude = models.DecimalField(max_digits=10, decimal_places=6, help_text="GPS latitude of sensor position") 
    longitude = models.DecimalField(max_digits=10, decimal_places=6, help_text="GPS longitude of sensor position") 
    
    depth = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, 
                                help_text="Depth of sensor installation (e.g., in cm or inches)") # Added

    is_active = models.BooleanField(default=True)
    
    # Renamed from installed_date to installation_date to match form request
    installation_date = models.DateTimeField(auto_now_add=True) 

    device_id = models.CharField(max_length=100, unique=True, null=True, blank=True,
                                 help_text="Unique identifier for the physical sensor device") # Added

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Under Maintenance'),
        ('faulty', 'Faulty'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active',
                              help_text="Current operational status of the sensor") # Added

    description = models.TextField(null=True, blank=True,
                                   help_text="Additional notes or description about the sensor") # Added
    
    # Calibration details
    calibration_slope = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True,
                                           help_text="Slope value for sensor calibration (m in y=mx+c)") # Added
    calibration_offset = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True,
                                            help_text="Offset value for sensor calibration (c in y=mx+c)") # Added
    last_calibration = models.DateField(null=True, blank=True,
                                        help_text="Date of the last sensor calibration") # Added

    # Reading frequency (e.g., how often it sends data)
    reading_frequency = models.IntegerField(null=True, blank=True,
                                            help_text="Frequency of readings in minutes (e.g., 60 for hourly)") # Added

    # Battery level
    battery_level = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                        help_text="Current battery level (%)") # Added

    # Alert thresholds (existing fields)
    min_threshold = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_threshold = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        # Adjusted unique_together to use new field names if necessary
        # Keeping as is if position_x/y were just conceptual and lat/lon are the actual unique combination
        unique_together = ['field', 'latitude', 'longitude'] 
        ordering = ['name', 'field'] # Example ordering

    
    def __str__(self):
        # Updated __str__ to use 'name' if available, otherwise fallback to sensor_type and coordinates
        return f"{self.name or self.sensor_type.name} - {self.field.name} ({self.latitude}, {self.longitude})"

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

class Alert(models.Model):
    ALERT_TYPES = [
        ('low', 'Below Threshold'),
        ('high', 'Above Threshold'),
        ('malfunction', 'Sensor Malfunction'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='medium')
    message = models.TextField()
    reading_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.sensor.field.name} - {self.get_alert_type_display()} - {self.created_at}"
    
    def resolve(self, user=None):
        self.is_resolved = True
        self.resolved_at = timezone.now()
        if user:
            self.resolved_by = user
        self.save()
