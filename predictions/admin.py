# admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Avg, Count, Max, Min
from django.utils import timezone
from datetime import timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO
import base64
from .models import Field, SensorData, IrrigationPrediction, AIInsightsManager

# Custom admin actions
def generate_prediction_for_latest_data(modeladmin, request, queryset):
    """Generate predictions for selected fields using their latest sensor data"""
    ai_manager = AIInsightsManager()
    count = 0
    
    for field in queryset:
        latest_data = SensorData.objects.filter(field=field).first()
        if latest_data:
            prediction = ai_manager.get_irrigation_recommendation(
                latest_data.soil_moisture,
                latest_data.temperature,
                latest_data.humidity
            )
            
            IrrigationPrediction.objects.create(
                field=field,
                sensor_data=latest_data,
                recommendation=prediction['recommendation'],
                confidence_score=prediction['confidence_score'],
                reasoning=prediction['reasoning']
            )
            count += 1
    
    modeladmin.message_user(request, f"Generated predictions for {count} fields.")

generate_prediction_for_latest_data.short_description = "Generate AI predictions for latest sensor data"

@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'crop_type', 'size_hectares', 'location', 'latest_sensor_data', 'latest_prediction', 'created_at')
    list_filter = ('crop_type', 'created_at', 'owner')
    search_fields = ('name', 'location', 'crop_type', 'owner__username')
    readonly_fields = ('created_at', 'sensor_data_summary', 'prediction_summary')
    actions = [generate_prediction_for_latest_data]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'owner', 'location', 'crop_type', 'size_hectares')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
        ('Analytics', {
            'fields': ('sensor_data_summary', 'prediction_summary'),
            'classes': ('collapse',)
        })
    )
    
    def latest_sensor_data(self, obj):
        """Show latest sensor reading timestamp"""
        latest = SensorData.objects.filter(field=obj).first()
        if latest:
            time_diff = timezone.now() - latest.timestamp
            if time_diff.days > 0:
                color = 'red'
                status = f"{time_diff.days} days ago"
            elif time_diff.seconds > 3600:
                color = 'orange'
                status = f"{time_diff.seconds // 3600} hours ago"
            else:
                color = 'green'
                status = "Recent"
            
            return format_html(
                '<span style="color: {};">{}</span>',
                color,
                status
            )
        return format_html('<span style="color: gray;">No data</span>')
    
    latest_sensor_data.short_description = "Latest Data"
    
    def latest_prediction(self, obj):
        """Show latest prediction"""
        latest = IrrigationPrediction.objects.filter(field=obj).first()
        if latest:
            colors = {
                'IRRIGATE': 'red',
                'MONITOR': 'orange',
                'WAIT': 'green'
            }
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>',
                colors.get(latest.recommendation, 'black'),
                latest.recommendation
            )
        return format_html('<span style="color: gray;">No prediction</span>')
    
    latest_prediction.short_description = "Latest Prediction"
    
    def sensor_data_summary(self, obj):
        """Show summary of sensor data"""
        if obj.pk:
            data = SensorData.objects.filter(field=obj)
            if data.exists():
                stats = data.aggregate(
                    count=Count('id'),
                    avg_moisture=Avg('soil_moisture'),
                    avg_temp=Avg('temperature'),
                    avg_humidity=Avg('humidity'),
                    latest=Max('timestamp')
                )
                
                return format_html(
                    """
                    <div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">
                        <strong>Sensor Data Summary:</strong><br>
                        📊 Total Readings: {count}<br>
                        💧 Avg Soil Moisture: {avg_moisture:.1f}%<br>
                        🌡️ Avg Temperature: {avg_temp:.1f}°C<br>
                        💨 Avg Humidity: {avg_humidity:.1f}%<br>
                        📅 Latest Reading: {latest}
                    </div>
                    """,
                    count=stats['count'],
                    avg_moisture=stats['avg_moisture'] or 0,
                    avg_temp=stats['avg_temp'] or 0,
                    avg_humidity=stats['avg_humidity'] or 0,
                    latest=stats['latest'].strftime('%Y-%m-%d %H:%M') if stats['latest'] else 'N/A'
                )
        return "Save field first to see summary"
    
    sensor_data_summary.short_description = "Sensor Data Summary"
    
    def prediction_summary(self, obj):
        """Show summary of predictions"""
        if obj.pk:
            predictions = IrrigationPrediction.objects.filter(field=obj)
            if predictions.exists():
                recent_predictions = predictions.filter(
                    created_at__gte=timezone.now() - timedelta(days=30)
                )
                
                recommendation_counts = {}
                for pred in recent_predictions:
                    recommendation_counts[pred.recommendation] = recommendation_counts.get(pred.recommendation, 0) + 1
                
                avg_confidence = predictions.aggregate(Avg('confidence_score'))['confidence_score__avg']
                
                return format_html(
                    """
                    <div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">
                        <strong>Predictions Summary (Last 30 days):</strong><br>
                        🔴 Irrigate: {irrigate}<br>
                        🟡 Monitor: {monitor}<br>
                        🟢 Wait: {wait}<br>
                        📈 Avg Confidence: {confidence:.2f}
                    </div>
                    """,
                    irrigate=recommendation_counts.get('IRRIGATE', 0),
                    monitor=recommendation_counts.get('MONITOR', 0),
                    wait=recommendation_counts.get('WAIT', 0),
                    confidence=avg_confidence or 0
                )
        return "Save field first to see summary"
    
    prediction_summary.short_description = "Prediction Summary"

