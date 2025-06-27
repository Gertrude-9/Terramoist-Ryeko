# fields/admin.py
from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from django.utils.html import format_html
from .models import Field, IrrigationZone, Sensor
from .utils import FieldGeometryUtils, IrrigationGDALOperations, SensorGDALOperations

class IrrigationZoneInline(admin.TabularInline):
    model = IrrigationZone
    extra = 0
    fields = ('name', 'zone_type', 'area_acres', 'slope')
    readonly_fields = ('area_acres',)

    def area_acres(self, obj):
        return round(FieldGeometryUtils.calculate_field_area(obj.boundary), 2)
    area_acres.short_description = 'Area (acres)'

class SensorInline(admin.TabularInline):
    model = Sensor
    extra = 0
    fields = ('name', 'sensor_type', 'status', 'last_reading')

@admin.register(Field)
class FieldAdmin(GISModelAdmin):
    list_display = ('name', 'farm', 'crop_type', 'area_acres', 'valid_geometry', 'map_preview')
    list_filter = ('farm', 'crop_type', 'soil_type')
    search_fields = ('name', 'farm__name')
    inlines = [IrrigationZoneInline, SensorInline]
    actions = ['calculate_statistics']
    readonly_fields = ('map_preview', 'valid_geometry', 'area_acres')

    fieldsets = (
        ('Basic Information', {
            'fields': ('farm', 'name', 'crop_type', 'soil_type')
        }),
        ('Geospatial Data', {
            'fields': ('boundary', 'map_preview', 'valid_geometry', 'area_acres'),
            'classes': ('collapse', 'wide')
        }),
    )

    def area_acres(self, obj):
        return round(FieldGeometryUtils.calculate_field_area(obj.boundary), 2)
    area_acres.short_description = 'Area (acres)'

    def valid_geometry(self, obj):
        validation = FieldGeometryUtils.validate_field_polygon(obj.boundary)
        if validation['is_valid']:
            return format_html('<span style="color: green;">✓ Valid</span>')
        return format_html('<span style="color: red;">✗ Invalid: {}</span>', validation['errors'][0])
    valid_geometry.short_description = 'Geometry Status'

    def map_preview(self, obj):
        if obj.boundary:
            return format_html(
                '<div style="width: 300px; height: 200px;" data-geometry="{}"></div>',
                obj.boundary.geojson
            )
        return "No boundary defined"
    map_preview.short_description = 'Boundary Preview'

    def calculate_statistics(self, request, queryset):
        for field in queryset:
            # Example of using your utils in admin actions
            stats = FieldGeometryUtils.validate_field_polygon(field.boundary)
            self.message_user(
                request,
                f"Stats for {field.name}: Area: {self.area_acres(field)} acres, "
                f"Perimeter: {stats.get('perimeter_meters', 0):.2f} meters"
            )
    calculate_statistics.short_description = "Calculate field statistics"

@admin.register(IrrigationZone)
class IrrigationZoneAdmin(GISModelAdmin):
    list_display = ('name', 'field', 'zone_type', 'area_acres', 'water_needs')
    list_filter = ('zone_type', 'field__farm')
    readonly_fields = ('area_acres', 'water_needs_display')

    def area_acres(self, obj):
        return round(FieldGeometryUtils.calculate_field_area(obj.boundary), 2)
    area_acres.short_description = 'Area (acres)'

    def water_needs(self, obj):
        needs = IrrigationGDALOperations.calculate_zone_water_needs(obj.boundary)
        return f"{needs['daily_water_need_liters']:.1f} L/day"
    water_needs.short_description = 'Water Needs'

@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    list_display = ('name', 'field', 'sensor_type', 'status', 'coverage_area')
    list_filter = ('sensor_type', 'status', 'field__farm')
    readonly_fields = ('coverage_area',)

    def coverage_area(self, obj):
        coverage = SensorGDALOperations.create_sensor_coverage_area(obj.location, obj.coverage_radius)
        return f"{FieldGeometryUtils.calculate_field_area(coverage):.2f} acres"
    coverage_area.short_description = 'Coverage Area'

# Add GIS-specific admin customization
admin.site.site_header = "Farm Management GIS Admin"
admin.site.index_title = "Geospatial Farm Administration"