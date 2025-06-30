# admin.py
from django.contrib import admin
from .models import IrrigationZone, IrrigationSchedule, IrrigationLog, WeatherData

@admin.register(IrrigationZone)
class IrrigationZoneAdmin(admin.ModelAdmin):
    list_display = ['name', 'area_sqm', 'soil_type', 'plant_type', 'created_at']
    list_filter = ['soil_type', 'plant_type']
    search_fields = ['name', 'description']

@admin.register(IrrigationSchedule)
class IrrigationScheduleAdmin(admin.ModelAdmin):
    list_display = ['name', 'zone', 'start_time', 'duration_minutes', 'frequency', 'status']
    list_filter = ['status', 'frequency', 'auto_weather_adjust']
    search_fields = ['name', 'zone__name']

@admin.register(IrrigationLog)
class IrrigationLogAdmin(admin.ModelAdmin):
    list_display = ['zone', 'start_time', 'duration_actual', 'water_volume_liters']
    list_filter = ['start_time', 'zone']
    readonly_fields = ['start_time']

@admin.register(WeatherData)
class WeatherDataAdmin(admin.ModelAdmin):
    list_display = ['date', 'temperature_max', 'temperature_min', 'precipitation']
    list_filter = ['date']