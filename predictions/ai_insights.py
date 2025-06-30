# ai_insights.py
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Avg, Min, Max, Count
from typing import List, Dict, Tuple, Optional
import statistics
from .models import (
    SoilMoistureReading, SoilSensor, AIInsight, 
    PlantProfile, SensorPlantAssignment, WeatherData
)

class TerramostAIEngine:
    """AI Engine for generating soil moisture insights"""
    
    def __init__(self):
        self.confidence_threshold = 0.7
        self.trend_analysis_days = 7
        self.seasonal_analysis_days = 30
    
    def generate_insights_for_sensor(self, sensor: SoilSensor) -> List[Dict]:
        """Generate all types of insights for a specific sensor"""
        insights = []
        
        # Get recent readings
        recent_readings = self.get_recent_readings(sensor, days=7)
        if not recent_readings:
            return insights
        
        # Get plant profile if assigned
        plant_assignment = SensorPlantAssignment.objects.filter(
            sensor=sensor, is_active=True
        ).first()
        
        # Generate different types of insights
        insights.extend(self.analyze_watering_needs(sensor, recent_readings, plant_assignment))
        insights.extend(self.analyze_moisture_trends(sensor, recent_readings))
        insights.extend(self.detect_anomalies(sensor, recent_readings))
        insights.extend(self.analyze_plant_health(sensor, recent_readings, plant_assignment))
        insights.extend(self.analyze_weather_impact(sensor, recent_readings))
        
        return insights
    
    def get_recent_readings(self, sensor: SoilSensor, days: int = 7) -> List[SoilMoistureReading]:
        """Get recent readings for a sensor"""
        cutoff_date = timezone.now() - timedelta(days=days)
        return list(sensor.readings.filter(timestamp__gte=cutoff_date).order_by('timestamp'))
    
    def analyze_watering_needs(self, sensor: SoilSensor, readings: List, 
                             plant_assignment: Optional[SensorPlantAssignment]) -> List[Dict]:
        """Analyze watering needs based on current moisture levels"""
        insights = []
        
        if not readings:
            return insights
            
        latest_reading = readings[-1]
        current_moisture = latest_reading.moisture_percentage
        
        # Default thresholds if no plant profile
        low_threshold = 30
        high_threshold = 80
        optimal_min = 40
        optimal_max = 70
        
        if plant_assignment and plant_assignment.plant_profile:
            plant = plant_assignment.plant_profile
            low_threshold = plant.critical_low_moisture
            high_threshold = plant.critical_high_moisture
            optimal_min = plant.optimal_moisture_min
            optimal_max = plant.optimal_moisture_max
        
        # Critical low moisture
        if current_moisture <= low_threshold:
            insights.append({
                'type': 'watering_recommendation',
                'priority': 'critical',
                'title': 'Immediate Watering Required',
                'description': f'Soil moisture is critically low at {current_moisture:.1f}%. '
                             f'Plants may be stressed and require immediate watering.',
                'recommendation': 'Water immediately and monitor closely over the next 24 hours.',
                'confidence': 0.95,
                'data': {'current_moisture': current_moisture, 'threshold': low_threshold}
            })
        
        # Low moisture warning
        elif current_moisture <= optimal_min:
            insights.append({
                'type': 'watering_recommendation',
                'priority': 'high',
                'title': 'Watering Recommended',
                'description': f'Soil moisture is below optimal range at {current_moisture:.1f}%. '
                             f'Consider watering soon to maintain plant health.',
                'recommendation': 'Water within the next 6-12 hours for best results.',
                'confidence': 0.85,
                'data': {'current_moisture': current_moisture, 'optimal_min': optimal_min}
            })
        
        # High moisture warning
        elif current_moisture >= high_threshold:
            insights.append({
                'type': 'watering_recommendation',
                'priority': 'medium',
                'title': 'Overwatering Risk',
                'description': f'Soil moisture is very high at {current_moisture:.1f}%. '
                             f'This may lead to root rot or other plant health issues.',
                'recommendation': 'Avoid watering and ensure proper drainage. Monitor for signs of overwatering.',
                'confidence': 0.80,
                'data': {'current_moisture': current_moisture, 'threshold': high_threshold}
            })
        
        return insights
    
    def analyze_moisture_trends(self, sensor: SoilSensor, readings: List) -> List[Dict]:
        """Analyze moisture trends over time"""
        insights = []
        
        if len(readings) < 10:  # Need sufficient data for trend analysis
            return insights
        
        # Calculate trend
        moisture_values = [r.moisture_percentage for r in readings]
        timestamps = [r.timestamp.timestamp() for r in readings]
        
        # Simple linear regression for trend
        correlation = np.corrcoef(timestamps, moisture_values)[0, 1]
        slope = np.polyfit(timestamps, moisture_values, 1)[0]
        
        # Convert slope to percentage change per day
        slope_per_day = slope * 86400  # seconds in a day
        
        confidence = abs(correlation) if abs(correlation) > 0.3 else 0.3
        
        if abs(slope_per_day) > 5:  # Significant trend
            if slope_per_day > 0:
                insights.append({
                    'type': 'moisture_trend',
                    'priority': 'medium',
                    'title': 'Moisture Increasing Trend',
                    'description': f'Soil moisture has been increasing by {slope_per_day:.1f}% per day. '
                                 f'This could indicate overwatering or increased rainfall.',
                    'recommendation': 'Monitor watering schedule and check for proper drainage.',
                    'confidence': confidence,
                    'data': {'slope_per_day': slope_per_day, 'correlation': correlation}
                })
            else:
                insights.append({
                    'type': 'moisture_trend',
                    'priority': 'medium',
                    'title': 'Moisture Decreasing Trend',
                    'description': f'Soil moisture has been decreasing by {abs(slope_per_day):.1f}% per day. '
                                 f'This may indicate insufficient watering or hot weather.',
                    'recommendation': 'Consider increasing watering frequency or adjusting irrigation schedule.',
                    'confidence': confidence,
                    'data': {'slope_per_day': slope_per_day, 'correlation': correlation}
                })
        
        return insights
    
    def detect_anomalies(self, sensor: SoilSensor, readings: List) -> List[Dict]:
        """Detect anomalous readings that might indicate sensor issues"""
        insights = []
        
        if len(readings) < 20:
            return insights
        
        moisture_values = [r.moisture_percentage for r in readings]
        
        # Calculate statistics
        mean_moisture = statistics.mean(moisture_values)
        std_moisture = statistics.stdev(moisture_values) if len(moisture_values) > 1 else 0
        
        # Check for outliers (values beyond 2 standard deviations)
        outliers = []
        for reading in readings[-10:]:  # Check last 10 readings
            z_score = abs(reading.moisture_percentage - mean_moisture) / std_moisture if std_moisture > 0 else 0
            if z_score > 2:
                outliers.append(reading)
        
        if outliers:
            insights.append({
                'type': 'anomaly_detection',
                'priority': 'medium',
                'title': 'Unusual Moisture Readings Detected',
                'description': f'Detected {len(outliers)} unusual readings that deviate significantly '
                             f'from the normal pattern. This might indicate sensor malfunction.',
                'recommendation': 'Check sensor calibration and physical condition. '
                               'Consider recalibrating or replacing if issues persist.',
                'confidence': 0.75,
                'data': {'outlier_count': len(outliers), 'mean_moisture': mean_moisture}
            })
        
        # Check for stuck readings (same value repeatedly)
        recent_values = moisture_values[-5:]
        if len(set(recent_values)) == 1 and len(recent_values) >= 3:
            insights.append({
                'type': 'anomaly_detection',
                'priority': 'high',
                'title': 'Sensor May Be Stuck',
                'description': f'Sensor has been reporting the same value ({recent_values[0]:.1f}%) '
                             f'for multiple consecutive readings.',
                'recommendation': 'Check sensor connection and physical condition. '
                               'Sensor may need cleaning or replacement.',
                'confidence': 0.90,
                'data': {'stuck_value': recent_values[0], 'duration': len(recent_values)}
            })
        
        return insights
    
    def analyze_plant_health(self, sensor: SoilSensor, readings: List, 
                           plant_assignment: Optional[SensorPlantAssignment]) -> List[Dict]:
        """Analyze plant health based on moisture patterns"""
        insights = []
        
        if not plant_assignment or not plant_assignment.plant_profile:
            return insights
        
        plant = plant_assignment.plant_profile
        
        # Check how long moisture has been outside optimal range
        optimal_min = plant.optimal_moisture_min
        optimal_max = plant.optimal_moisture_max
        
        out_of_range_count = 0
        for reading in readings[-24:]:  # Last 24 readings
            if reading.moisture_percentage < optimal_min or reading.moisture_percentage > optimal_max:
                out_of_range_count += 1
        
        if out_of_range_count > 12:  # More than half the readings
            insights.append({
                'type': 'plant_health',
                'priority': 'high',
                'title': 'Plant Health Concern',
                'description': f'Soil moisture has been outside the optimal range for {plant.name} '
                             f'for {out_of_range_count} out of the last 24 readings.',
                'recommendation': f'Adjust watering schedule to maintain moisture between '
                               f'{optimal_min}% and {optimal_max}% for optimal {plant.name} health.',
                'confidence': 0.85,
                'data': {
                    'out_of_range_count': out_of_range_count,
                    'optimal_range': [optimal_min, optimal_max]
                }
            })
        
        return insights
    
    def analyze_weather_impact(self, sensor: SoilSensor, readings: List) -> List[Dict]:
        """Analyze how weather affects soil moisture"""
        insights = []
        
        if not sensor.latitude or not sensor.longitude:
            return insights
        
        # Get recent weather data
        recent_weather = WeatherData.objects.filter(
            latitude=sensor.latitude,
            longitude=sensor.longitude,
            timestamp__gte=timezone.now() - timedelta(days=3)
        ).order_by('timestamp')
        
        if not recent_weather.exists():
            return insights
        
        # Check for recent precipitation
        total_precipitation = sum(w.precipitation_mm for w in recent_weather)
        
        if total_precipitation > 10:  # Significant rainfall
            insights.append({
                'type': 'optimization',
                'priority': 'low',
                'title': 'Recent Rainfall Detected',
                'description': f'Recent rainfall totaled {total_precipitation:.1f}mm. '
                             f'This may affect your watering schedule.',
                'recommendation': 'Consider reducing watering frequency for the next few days '
                               'to account for natural precipitation.',
                'confidence': 0.80,
                'data': {'precipitation_mm': total_precipitation}
            })
        
        return insights
    
    def save_insights_to_db(self, sensor: SoilSensor, insights: List[Dict]):
        """Save generated insights to the database"""
        for insight_data in insights:
            # Check if similar insight already exists
            existing = AIInsight.objects.filter(
                sensor=sensor,
                insight_type=insight_data['type'],
                title=insight_data['title'],
                created_at__gte=timezone.now() - timedelta(hours=24)
            ).first()
            
            if existing:
                # Update existing insight
                existing.confidence_score = insight_data['confidence']
                existing.data_analyzed = insight_data['data']
                existing.save()
            else:
                # Create new insight
                AIInsight.objects.create(
                    sensor=sensor,
                    insight_type=insight_data['type'],
                    priority=insight_data['priority'],
                    title=insight_data['title'],
                    description=insight_data['description'],
                    recommendation=insight_data['recommendation'],
                    confidence_score=insight_data['confidence'],
                    data_analyzed=insight_data['data']
                )

# Task function for scheduled AI analysis
def run_ai_analysis():
    """Run AI analysis for all active sensors"""
    ai_engine = TerramostAIEngine()
    
    active_sensors = SoilSensor.objects.filter(is_active=True)
    
    for sensor in active_sensors:
        try:
            insights = ai_engine.generate_insights_for_sensor(sensor)
            ai_engine.save_insights_to_db(sensor, insights)
        except Exception as e:
            print(f"Error analyzing sensor {sensor.sensor_id}: {str(e)}")
    
    print(f"AI analysis completed for {active_sensors.count()} sensors")