from django.db import models

class Field(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    area = models.FloatField(help_text="Area in hectares")
    crop_type = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Sensor(models.Model):
    SENSOR_TYPES = [
        ('soil_moisture', 'Soil Moisture'),
        ('temperature', 'Temperature'),
        ('humidity', 'Humidity'),
    ]

    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='sensors')
    sensor_type = models.CharField(max_length=20, choices=SENSOR_TYPES)
    installation_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.get_sensor_type_display()} - {self.field.name}"

class SensorReading(models.Model):
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE)
    value = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.sensor}: {self.value} at {self.timestamp}"

class WeatherData(models.Model):
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    temperature = models.FloatField()
    humidity = models.FloatField()
    rainfall = models.FloatField(help_text="Rainfall in mm")
    wind_speed = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Weather at {self.field.name} - {self.timestamp}"

class IrrigationZone(models.Model):
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='zones')
    name = models.CharField(max_length=100)
    area = models.FloatField(help_text="Area in square meters")
    crop_type = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.field.name})"

class IrrigationSchedule(models.Model):
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('custom', 'Custom'),
    ]

    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    duration_minutes = models.PositiveIntegerField(help_text="Duration in minutes")
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    start_time = models.TimeField()
    auto_weather_adjust = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.field.name}) - {self.get_frequency_display()}"

class IrrigationLog(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'),
        ('failed', 'Failed'),
    ]
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('custom', 'Custom'),
    ]


    name = models.ForeignKey(Field, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    start_time_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(help_text="Actual duration in minutes", null=True, blank=True)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    auto_weather_adjust = models.BooleanField(default=False)
    is_active = models.BooleanField(blank=True)

    class Meta:
        ordering = ['-start_time']

    def __str__(self):
        return f"Irrigation at {self.field.name} - {self.status}"

