# tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import SoilSensor, AIInsight, UserPreferences
from .ai_insights import TerramostAIEngine
import logging

logger = logging.getLogger(__name__)

@shared_task
def run_ai_analysis_for_all_sensors():
    """
    Scheduled task to run AI analysis for all active sensors
    This should be run periodically (e.g., every hour or daily)
    """
    ai_engine = TerramostAIEngine()
    active_sensors = SoilSensor.objects.filter(is_active=True)
    
    total_insights = 0
    processed_sensors = 0
    errors = 0
    
    for sensor in active_sensors:
        try:
            insights = ai_engine.generate_insights_for_sensor(sensor)
            ai_engine.save_insights_to_db(sensor, insights)
            total_insights += len(insights)
            processed_sensors += 1
            
            logger.info(f"Generated {len(insights)} insights for sensor {sensor.sensor_id}")
            
        except Exception as e:
            errors += 1
            logger.error(f"Error analyzing sensor {sensor.sensor_id}: {str(e)}")
    
    logger.info(f"AI analysis completed: {processed_sensors} sensors processed, "
               f"{total_insights} insights generated, {errors} errors")
    
    return {
        'processed_sensors': processed_sensors,
        'total_insights': total_insights,
        'errors': errors
    }

@shared_task
def run_ai_analysis_for_sensor(sensor_id):
    """
    Task to run AI analysis for a specific sensor
    """
    try:
        sensor = SoilSensor.objects.get(sensor_id=sensor_id, is_active=True)
        ai_engine = TerramostAIEngine()
        
        insights = ai_engine.generate_insights_for_sensor(sensor)
        ai_engine.save_insights_to_db(sensor, insights)
        
        logger.info(f"Generated {len(insights)} insights for sensor {sensor_id}")
        
        return {
            'sensor_id': sensor_id,
            'insights_generated': len(insights)
        }
        
    except SoilSensor.DoesNotExist:
        logger.error(f"Sensor {sensor_id} not found or inactive")
        return {'error': f'Sensor {sensor_id} not found or inactive'}
    
    except Exception as e:
        logger.error(f"Error analyzing sensor {sensor_id}: {str(e)}")
        return {'error': str(e)}

@shared_task
def send_insights_notifications():
    """
    Send email notifications for critical and high-priority insights
    """
    # Get users who want notifications
    users_with_notifications = UserPreferences.objects.filter(
        enable_ai_insights=True
    ).select_related('user')
    
    notifications_sent = 0
    
    for user_pref in users_with_notifications:
        user = user_pref.user
        
        # Get user's sensors
        user_sensors = SoilSensor.objects.filter(owner=user, is_active=True)
        
        # Get unread critical and high priority insights from last 24 hours
        recent_insights = AIInsight.objects.filter(
            sensor__in=user_sensors,
            priority__in=['critical', 'high'],
            is_read=False,
            is_dismissed=False,
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).select_related('sensor')
        
        if recent_insights.exists():
            try:
                # Send notification email
                send_insight_notification_email(user, recent_insights)
                notifications_sent += 1
                logger.info(f"Sent insights notification to {user.email}")
                
            except Exception as e:
                logger.error(f"Failed to send notification to {user.email}: {str(e)}")
    
    return {'notifications_sent': notifications_sent}

def send_insight_notification_email(user, insights):
    """
    Send email notification for insights
    """
    critical_insights = [i for i in insights if i.priority == 'critical']
    high_insights = [i for i in insights if i.priority == 'high']
    
    context = {
        'user': user,
        'critical_insights': critical_insights,
        'high_insights': high_insights,
        'total_insights': len(insights),
    }
    
    subject = f"Terramoist Alert: {len(critical_insights)} Critical Insights"
    if len(critical_insights) == 0:
        subject = f"Terramoist: {len(high_insights)} High Priority Insights"
    
    html_message = render_to_string('emails/insights_notification.html', context)
    text_message = render_to_string('emails/insights_notification.txt', context)
    
    send_mail(
        subject=subject,
        message=text_message,
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )

