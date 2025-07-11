# irrigation/admin.py
from django.contrib import admin
from .models import Field, Sensor, SensorReading, WeatherData, IrrigationSchedule, IrrigationLog

@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'area', 'crop_type']
    search_fields = ['name', 'location']

@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    list_display = ['field', 'sensor_type', 'installation_date', 'is_active']
    list_filter = ['sensor_type', 'is_active']

@admin.register(SensorReading)
class SensorReadingAdmin(admin.ModelAdmin):
    list_display = ['sensor', 'value', 'timestamp']
    list_filter = ['sensor__sensor_type']
    date_hierarchy = 'timestamp'

@admin.register(WeatherData)
class WeatherDataAdmin(admin.ModelAdmin):
    list_display = ['field', 'temperature', 'humidity', 'rainfall', 'timestamp']
    date_hierarchy = 'timestamp'

@admin.register(IrrigationSchedule)
class IrrigationScheduleAdmin(admin.ModelAdmin):
    list_display = ['field', 'start_time', 'duration_minutes', 'frequency', 'is_active', 'auto_weather_adjust']
    list_filter = ['frequency', 'is_active']

@admin.register(IrrigationLog)
class IrrigationLogAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_time', 'frequency', 'duration_minutes', 'is_active', 'auto_weather_adjust']
    list_filter = ['is_active']
    date_hierarchy = 'start_time'
    search_fields = ['field__name', 'reason']