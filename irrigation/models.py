# irrigation/models.py
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone

class IrrigationZone(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    area_sqm = models.DecimalField(max_digits=10, decimal_places=2)
    soil_type = models.CharField(max_length=50, choices=[
        ('clay', 'Clay'),
        ('loam', 'Loam'),
        ('sand', 'Sandy'),
        ('silt', 'Silt'),
    ])
    plant_type = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class IrrigationSchedule(models.Model):
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('every_other_day', 'Every Other Day'),
        ('twice_weekly', 'Twice Weekly'),
        ('weekly', 'Weekly'),
        ('custom', 'Custom'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
    ]
    
    zone = models.ForeignKey(IrrigationZone, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField()
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    auto_weather_adjust = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.zone.name}"

class IrrigationLog(models.Model):
    schedule = models.ForeignKey(IrrigationSchedule, on_delete=models.CASCADE, null=True, blank=True)
    zone = models.ForeignKey(IrrigationZone, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    duration_actual = models.PositiveIntegerField(null=True, blank=True)
    water_volume_liters = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    weather_condition = models.CharField(max_length=50, blank=True)
    soil_moisture_before = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    soil_moisture_after = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.zone.name} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"

class WeatherData(models.Model):
    date = models.DateField()
    temperature_max = models.DecimalField(max_digits=5, decimal_places=2)
    temperature_min = models.DecimalField(max_digits=5, decimal_places=2)
    humidity = models.DecimalField(max_digits=5, decimal_places=2)
    precipitation = models.DecimalField(max_digits=5, decimal_places=2)
    wind_speed = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['date']
    
    def __str__(self):
        return f"Weather {self.date}"