
#from .models import Field
from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import os

class Field(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    location = models.CharField(max_length=200)
    size_hectares = models.FloatField()
    crop_type = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.crop_type}"

class SensorData(models.Model):
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='sensor_data')
    soil_moisture = models.FloatField(help_text="Soil moisture percentage (0-100)")
    temperature = models.FloatField(help_text="Temperature in Celsius")
    humidity = models.FloatField(help_text="Humidity percentage (0-100)")
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.field.name} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

class IrrigationPrediction(models.Model):
    RECOMMENDATION_CHOICES = [
        ('IRRIGATE', 'Irrigate Now'),
        ('WAIT', 'Wait'),
        ('MONITOR', 'Monitor Closely'),
    ]
    
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='predictions')
    sensor_data = models.ForeignKey(SensorData, on_delete=models.CASCADE)
    recommendation = models.CharField(max_length=10, choices=RECOMMENDATION_CHOICES)
    confidence_score = models.FloatField(help_text="Confidence score (0-1)")
    reasoning = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

class AIInsightsManager:
    """Manager class for AI insights and predictions"""
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.load_or_create_model()
    
    def load_or_create_model(self):
        """Load existing model or create a new one"""
        try:
            self.model = joblib.load('irrigation_model.pkl')
            self.scaler = joblib.load('irrigation_scaler.pkl')
        except FileNotFoundError:
            self.create_initial_model()
    
    def create_initial_model(self):
        """Create initial model with sample data"""
        # Sample training data based on agricultural best practices
        training_data = np.array([
            [15, 35, 40],  # Low moisture, high temp, low humidity -> IRRIGATE
            [45, 25, 60],  # Good moisture, moderate temp, good humidity -> WAIT
            [25, 30, 45],  # Moderate moisture, moderate temp, moderate humidity -> MONITOR
            [10, 40, 35],  # Very low moisture, high temp, low humidity -> IRRIGATE
            [60, 20, 70],  # High moisture, low temp, high humidity -> WAIT
            [35, 28, 55],  # Good moisture, optimal temp, good humidity -> WAIT
            [20, 38, 30],  # Low moisture, high temp, very low humidity -> IRRIGATE
            [50, 22, 65],  # High moisture, low temp, high humidity -> WAIT
            [30, 32, 50],  # Moderate moisture, moderate temp, moderate humidity -> MONITOR
            [12, 42, 25],  # Very low moisture, very high temp, very low humidity -> IRRIGATE
        ])
        
        # Labels: 0=WAIT, 1=MONITOR, 2=IRRIGATE
        labels = np.array([2, 0, 1, 2, 0, 0, 2, 0, 1, 2])
        
        self.scaler = StandardScaler()
        scaled_data = self.scaler.fit_transform(training_data)
        
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(scaled_data, labels)
        
        # Save the model
        joblib.dump(self.model, 'irrigation_model.pkl')
        joblib.dump(self.scaler, 'irrigation_scaler.pkl')
    
    def get_irrigation_recommendation(self, soil_moisture, temperature, humidity):
        """Get irrigation recommendation based on sensor data"""
        # Prepare input data
        input_data = np.array([[soil_moisture, temperature, humidity]])
        scaled_input = self.scaler.transform(input_data)
        
        # Make prediction
        prediction = self.model.predict(scaled_input)[0]
        confidence = np.max(self.model.predict_proba(scaled_input))
        
        # Map prediction to recommendation
        recommendation_map = {0: 'WAIT', 1: 'MONITOR', 2: 'IRRIGATE'}
        recommendation = recommendation_map[prediction]
        
        # Generate reasoning
        reasoning = self.generate_reasoning(soil_moisture, temperature, humidity, recommendation)
        
        return {
            'recommendation': recommendation,
            'confidence_score': confidence,
            'reasoning': reasoning
        }
    
    def generate_reasoning(self, soil_moisture, temperature, humidity, recommendation):
        """Generate human-readable reasoning for the recommendation"""
        reasoning_parts = []
        
        # Soil moisture analysis
        if soil_moisture < 20:
            reasoning_parts.append("Soil moisture is critically low")
        elif soil_moisture < 35:
            reasoning_parts.append("Soil moisture is below optimal levels")
        elif soil_moisture > 60:
            reasoning_parts.append("Soil moisture is adequately high")
        else:
            reasoning_parts.append("Soil moisture is at moderate levels")
        
        # Temperature analysis
        if temperature > 35:
            reasoning_parts.append("high temperature increases water stress")
        elif temperature < 15:
            reasoning_parts.append("low temperature reduces water demand")
        else:
            reasoning_parts.append("temperature is within normal range")
        
        # Humidity analysis
        if humidity < 40:
            reasoning_parts.append("low humidity increases evaporation")
        elif humidity > 70:
            reasoning_parts.append("high humidity reduces water loss")
        else:
            reasoning_parts.append("humidity is at moderate levels")
        
        # Combine reasoning
        base_reasoning = ". ".join(reasoning_parts).capitalize()
        
        if recommendation == 'IRRIGATE':
            return f"{base_reasoning}. Immediate irrigation is recommended to prevent crop stress."
        elif recommendation == 'MONITOR':
            return f"{base_reasoning}. Continue monitoring; irrigation may be needed soon."
        else:
            return f"{base_reasoning}. Current conditions are adequate; irrigation can be delayed."
    
    def get_insights_by_type(self, field_id, insight_type='all', days=7):
        """Get insights filtered by type for the last N days"""
        from datetime import timedelta
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        sensor_data = SensorData.objects.filter(
            field_id=field_id,
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).order_by('-timestamp')
        
        insights = {
            'soil_moisture': [],
            'temperature': [],
            'humidity': [],
            'predictions': []
        }
        
        for data in sensor_data:
            prediction = self.get_irrigation_recommendation(
                data.soil_moisture, data.temperature, data.humidity
            )
            
            if insight_type == 'all' or insight_type == 'soil_moisture':
                insights['soil_moisture'].append({
                    'timestamp': data.timestamp,
                    'value': data.soil_moisture,
                    'status': 'critical' if data.soil_moisture < 20 else 'low' if data.soil_moisture < 35 else 'good'
                })
            
            if insight_type == 'all' or insight_type == 'temperature':
                insights['temperature'].append({
                    'timestamp': data.timestamp,
                    'value': data.temperature,
                    'status': 'high' if data.temperature > 35 else 'low' if data.temperature < 15 else 'normal'
                })
            
            if insight_type == 'all' or insight_type == 'humidity':
                insights['humidity'].append({
                    'timestamp': data.timestamp,
                    'value': data.humidity,
                    'status': 'low' if data.humidity < 40 else 'high' if data.humidity > 70 else 'normal'
                })
            
            insights['predictions'].append({
                'timestamp': data.timestamp,
                'recommendation': prediction['recommendation'],
                'confidence': prediction['confidence_score'],
                'reasoning': prediction['reasoning']
            })
        
        return insights