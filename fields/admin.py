# fields/admin.py

from django.contrib import admin
from .models import Alert
from .models import Farm, Field
from sensors.models import SensorType, Sensor
from data_collection.models import SensorReading


# Register your models here.

@admin.register(Farm)
class FarmAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'location', 'created_at')
    search_fields = ('name', 'owner__username', 'location')
    list_filter = ('owner',)

@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    # Corrected list_display to use 'area', 'latitude', 'longitude'
    list_display = ('name', 'farm', 'area', 'crop_type', 'latitude', 'longitude', 'is_active', 'planting_date', 'created_at')
    list_filter = ('farm', 'crop_type', 'soil_type', 'is_active', 'irrigation_system')
    search_fields = ('name', 'description', 'farm__name')
    raw_id_fields = ('farm',) # Useful for ForeignKey fields when many instances exist

@admin.register(SensorType)
class SensorTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'unit')
    search_fields = ('name',)

@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    # Corrected list_display to use 'latitude', 'longitude'
    list_display = ('name', 'field', 'sensor_type', 'latitude', 'longitude', 'depth', 'is_active', 'status', 'device_id', 'installation_date')
    list_filter = ('field', 'sensor_type', 'is_active', 'status')
    search_fields = ('name', 'device_id', 'description', 'field__name', 'sensor_type__name')
    raw_id_fields = ('field', 'sensor_type')
    fieldsets = (
        (None, {
            'fields': ('field', 'name', 'sensor_type', 'device_id', 'status', 'is_active', 'description')
        }),
        ('Location & Depth', {
            'fields': ('latitude', 'longitude', 'depth')
        }),
        ('Calibration', {
            'fields': ('calibration_slope', 'calibration_offset', 'last_calibration')
        }),
        ('Operational Details', {
            'fields': ('reading_frequency', 'battery_level', 'min_threshold', 'max_threshold')
        }),
    )

@admin.register(SensorReading)
class SensorReadingAdmin(admin.ModelAdmin):
    list_display = ('sensor', 'value', 'timestamp')
    list_filter = ('sensor', 'sensor__sensor_type', 'timestamp')
    search_fields = ('sensor__name', 'sensor__device_id')
    date_hierarchy = 'timestamp'
    raw_id_fields = ('sensor',)

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('sensor', 'alert_type', 'severity', 'is_resolved', 'created_at', 'resolved_at', 'resolved_by')
    list_filter = ('alert_type', 'severity', 'is_resolved', 'created_at', 'sensor__field__farm', 'sensor__field', 'sensor__sensor_type')
    search_fields = ('message', 'sensor__name', 'sensor__field__name')
    date_hierarchy = 'created_at'
    raw_id_fields = ('sensor', 'resolved_by')
    actions = ['mark_as_resolved']

    def mark_as_resolved(self, request, queryset):
        for alert in queryset:
            alert.resolve(user=request.user)
        self.message_user(request, f"{queryset.count()} alerts marked as resolved.")
    mark_as_resolved.short_description = "Mark selected alerts as resolved"