@shared_task
def cleanup_old_insights():
    """
    Clean up old insights that are no longer relevant
    """
    # Delete expired insights
    expired_insights = AIInsight.objects.filter(
        expires_at__lt=timezone.now()
    )
    expired_count = expired_insights.count()
    expired_insights.delete()
    
    # Delete very old dismissed insights (older than 30 days)
    old_dismissed = AIInsight.objects.filter(
        is_dismissed=True,
        created_at__lt=timezone.now() - timedelta(days=30)
    )
    old_dismissed_count = old_dismissed.count()
    old_dismissed.delete()
    
    # Delete old low-priority insights (older than 7 days)
    old_low_priority = AIInsight.objects.filter(
        priority='low',
        created_at__lt=timezone.now() - timedelta(days=7)
    )
    old_low_count = old_low_priority.count()
    old_low_priority.delete()
    
    logger.info(f"Cleaned up insights: {expired_count} expired, "
               f"{old_dismissed_count} old dismissed, {old_low_count} old low-priority")
    
    return {
        'expired_insights': expired_count,
        'old_dismissed': old_dismissed_count,
        'old_low_priority': old_low_count
    }

@shared_task
def generate_insights_report(user_id, days=30):
    """
    Generate a comprehensive insights report for a user
    """
    from django.contrib.auth.models import User
    
    try:
        user = User.objects.get(id=user_id)
        user_sensors = SoilSensor.objects.filter(owner=user, is_active=True)
        
        cutoff_date = timezone.now() - timedelta(days=days)
        insights = AIInsight.objects.filter(
            sensor__in=user_sensors,
            created_at__gte=cutoff_date
        ).select_related('sensor')
        
        # Generate report data
        report_data = {
            'user': user.username,
            'period_days': days,
            'total_insights': insights.count(),
            'sensors_analyzed': user_sensors.count(),
            'insights_by_type': {},
            'insights_by_priority': {},
            'sensors_with_issues': [],
            'recommendations': []
        }
        
        # Insights by type
        for insight_type, display_name in AIInsight.INSIGHT_TYPES:
            count = insights.filter(insight_type=insight_type).count()
            if count > 0:
                report_data['insights_by_type'][display_name] = count
        
        # Insights by priority
        for priority, display_name in AIInsight.PRIORITY_LEVELS:
            count = insights.filter(priority=priority).count()
            if count > 0:
                report_data['insights_by_priority'][display_name] = count
        
        # Sensors with critical issues
        critical_sensors = insights.filter(priority='critical').values_list('sensor__name', flat=True).distinct()
        report_data['sensors_with_issues'] = list(critical_sensors)
        
        # Top recommendations
        top_recommendations = insights.filter(
            priority__in=['critical', 'high']
        ).values_list('recommendation', flat=True)[:5]
        report_data['recommendations'] = list(top_recommendations)
        
        logger.info(f"Generated insights report for user {user.username}")
        return report_data
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return {'error': f'User {user_id} not found'}
    
    except Exception as e:
        logger.error(f"Error generating report for user {user_id}: {str(e)}")
        return {'error': str(e)}

# Periodic task configuration (add to your celery beat schedule)
"""
Example celery beat configuration in settings.py:

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'run-ai-analysis': {
        'task': 'terramoist.tasks.run_ai_analysis_for_all_sensors',
        'schedule': crontab(minute=0),  # Run every hour
    },
    'send-insights-notifications': {
        'task': 'terramoist.tasks.send_insights_notifications',
        'schedule': crontab(hour=8, minute=0),  # Run daily at 8 AM
    },
    'cleanup-old-insights': {
        'task': 'terramoist.tasks.cleanup_old_insights',
        'schedule': crontab(hour=2, minute=0),  # Run daily at 2 AM
    },
}
"""