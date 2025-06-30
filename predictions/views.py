# views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
import json

from requests import request

from .models import SoilSensor, AIInsight, SoilMoistureReading, UserPreferences
from .ai_insights import TerramostAIEngine
@login_required
def ai_insights_dashboard(request):
    """Main dashboard for AI insights"""
    user_sensors = SoilSensor.objects.filter(owner=request.user, is_active=True)
    sensor_id = request.GET.get('sensor_id')

    if not sensor_id:
        # Example: default to first sensor id if available
        if user_sensors.exists():
            sensor_id = user_sensors.first().id
        else:
            sensor_id = None  # Or handle no sensors case explicitly

    # Get recent insights
    recent_insights = AIInsight.objects.filter(
        sensor__owner=request.user,
        created_at__gte=timezone.now() - timedelta(days=7)
    ).select_related('sensor').order_by('-created_at')[:10]

    # Get insights by priority
    critical_insights = AIInsight.objects.filter(
        sensor__owner=request.user,
        priority='critical',
        is_dismissed=False
    ).count()

    high_insights = AIInsight.objects.filter(
        sensor__owner=request.user,
        priority='high',
        is_dismissed=False
    ).count()

    # Get insights by type
    insight_stats = AIInsight.objects.filter(
        sensor__owner=request.user,
        created_at__gte=timezone.now() - timedelta(days=30)
    ).values('insight_type').annotate(count=Count('id'))

    context = {
        'sensors': user_sensors,
        'recent_insights': recent_insights,
        'critical_count': critical_insights,
        'high_count': high_insights,
        'insight_stats': insight_stats,
        'sensor_id': sensor_id,  # include sensor_id in context here
    }

    return render(request, 'predictions/ai_insights_dashboard.html', context)

@login_required
def sensor_insights(request, sensor_id):
    """Get insights for a specific sensor"""
    sensor = get_object_or_404(SoilSensor, sensor_id=sensor_id, owner=request.user)
    
    # Filter insights
    insights_query = AIInsight.objects.filter(sensor=sensor)
    
    # Apply filters
    priority_filter = request.GET.get('priority')
    if priority_filter:
        insights_query = insights_query.filter(priority=priority_filter)
    
    type_filter = request.GET.get('type')
    if type_filter:
        insights_query = insights_query.filter(insight_type=type_filter)
    
    date_filter = request.GET.get('days', '7')
    try:
        days = int(date_filter)
        cutoff_date = timezone.now() - timedelta(days=days)
        insights_query = insights_query.filter(created_at__gte=cutoff_date)
    except ValueError:
        days = 7
    
    insights = insights_query.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(insights, 20)
    page = request.GET.get('page')
    insights_page = paginator.get_page(page)
    
    context = {
        'sensor': sensor,
        'sensor_id': sensor.sensor_id,   # ✅ add this line
        'insights': insights_page,
        'priority_filter': priority_filter,
        'type_filter': type_filter,
        'days': days,
    }
    
    return render(request, 'predictions/sensor_insights.html', context)

