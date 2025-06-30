# models.py
from django.db import models
from django.utils import timezone
import json
from django.conf import settings

class SoilSensor(models.Model):
    """Model for soil moisture sensors"""
    SENSOR_TYPES = [
        ('capacitive', 'Capacitive'),
        ('resistive', 'Resistive'), 
        ('tensiometer', 'Tensiometer'),
        ('tdr', 'Time Domain Reflectometry'),
    ]
    
    name = models.CharField(max_length=100)
    sensor_id = models.CharField(max_length=50, unique=True)
    sensor_type = models.CharField(max_length=20, choices=SENSOR_TYPES)
    location = models.CharField(max_length=200)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    depth_cm = models.IntegerField(help_text="Sensor depth in centimeters")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


    def __str__(self):
        return f"{self.name} ({self.sensor_id})"

class SoilMoistureReading(models.Model):
    """Model for individual soil moisture readings"""
    sensor = models.ForeignKey(SoilSensor, on_delete=models.CASCADE, related_name='readings')
    moisture_percentage = models.FloatField(help_text="Moisture percentage (0-100)")
    temperature_celsius = models.FloatField(null=True, blank=True)
    humidity_percentage = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    raw_value = models.IntegerField(null=True, blank=True, help_text="Raw sensor reading")
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['sensor', '-timestamp']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.sensor.name} - {self.moisture_percentage}% at {self.timestamp}"

class PlantProfile(models.Model):
    """Model for different plant types and their moisture requirements"""
    PLANT_CATEGORIES = [
        ('vegetable', 'Vegetable'),
        ('fruit', 'Fruit'),
        ('herb', 'Herb'),
        ('flower', 'Flower'),
        ('tree', 'Tree'),
        ('grass', 'Grass/Lawn'),
        ('succulent', 'Succulent'),
    ]
    
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=PLANT_CATEGORIES)
    optimal_moisture_min = models.FloatField(help_text="Minimum optimal moisture %")
    optimal_moisture_max = models.FloatField(help_text="Maximum optimal moisture %")
    critical_low_moisture = models.FloatField(help_text="Critical low moisture threshold %")
    critical_high_moisture = models.FloatField(help_text="Critical high moisture threshold %")
    watering_frequency_days = models.IntegerField(help_text="Typical watering frequency in days")
    growth_season_start = models.IntegerField(help_text="Growing season start month (1-12)")
    growth_season_end = models.IntegerField(help_text="Growing season end month (1-12)")
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.category})"

class SensorPlantAssignment(models.Model):
    """Model to assign plant profiles to sensors"""
    sensor = models.ForeignKey(SoilSensor, on_delete=models.CASCADE)
    plant_profile = models.ForeignKey(PlantProfile, on_delete=models.CASCADE)
    assigned_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['sensor', 'plant_profile']

class AIInsight(models.Model):
    """Model for AI-generated insights"""
    INSIGHT_TYPES = [
        ('watering_recommendation', 'Watering Recommendation'),
        ('moisture_trend', 'Moisture Trend Analysis'),
        ('plant_health', 'Plant Health Assessment'),
        ('seasonal_pattern', 'Seasonal Pattern'),
        ('anomaly_detection', 'Anomaly Detection'),
        ('optimization', 'Optimization Suggestion'),
        ('alert', 'Alert/Warning'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    sensor = models.ForeignKey(SoilSensor, on_delete=models.CASCADE, related_name='insights')
    insight_type = models.CharField(max_length=30, choices=INSIGHT_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    title = models.CharField(max_length=200)
    description = models.TextField()
    recommendation = models.TextField(blank=True)
    confidence_score = models.FloatField(help_text="AI confidence (0-1)")
    data_analyzed = models.JSONField(default=dict, help_text="Metadata about analyzed data")
    is_read = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sensor', '-created_at']),
            models.Index(fields=['priority', 'is_read']),
        ]

    def __str__(self):
        return f"{self.title} - {self.sensor.name}"

class WeatherData(models.Model):
    """Model for weather data that affects soil moisture"""
    location = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    timestamp = models.DateTimeField()
    temperature_celsius = models.FloatField()
    humidity_percentage = models.FloatField()
    precipitation_mm = models.FloatField(default=0)
    wind_speed_kmh = models.FloatField(null=True, blank=True)
    pressure_hpa = models.FloatField(null=True, blank=True)
    uv_index = models.FloatField(null=True, blank=True)
    
    class Meta:
        unique_together = ['location', 'timestamp']
        ordering = ['-timestamp']

class UserPreferences(models.Model):
    """Model for user AI insight preferences"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    enable_ai_insights = models.BooleanField(default=True)
    insight_frequency = models.CharField(
        max_length=20, 
        choices=[
            ('realtime', 'Real-time'),
            ('hourly', 'Hourly'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
        ],
        default='daily'
    )
    notification_types = models.JSONField(
        default=list,
        help_text="List of insight types to receive notifications for"
    )
    timezone = models.CharField(max_length=50, default='UTC')
    
    def __str__(self):
        return f"{self.user.username} - AI Preferences"