@admin.register(SensorData)
class SensorDataAdmin(admin.ModelAdmin):
    list_display = ('field', 'soil_moisture_display', 'temperature_display', 'humidity_display', 'timestamp', 'data_quality')
    list_filter = ('field', 'timestamp', 'field__crop_type')
    search_fields = ('field__name',)
    readonly_fields = ('timestamp', 'data_visualization')
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Field Information', {
            'fields': ('field',)
        }),
        ('Sensor Readings', {
            'fields': ('soil_moisture', 'temperature', 'humidity', 'timestamp')
        }),
        ('Data Visualization', {
            'fields': ('data_visualization',),
            'classes': ('collapse',)
        })
    )
    
    def soil_moisture_display(self, obj):
        """Display soil moisture with color coding"""
        if obj.soil_moisture < 20:
            color = 'red'
            status = 'Critical'
        elif obj.soil_moisture < 35:
            color = 'orange'
            status = 'Low'
        elif obj.soil_moisture > 60:
            color = 'blue'
            status = 'High'
        else:
            color = 'green'
            status = 'Good'
        
        return format_html(
            '<span style="color: {};">{:.1f}% ({})</span>',
            color,
            obj.soil_moisture,
            status
        )
    
    soil_moisture_display.short_description = "Soil Moisture"
    
    def temperature_display(self, obj):
        """Display temperature with color coding"""
        if obj.temperature > 35:
            color = 'red'
            status = 'High'
        elif obj.temperature < 15:
            color = 'blue'
            status = 'Low'
        else:
            color = 'green'
            status = 'Normal'
        
        return format_html(
            '<span style="color: {};">{:.1f}°C ({})</span>',
            color,
            obj.temperature,
            status
        )
    
    temperature_display.short_description = "Temperature"
    
    def humidity_display(self, obj):
        """Display humidity with color coding"""
        if obj.humidity < 40:
            color = 'red'
            status = 'Low'
        elif obj.humidity > 70:
            color = 'blue'
            status = 'High'
        else:
            color = 'green'
            status = 'Normal'
        
        return format_html(
            '<span style="color: {};">{:.1f}% ({})</span>',
            color,
            obj.humidity,
            status
        )
    
    humidity_display.short_description = "Humidity"
    
    def data_quality(self, obj):
        """Assess data quality"""
        issues = []
        
        if obj.soil_moisture < 0 or obj.soil_moisture > 100:
            issues.append("Invalid moisture")
        if obj.temperature < -20 or obj.temperature > 60:
            issues.append("Invalid temperature")
        if obj.humidity < 0 or obj.humidity > 100:
            issues.append("Invalid humidity")
        
        if not issues:
            return format_html('<span style="color: green;">✓ Valid</span>')
        else:
            return format_html(
                '<span style="color: red;">⚠ {}</span>',
                ", ".join(issues)
            )
    
    data_quality.short_description = "Data Quality"
    
    def data_visualization(self, obj):
        """Generate a simple visualization of the data"""
        if obj.pk:
            # Get recent data for this field
            recent_data = SensorData.objects.filter(
                field=obj.field,
                timestamp__gte=timezone.now() - timedelta(days=7)
            ).order_by('timestamp')[:50]
            
            if recent_data.count() > 1:
                try:
                    # Create a simple plot
                    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 6))
                    
                    timestamps = [d.timestamp for d in recent_data]
                    moistures = [d.soil_moisture for d in recent_data]
                    temperatures = [d.temperature for d in recent_data]
                    humidities = [d.humidity for d in recent_data]
                    
                    ax1.plot(timestamps, moistures, 'b-', label='Soil Moisture')
                    ax1.set_ylabel('Moisture (%)')
                    ax1.grid(True)
                    ax1.axhline(y=obj.soil_moisture, color='r', linestyle='--', alpha=0.7)
                    
                    ax2.plot(timestamps, temperatures, 'r-', label='Temperature')
                    ax2.set_ylabel('Temperature (°C)')
                    ax2.grid(True)
                    ax2.axhline(y=obj.temperature, color='r', linestyle='--', alpha=0.7)
                    
                    ax3.plot(timestamps, humidities, 'g-', label='Humidity')
                    ax3.set_ylabel('Humidity (%)')
                    ax3.set_xlabel('Time')
                    ax3.grid(True)
                    ax3.axhline(y=obj.humidity, color='r', linestyle='--', alpha=0.7)
                    
                    # Format x-axis
                    for ax in [ax1, ax2, ax3]:
                        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
                        ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
                        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
                    
                    plt.tight_layout()
                    
                    # Save plot to base64 string
                    buffer = BytesIO()
                    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
                    buffer.seek(0)
                    image_png = buffer.getvalue()
                    buffer.close()
                    plt.close()
                    
                    graphic = base64.b64encode(image_png)
                    graphic = graphic.decode('utf-8')
                    
                    return format_html(
                        '<img src="data:image/png;base64,{}" style="max-width: 100%; height: auto;">',
                        graphic
                    )
                except Exception as e:
                    return f"Could not generate visualization: {str(e)}"
            else:
                return "Need more data points for visualization"
        return "Save record first to see visualization"
    
    data_visualization.short_description = "Data Visualization"

