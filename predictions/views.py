# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from datetime import timedelta
import json
from fields.models import Field
from predictions.models import AIInsightsManager, IrrigationPrediction, SensorData
from predictions.forms import SensorDataForm

class AIInsightsView(TemplateView):
    template_name = "predictions/ai_insights.html"

class HomeView(LoginRequiredMixin, TemplateView):
    """Main dashboard view"""
    template_name = 'predictions/prediction_home.html'

    
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    # Corrected queryset filter:
    fields = Field.objects.filter(owner=self.request.user)
    
    # Get status for each field
    field_status = []
    for field in fields:
        latest_prediction = field.predictions.first()
        status = {
            'field': field,
            'latest_data': field.sensor_data.first(),
            'prediction': latest_prediction,
            'status': (
                'secondary' if not latest_prediction else
                'danger' if latest_prediction.recommendation == 'IRRIGATE' else
                'warning' if latest_prediction.recommendation == 'MONITOR' else
                'success'
            )
        }
        field_status.append(status)

        context.update({
        'fields': fields,
        'field_status': field_status,
        'fields_count': fields.count(),
        'active_alerts': 0,  # Replace with actual alerts count
        'pending_tasks': 0,  # Replace with actual tasks count
        'active_sensors': SensorData.objects.filter(field__owner=self.request.user).count(),
        'total_sensors': fields.count() * 3,  # Assuming 3 sensors per field
        'sensor_percentage': 75,  # Example value
        'last_update': timezone.now() - timedelta(hours=2)  # Example value
    })
    return context

class IrrigationInsightsView(LoginRequiredMixin, View):
    """View for field insights and predictions"""
    template_name = 'insights_api.html'

    def __init__(self):
        super().__init__()
        self.ai_manager = AIInsightsManager()

    def get(self, request, field_id):
        field = get_object_or_404(Field, id=field_id, owner=request.user)
        
        # Get query parameters
        insight_type = request.GET.get('insight_type', 'all')
        days = int(request.GET.get('days', 7))
        
        # Get insights
        insights = self.ai_manager.get_insights_by_type(field_id, insight_type, days)
        
        # Get latest sensor data for current recommendation
        latest_data = field.sensor_data.first()
        current_prediction = None
        
        if latest_data:
            current_prediction = self.ai_manager.get_irrigation_recommendation(
                latest_data.soil_moisture,
                latest_data.temperature,
                latest_data.humidity
            )
        
        context = {
            'field': field,
            'insights': insights,
            'current_prediction': current_prediction,
            'latest_data': latest_data,
            'insight_type': insight_type,
            'days': days
        }
        
        return render(request, self.template_name, context)

class PredictionView(LoginRequiredMixin, View):
    """View for getting irrigation predictions"""
    template_name = 'prediction_api.html'

    def __init__(self):
        super().__init__()
        self.ai_manager = AIInsightsManager()

    def get(self, request, field_id):
        field = get_object_or_404(Field, id=field_id, owner=request.user)
        latest_data = field.sensor_data.first()
        prediction = None

        if latest_data:
            prediction = self.ai_manager.get_irrigation_recommendation(
                latest_data.soil_moisture,
                latest_data.temperature,
                latest_data.humidity
            )

        context = {
            'field': field,
            'latest_data': latest_data,
            'prediction': prediction,
            'form': SensorDataForm()
        }
        return render(request, self.template_name, context)

    def post(self, request, field_id):
        field = get_object_or_404(Field, id=field_id, owner=request.user)
        form = SensorDataForm(request.POST)
        
        if form.is_valid():
            sensor_data = form.save(commit=False)
            sensor_data.field = field
            sensor_data.save()
            
            # Get prediction
            prediction = self.ai_manager.get_irrigation_recommendation(
                sensor_data.soil_moisture,
                sensor_data.temperature,
                sensor_data.humidity
            )
            
            # Save prediction
            IrrigationPrediction.objects.create(
                field=field,
                sensor_data=sensor_data,
                recommendation=prediction['recommendation'],
                confidence_score=prediction['confidence_score'],
                reasoning=prediction['reasoning']
            )
            
            return redirect('prediction_view', field_id=field.id)
        
        context = {
            'field': field,
            'form': form
        }
        return render(request, self.template_name, context)

@method_decorator(csrf_exempt, name='dispatch')
class PredictionAPIView(LoginRequiredMixin, View):
    """API endpoint for getting irrigation predictions"""
    
    def __init__(self):
        super().__init__()
        self.ai_manager = AIInsightsManager()
    
    def post(self, request):
        """Make a prediction based on provided sensor data"""
        try:
            data = json.loads(request.body)
            
            soil_moisture = data.get('soil_moisture')
            temperature = data.get('temperature')
            humidity = data.get('humidity')
            field_id = data.get('field_id')
            
            if not all([soil_moisture, temperature, humidity, field_id]):
                return JsonResponse({'error': 'Missing required parameters'}, status=400)
            
            # Get prediction
            prediction = self.ai_manager.get_irrigation_recommendation(
                soil_moisture, temperature, humidity
            )
            
            # Save sensor data and prediction
            field = get_object_or_404(Field, id=field_id, owner=request.user)
            sensor_data = SensorData.objects.create(
                field=field,
                soil_moisture=soil_moisture,
                temperature=temperature,
                humidity=humidity
            )
            
            IrrigationPrediction.objects.create(
                field=field,
                sensor_data=sensor_data,
                recommendation=prediction['recommendation'],
                confidence_score=prediction['confidence_score'],
                reasoning=prediction['reasoning']
            )
            
            return JsonResponse({
                'success': True,
                'prediction': prediction,
                'sensor_data_id': sensor_data.id
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

class InsightsAPIView(LoginRequiredMixin, View):
    """API endpoint for getting various insights"""
    
    def __init__(self):
        super().__init__()
        self.ai_manager = AIInsightsManager()
    
    def get(self, request, field_id):
        """Get insights via API"""
        insight_type = request.GET.get('type', 'all')
        days = int(request.GET.get('days', 7))
        
        try:
            field = get_object_or_404(Field, id=field_id, owner=request.user)
            insights = self.ai_manager.get_insights_by_type(field_id, insight_type, days)
            
            return JsonResponse({
                'success': True,
                'insights': insights,
                'field_id': field_id,
                'type': insight_type,
                'days': days
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)