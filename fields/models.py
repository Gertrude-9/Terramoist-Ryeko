# fields/models.py

from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

from farms.models import Farm
from sensors.models import Sensor, SensorType



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

class SensorReading(models.Model):
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, related_name='readings')
    value = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)


