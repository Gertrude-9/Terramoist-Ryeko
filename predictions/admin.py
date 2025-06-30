# admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import (
    SoilSensor, SoilMoistureReading, PlantProfile, 
    SensorPlantAssignment, AIInsight, WeatherData, UserPreferences
)

@admin.register(SoilSensor)
class SoilSensorAdmin(admin.ModelAdmin):
    list_display = ['name', 'sensor_id', 'sensor_type', 'location', 'owner', 'is_active', 'created_at']
    list_filter = ['sensor_type', 'is_active', 'created_at']
    search_fields = ['name', 'sensor_id', 'location', 'owner__username']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'sensor_id', 'sensor_type', 'owner')
        }),
        ('Location', {
            'fields': ('location', 'latitude', 'longitude', 'depth_cm')
        }),
        ('Status', {
            'fields': ('is_active', 'created_at')
        }),
    )

@admin.register(SoilMoistureReading)
class SoilMoistureReadingAdmin(admin.ModelAdmin):
    list_display = ['sensor', 'moisture_percentage', 'temperature_celsius', 'timestamp']
    list_filter = ['sensor', 'timestamp']
    search_fields = ['sensor__name', 'sensor__sensor_id']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    def get_queryset(self, request):
        # Limit to recent readings for performance
        qs = super().get_queryset(request)
        return qs.filter(timestamp__gte=timezone.now() - timedelta(days=30))

@admin.register(PlantProfile)
class PlantProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'optimal_moisture_range', 'watering_frequency_days']
    list_filter = ['category']
    search_fields = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'description')
        }),
        ('Moisture Requirements', {
            'fields': ('optimal_moisture_min', 'optimal_moisture_max', 
                      'critical_low_moisture', 'critical_high_moisture')
        }),
        ('Care Schedule', {
            'fields': ('watering_frequency_days', 'growth_season_start', 'growth_season_end')
        }),
    )
    
    def optimal_moisture_range(self, obj):
        return f"{obj.optimal_moisture_min}% - {obj.optimal_moisture_max}%"
    optimal_moisture_range.short_description = 'Optimal Range'

@admin.register(SensorPlantAssignment)
class SensorPlantAssignmentAdmin(admin.ModelAdmin):
    list_display = ['sensor', 'plant_profile', 'assigned_date', 'is_active']
    list_filter = ['is_active', 'assigned_date', 'plant_profile__category']
    search_fields = ['sensor__name', 'plant_profile__name']
    readonly_fields = ['assigned_date']


class AIInsightAdmin(admin.ModelAdmin):
    list_display = ['title', 'sensor', 'insight_type', 'priority', 'confidence_score', 
                   'is_read', 'is_dismissed', 'created_at']
    list_filter = ['insight_type', 'priority', 'is_read', 'is_dismissed', 'created_at']
    search_fields = ['title', 'description', 'sensor__name']
    readonly_fields = ['created_at', 'confidence_score', 'data_analyzed']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Insight Information', {
            'fields': ('sensor', 'insight_type', 'priority', 'title', 'description', 'recommendation')
        }),
        ('AI Analysis', {
            'fields': ('confidence_score', 'data_analyzed'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_read', 'is_dismissed', 'created_at', 'expires_at')
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_dismissed', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} insights marked as read.')
    mark_as_read.short_description = 'Mark selected insights as read'
    
    def mark_as_dismissed(self, request, queryset):
        updated = queryset.update(is_dismissed=True)
        self.message_user(request, f'{updated} insights dismissed.')
    mark_as_dismissed.short_description = 'Dismiss selected insights'
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} insights marked as unread.')
    mark_as_unread.short_description = 'Mark selected insights as unread'

@admin.register(WeatherData)
class WeatherDataAdmin(admin.ModelAdmin):
    list_display = ['location', 'timestamp', 'temperature_celsius', 'humidity_percentage', 
                   'precipitation_mm']
    list_filter = ['location', 'timestamp']
    search_fields = ['location']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    def get_queryset(self, request):
        # Limit to recent weather data for performance
        qs = super().get_queryset(request)
        return qs.filter(timestamp__gte=timezone.now() - timedelta(days=7))

@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    list_display = ['user', 'enable_ai_insights', 'insight_frequency', 'timezone']
    list_filter = ['enable_ai_insights', 'insight_frequency']
    search_fields = ['user__username', 'user__email']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('AI Settings', {
            'fields': ('enable_ai_insights', 'insight_frequency', 'notification_types')
        }),
        ('Localization', {
            'fields': ('timezone',)
        }),
    )

# Custom admin views for insights analytics
class InsightsAnalyticsAdmin(admin.ModelAdmin):
    """Custom admin view for insights analytics"""
    change_list_template ='predictions/ai_insights_dashboard.html'
    
    def changelist_view(self, request, extra_context=None):
        # Calculate analytics data
        response = super().changelist_view(request, extra_context=extra_context)
        
        try:
            qs = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response
        
        # Insights by type
        insights_by_type = {}
        for insight_type, display_name in AIInsight.INSIGHT_TYPES:
            count = qs.filter(insight_type=insight_type).count()
            if count > 0:
                insights_by_type[display_name] = count
        
        # Insights by priority
        insights_by_priority = {}
        for priority, display_name in AIInsight.PRIORITY_LEVELS:
            count = qs.filter(priority=priority).count()
            if count > 0:
                insights_by_priority[display_name] = count
        
        # Recent activity
        recent_insights = qs.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        # Average confidence
        confidences = [i.confidence_score for i in qs if i.confidence_score]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        extra_context = extra_context or {}
        extra_context.update({
            'insights_by_type': insights_by_type,
            'insights_by_priority': insights_by_priority,
            'recent_insights_count': recent_insights,
            'average_confidence': round(avg_confidence, 2),
            'total_insights': qs.count(),
        })
        
        response.context_data.update(extra_context)
        return response

# Register the analytics view
admin.site.register(AIInsight, InsightsAnalyticsAdmin)