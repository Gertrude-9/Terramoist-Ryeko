from django.utils import timezone
from datetime import timedelta
from .models import Sensor, SensorReading, WeatherData, IrrigationLog
import logging

logger = logging.getLogger(__name__)

class IrrigationService:
    @staticmethod
    def check_irrigation_needs():
        """Check all fields and determine if irrigation is needed"""
        from .models import Field
        
        for field in Field.objects.all():
            # Get latest weather data
            weather = WeatherData.objects.filter(field=field).order_by('-timestamp').first()
            
            # Skip if raining
            if weather and weather.rainfall > 5:  # More than 5mm rain
                IrrigationService.log_irrigation(
                    field,
                    'skipped',
                    f"Skipped due to rainfall: {weather.rainfall}mm"
                )
                continue
            
            # Get latest sensor readings
            moisture_readings = SensorReading.objects.filter(
                sensor__field=field,
                sensor__sensor_type='soil_moisture'
            ).order_by('-timestamp')[:3]
            
            temp_readings = SensorReading.objects.filter(
                sensor__field=field,
                sensor__sensor_type='temperature'
            ).order_by('-timestamp')[:3]
            
            if not moisture_readings or not temp_readings:
                continue
            
            avg_moisture = sum(r.value for r in moisture_readings) / len(moisture_readings)
            avg_temp = sum(r.value for r in temp_readings) / len(temp_readings)
            
            # Decision logic
            irrigation_needed = False
            reason = ""
            
            if avg_moisture < 40:
                irrigation_needed = True
                reason = f"Soil moisture too low: {avg_moisture:.1f}%"
            elif avg_moisture < 50 and avg_temp > 30:
                irrigation_needed = True
                reason = f"Moderate moisture ({avg_moisture:.1f}%) but high temperature ({avg_temp:.1f}°C)"
            elif weather and weather.humidity < 40 and avg_moisture < 55:
                irrigation_needed = True
                reason = f"Low humidity ({weather.humidity:.1f}%) and moderate moisture ({avg_moisture:.1f}%)"
            
            if irrigation_needed:
                IrrigationService.start_irrigation(field, 30, reason)  # Default 30 min irrigation
            else:
                IrrigationService.log_irrigation(
                    field,
                    'skipped',
                    f"No irrigation needed. Moisture: {avg_moisture:.1f}%, Temp: {avg_temp:.1f}°C"
                )
    
    @staticmethod
    def start_irrigation(field, duration_minutes, reason=""):
        """Start an irrigation session"""
        # Check if already running
        if IrrigationLog.objects.filter(field=field, status='running').exists():
            return False
        
        # Calculate estimated water usage (assuming 10L/min flow rate)
        water_estimate = duration_minutes * 10
        
        log = IrrigationLog.objects.create(
            field=field,
            start_time=timezone.now(),
            duration=duration_minutes,
            water_used=water_estimate,
            status='running',
            reason=reason
        )
        
        # Here you would add actual hardware control logic
        logger.info(f"Starting irrigation for {field.name}: {reason}")
        
        return log
    
    @staticmethod
    def log_irrigation(field, status, reason=""):
        """Log irrigation activity"""
        return IrrigationLog.objects.create(
            field=field,
            start_time=timezone.now(),
            status=status,
            reason=reason
        )
    
    @staticmethod
    def check_scheduled_irrigation():
        """Check and execute scheduled irrigation if conditions are right"""
        from .models import IrrigationSchedule
        
        now = timezone.now()
        current_time = now.time()
        
        for schedule in IrrigationSchedule.objects.filter(is_active=True):
            # Check if it's time to run (within 5 minutes of scheduled time)
            time_diff = abs((current_time.hour * 60 + current_time.minute) - 
                          (schedule.start_time.hour * 60 + schedule.start_time.minute))
            
            if time_diff > 5:
                continue
            
            # Check if already ran today
            if schedule.last_run and schedule.last_run.date() == now.date():
                continue
            
            # Get weather data
            weather = WeatherData.objects.filter(field=schedule.field).order_by('-timestamp').first()
            
            # Skip if raining
            if weather and weather.rainfall > 5:
                IrrigationService.log_irrigation(
                    schedule.field,
                    'skipped',
                    f"Scheduled irrigation skipped due to rainfall: {weather.rainfall}mm"
                )
                continue
            
            # Get soil moisture
            moisture_reading = SensorReading.objects.filter(
                sensor__field=schedule.field,
                sensor__sensor_type='soil_moisture'
            ).order_by('-timestamp').first()
            
            # Skip if soil moisture is adequate
            if moisture_reading and moisture_reading.value > 50:
                IrrigationService.log_irrigation(
                    schedule.field,
                    'skipped',
                    f"Scheduled irrigation skipped - soil moisture adequate: {moisture_reading.value}%"
                )
                continue
            
            # Start irrigation
            IrrigationService.start_irrigation(
                schedule.field,
                schedule.duration,
                "Scheduled irrigation"
            )
            
            # Update last run time
            schedule.last_run = now
            schedule.save()