@login_required
@require_http_methods(["POST"])
def generate_insights_api(request, sensor_id):
    """API endpoint to manually trigger insight generation"""
    sensor = get_object_or_404(SoilSensor, sensor_id=sensor_id, owner=request.user)
    
    try:
        ai_engine = TerramostAIEngine()
        insights = ai_engine.generate_insights_for_sensor(sensor)
        ai_engine.save_insights_to_db(sensor, insights)
        
        return JsonResponse({
            'success': True,
            'message': f'Generated {len(insights)} new insights',
            'insights_count': len(insights)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["GET"])
def insights_api(request):
    """API endpoint to get insights data"""
    user_sensors = SoilSensor.objects.filter(owner=request.user, is_active=True)
    
    # Get query parameters
    sensor_id = request.GET.get('sensor_id')
    priority = request.GET.get('priority')
    insight_type = request.GET.get('type')
    days = int(request.GET.get('days', 7))
    limit = int(request.GET.get('limit', 50))
    
    # Build query
    insights_query = AIInsight.objects.filter(sensor__in=user_sensors)
    
    if sensor_id:
        insights_query = insights_query.filter(sensor__sensor_id=sensor_id)
    
    if priority:
        insights_query = insights_query.filter(priority=priority)
    
    if insight_type:
        insights_query = insights_query.filter(insight_type=insight_type)
    
    # Date filter
    cutoff_date = timezone.now() - timedelta(days=days)
    insights_query = insights_query.filter(created_at__gte=cutoff_date)
    
    insights = insights_query.select_related('sensor').order_by('-created_at')[:limit]
    
    # Format response
    insights_data = []
    for insight in insights:
        insights_data.append({
            'id': insight.id,
            'sensor_id': insight.sensor.sensor_id,
            'sensor_name': insight.sensor.name,
            'type': insight.insight_type,
            'priority': insight.priority,
            'title': insight.title,
            'description': insight.description,
            'recommendation': insight.recommendation,
            'confidence': insight.confidence_score,
            'created_at': insight.created_at.isoformat(),
            'is_read': insight.is_read,
            'is_dismissed': insight.is_dismissed,
        })
    
    return JsonResponse({
        'insights': insights_data,
        'total_count': insights_query.count()
    })

@login_required
@require_http_methods(["POST"])
def mark_insight_read(request, insight_id):
    """Mark an insight as read"""
    insight = get_object_or_404(AIInsight, id=insight_id, sensor__owner=request.user)
    insight.is_read = True
    insight.save()
    
    return JsonResponse({'success': True})

@login_required
@require_http_methods(["POST"])
def dismiss_insight(request, insight_id):
    """Dismiss an insight"""
    insight = get_object_or_404(AIInsight, id=insight_id, sensor__owner=request.user)
    insight.is_dismissed = True
    insight.save()
    
    return JsonResponse({'success': True})

@login_required
def moisture_trends_api(request, sensor_id):
    """API endpoint for moisture trend data"""
    sensor = get_object_or_404(SoilSensor, sensor_id=sensor_id, owner=request.user)
    
    # Get number of days from query parameter
    days = int(request.GET.get('days', 7))
    cutoff_date = timezone.now() - timedelta(days=days)
    
    # Get readings
    readings = SoilMoistureReading.objects.filter(
        sensor=sensor,
        timestamp__gte=cutoff_date
    ).order_by('timestamp')
    
    # Format data for charts
    chart_data = []
    for reading in readings:
        chart_data.append({
            'timestamp': reading.timestamp.isoformat(),
            'moisture': reading.moisture_percentage,
            'temperature': reading.temperature_celsius,
            'humidity': reading.humidity_percentage,
        })
    
    # Calculate trend statistics
    moisture_values = [r.moisture_percentage for r in readings]
    if len(moisture_values) > 1:
        avg_moisture = sum(moisture_values) / len(moisture_values)
        min_moisture = min(moisture_values)
        max_moisture = max(moisture_values)
        
        # Simple trend calculation
        recent_avg = sum(moisture_values[-5:]) / min(5, len(moisture_values))
        older_avg = sum(moisture_values[:5]) / min(5, len(moisture_values))
        trend_direction = "increasing" if recent_avg > older_avg else "decreasing"
    else:
        avg_moisture = moisture_values[0] if moisture_values else 0
        min_moisture = max_moisture = avg_moisture
        trend_direction = "stable"
    
    return JsonResponse({
        'chart_data': chart_data,
        'statistics': {
            'average_moisture': round(avg_moisture, 2),
            'min_moisture': round(min_moisture, 2),
            'max_moisture': round(max_moisture, 2),
            'trend_direction': trend_direction,
            'total_readings': len(chart_data)
        }
    })

@login_required
def ai_preferences(request):
    """User AI preferences page"""
    preferences, created = UserPreferences.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update preferences
        preferences.enable_ai_insights = request.POST.get('enable_ai_insights') == 'on'
        preferences.insight_frequency = request.POST.get('insight_frequency', 'daily')
        
        # Handle notification types
        notification_types = request.POST.getlist('notification_types')
        preferences.notification_types = notification_types
        
        preferences.timezone = request.POST.get('timezone', 'UTC')
        preferences.save()
        
        return JsonResponse({'success': True, 'message': 'Preferences updated successfully'})
    
    context = {
        'preferences': preferences,
        'insight_types': AIInsight.INSIGHT_TYPES,
        'frequency_choices': UserPreferences._meta.get_field('insight_frequency').choices,
    }
    
    return render(request, 'predictions/ai_preferences.html', context)

@login_required
def insight_detail_api(request, insight_id):
    """Get detailed information about a specific insight"""
    insight = get_object_or_404(AIInsight, id=insight_id, sensor__owner=request.user)
    
    # Get recent readings for context
    recent_readings = SoilMoistureReading.objects.filter(
        sensor=insight.sensor,
        timestamp__gte=timezone.now() - timedelta(days=3)
    ).order_by('-timestamp')[:20]
    
    readings_data = []
    for reading in recent_readings:
        readings_data.append({
            'timestamp': reading.timestamp.isoformat(),
            'moisture': reading.moisture_percentage,
            'temperature': reading.temperature_celsius,
        })
    
    return JsonResponse({
        'insight': {
            'id': insight.id,
            'type': insight.insight_type,
            'priority': insight.priority,
            'title': insight.title,
            'description': insight.description,
            'recommendation': insight.recommendation,
            'confidence': insight.confidence_score,
            'created_at': insight.created_at.isoformat(),
            'data_analyzed': insight.data_analyzed,
        },
        'sensor': {
            'id': insight.sensor.sensor_id,
            'name': insight.sensor.name,
            'location': insight.sensor.location,
        },
        'recent_readings': readings_data
    })

@login_required
def insights_summary_api(request):
    """Get summary statistics for insights"""
    user_sensors = SoilSensor.objects.filter(owner=request.user, is_active=True)
    
    # Get time period
    days = int(request.GET.get('days', 30))
    cutoff_date = timezone.now() - timedelta(days=days)
    
    # Get insights in time period
    insights = AIInsight.objects.filter(
        sensor__in=user_sensors,
        created_at__gte=cutoff_date
    )
    
    # Calculate statistics
    total_insights = insights.count()
    unread_insights = insights.filter(is_read=False).count()
    critical_insights = insights.filter(priority='critical').count()
    high_priority_insights = insights.filter(priority='high').count()
    
    # Insights by type
    insights_by_type = {}
    for insight_type, display_name in AIInsight.INSIGHT_TYPES:
        count = insights.filter(insight_type=insight_type).count()
        if count > 0:
            insights_by_type[display_name] = count
    
    # Insights by sensor
    insights_by_sensor = {}
    for sensor in user_sensors:
        count = insights.filter(sensor=sensor).count()
        if count > 0:
            insights_by_sensor[sensor.name] = count
    
    # Average confidence score
    confidence_scores = [i.confidence_score for i in insights if i.confidence_score]
    avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
    
    return JsonResponse({
        'summary': {
            'total_insights': total_insights,
            'unread_insights': unread_insights,
            'critical_insights': critical_insights,
            'high_priority_insights': high_priority_insights,
            'average_confidence': round(avg_confidence, 2),
        },
        'insights_by_type': insights_by_type,
        'insights_by_sensor': insights_by_sensor,
        'time_period_days': days
    })

# Utility functions for templates
def get_priority_badge_class(priority):
    """Get CSS class for priority badge"""
    priority_classes = {
        'critical': 'badge-danger',
        'high': 'badge-warning',
        'medium': 'badge-info',
        'low': 'badge-secondary',
    }
    return priority_classes.get(priority, 'badge-secondary')

def get_insight_type_icon(insight_type):
    """Get icon for insight type"""
    type_icons = {
        'watering_recommendation': 'fas fa-tint',
        'moisture_trend': 'fas fa-chart-line',
        'plant_health': 'fas fa-leaf',
        'seasonal_pattern': 'fas fa-calendar-alt',
        'anomaly_detection': 'fas fa-exclamation-triangle',
        'optimization': 'fas fa-cogs',
        'alert': 'fas fa-bell',
    }
    return type_icons.get(insight_type, 'fas fa-info-circle')