@admin.register(IrrigationPrediction)
class IrrigationPredictionAdmin(admin.ModelAdmin):
    list_display = ('field', 'recommendation_display', 'confidence_display', 'sensor_values', 'created_at')
    list_filter = ('recommendation', 'created_at', 'field__crop_type')
    search_fields = ('field__name', 'reasoning')
    readonly_fields = ('created_at', 'sensor_details', 'prediction_analysis')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Prediction Information', {
            'fields': ('field', 'sensor_data', 'recommendation', 'confidence_score', 'reasoning')
        }),
        ('Analysis', {
            'fields': ('sensor_details', 'prediction_analysis'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def recommendation_display(self, obj):
        """Display recommendation with color coding and icons"""
        colors = {
            'IRRIGATE': 'red',
            'MONITOR': 'orange',
            'WAIT': 'green'
        }
        icons = {
            'IRRIGATE': '💧',
            'MONITOR': '👀',
            'WAIT': '⏱️'
        }
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            colors.get(obj.recommendation, 'black'),
            icons.get(obj.recommendation, ''),
            obj.recommendation
        )
    
    recommendation_display.short_description = "Recommendation"
    
    def confidence_display(self, obj):
        """Display confidence score with color coding"""
        confidence = obj.confidence_score
        if confidence > 0.8:
            color = 'green'
            status = 'High'
        elif confidence > 0.6:
            color = 'orange'
            status = 'Medium'
        else:
            color = 'red'
            status = 'Low'
        
        return format_html(
            '<span style="color: {};">{:.1%} ({})</span>',
            color,
            confidence,
            status
        )
    
    confidence_display.short_description = "Confidence"
    
    def sensor_values(self, obj):
        """Display sensor values inline"""
        return format_html(
            '💧{:.1f}% | 🌡️{:.1f}°C | 💨{:.1f}%',
            obj.sensor_data.soil_moisture,
            obj.sensor_data.temperature,
            obj.sensor_data.humidity
        )
    
    sensor_values.short_description = "Sensor Values"
    
    def sensor_details(self, obj):
        """Show detailed sensor information"""
        return format_html(
            """
            <div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">
                <strong>Sensor Reading Details:</strong><br>
                📊 Soil Moisture: {:.1f}%<br>
                🌡️ Temperature: {:.1f}°C<br>
                💨 Humidity: {:.1f}%<br>
                📅 Reading Time: {}<br>
                📍 Field: {} ({})
            </div>
            """,
            obj.sensor_data.soil_moisture,
            obj.sensor_data.temperature,
            obj.sensor_data.humidity,
            obj.sensor_data.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            obj.field.name,
            obj.field.crop_type
        )
    
    sensor_details.short_description = "Sensor Details"
    
    def prediction_analysis(self, obj):
        """Show prediction analysis"""
        # Calculate thresholds
        moisture_status = "Critical" if obj.sensor_data.soil_moisture < 20 else "Low" if obj.sensor_data.soil_moisture < 35 else "Good"
        temp_status = "High" if obj.sensor_data.temperature > 35 else "Low" if obj.sensor_data.temperature < 15 else "Normal"
        humidity_status = "Low" if obj.sensor_data.humidity < 40 else "High" if obj.sensor_data.humidity > 70 else "Normal"
        
        return format_html(
            """
            <div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">
                <strong>Prediction Analysis:</strong><br>
                🔍 Moisture Status: {}<br>
                🔍 Temperature Status: {}<br>
                🔍 Humidity Status: {}<br>
                💡 Recommendation: <strong>{}</strong><br>
                📊 Confidence: {:.1%}<br>
                🎯 Reasoning: {}<br>
            </div>
            """,
            moisture_status,
            temp_status,
            humidity_status,
            obj.recommendation,
            obj.confidence_score,
            obj.reasoning[:100] + "..." if len(obj.reasoning) > 100 else obj.reasoning
        )
    
    prediction_analysis.short_description = "Prediction Analysis"

# Custom admin site configuration
admin.site.site_header = "Irrigation AI Management System"
admin.site.site_title = "Irrigation AI Admin"
admin.site.index_title = "Welcome to Irrigation AI Administration"

# Add custom CSS for better styling
admin.site.enable_nav_sidebar = True