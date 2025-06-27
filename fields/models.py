from django.db import models
from users.models import User
from django.core.validators import MinValueValidator

class Farm(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='farms')
    name = models.CharField(max_length=100)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    total_area = models.FloatField(help_text="Area in acres")
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['location']),
            models.Index(fields=['boundary']),
        ]

    def save(self, *args, **kwargs):
        if self.boundary:
            # Calculate area in acres (converting from sq degrees to acres)
            # Note: This is approximate - for better accuracy use PostGIS geography type
            self.total_area = self.boundary.area * 76900409.5 * 0.000247105
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Field(models.Model):
    SOIL_TYPE_CHOICES = [
        ('clay', 'Clay'),
        ('sandy', 'Sandy'),
        ('loamy', 'Loamy'),
        ('silty', 'Silty'),
        ('peat', 'Peat'),
        ('chalky', 'Chalky'),
    ]
    
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='fields')
    name = models.CharField(max_length=100)
    boundary = models.PolygonField(srid=4326)  # Required field
    crop_type = models.CharField(max_length=100)
    planting_date = models.DateField()
    harvest_date = models.DateField(null=True, blank=True)
    area = models.FloatField(help_text="Area in acres", null=True, blank=True)
    soil_type = models.CharField(max_length=100, choices=SOIL_TYPE_CHOICES)
    elevation = models.FloatField(null=True, blank=True, help_text="Elevation in meters")
    slope = models.FloatField(null=True, blank=True, help_text="Slope percentage")

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['boundary']),
            models.Index(fields=['crop_type']),
        ]

    def save(self, *args, **kwargs):
        # Calculate area in acres (approximate)
        if self.boundary:
            self.area = self.boundary.area * 76900409.5 * 0.000247105
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.crop_type})"


class Sensor(models.Model):
    STATUS_CHOICES = [
        ('optimal', 'Optimal'),
        ('monitoring', 'Needs Monitoring'),
        ('critical', 'Needs Irrigation'),
        ('offline', 'Offline'),
    ]
    
    SENSOR_TYPE_CHOICES = [
        ('moisture', 'Soil Moisture'),
        ('temperature', 'Temperature'),
        ('humidity', 'Humidity'),
        ('ph', 'pH Level'),
        ('nutrient', 'Nutrient Level'),
        ('multi', 'Multi-Sensor'),
    ]
    
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='sensors')
    name = models.CharField(max_length=100)
    location = models.PointField(srid=4326)
    sensor_type = models.CharField(max_length=50, choices=SENSOR_TYPE_CHOICES)
    last_reading = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='optimal')
    installation_date = models.DateField()
    last_maintenance = models.DateField(null=True, blank=True)
    coverage_radius = models.FloatField(
        validators=[MinValueValidator(0)],
        help_text="Sensor coverage radius in meters"
    )

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['location']),
            models.Index(fields=['sensor_type']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class IrrigationZone(models.Model):
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='irrigation_zones')
    name = models.CharField(max_length=100)
    boundary = models.PolygonField(srid=4326)
    water_requirement = models.FloatField(
        help_text="Water requirement in liters per day",
        validators=[MinValueValidator(0)]
    )
    last_irrigated = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.field}"


class WeatherStation(models.Model):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='weather_stations')
    name = models.CharField(max_length=100)
    location = models.PointField(srid=4326)
    last_reading = models.JSONField(null=True, blank=True)
    installation_date = models.DateField()

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} at {self.farm}"