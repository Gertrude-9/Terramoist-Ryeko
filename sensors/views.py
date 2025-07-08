import json
import logging
from datetime import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods
from django.views.generic import (
    ListView, CreateView, DetailView, UpdateView, DeleteView
)

from fields.models import Farm, Field
from sensors.models import Sensor, SensorType
from .forms import SensorForm

logger = logging.getLogger(__name__)


class SensorListView(LoginRequiredMixin, ListView):
    model = Sensor
    template_name = 'sensors/sensor_list.html'
    context_object_name = 'sensors'

    def get_queryset(self):
        queryset = super().get_queryset().filter(field__farm__owner=self.request.user)
        farm_id = self.request.GET.get('farm')
        field_id = self.request.GET.get('field')
        if farm_id:
            queryset = queryset.filter(field__farm_id=farm_id)
        elif field_id:
            queryset = queryset.filter(field_id=field_id)
        return queryset.select_related('field', 'field__farm', 'sensor_type')


class SensorCreateView(LoginRequiredMixin, CreateView):
    model = Sensor
    form_class = SensorForm
    template_name = 'sensors/sensor_create.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user  # ✅ pass user into form
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['farms'] = Farm.objects.filter(owner=self.request.user).prefetch_related('fields')
        return context

    def form_valid(self, form):
        # Get the selected field from the form data
        field_id = self.request.POST.get('field')
        if field_id:
            try:
                field = Field.objects.get(id=field_id, farm__owner=self.request.user)
                form.instance.field = field
                form.instance.farm = field.farm  # Set the farm as well
            except Field.DoesNotExist:
                form.add_error('field', 'Selected field does not exist or you do not have permission to access it.')
                return self.form_invalid(form)
        else:
            form.add_error('field', 'Please select a field.')
            return self.form_invalid(form)
        
        # Save the sensor
        response = super().form_valid(form)
        return response

    def get_success_url(self):
        return reverse_lazy('sensors:sensor_detail', kwargs={'pk': self.object.pk})


class SensorDetailView(LoginRequiredMixin, DetailView):
    model = Sensor
    template_name = 'sensors/sensor_detail.html'
    context_object_name = 'sensor'

    def get_queryset(self):
        return super().get_queryset().filter(field__farm__owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        farms = Farm.objects.all()
        
        # Convert farms and their fields to a serializable format
        farms_data = []
        for farm in farms:
            farm_data = {
                'id': farm.id,
                'name': farm.name,
                'fields': list(farm.fields.values('id', 'name'))  # Convert to list of dicts
            }
            farms_data.append(farm_data)
        
        context['farms'] = farms_data
        return context


class SensorUpdateView(LoginRequiredMixin, UpdateView):
    model = Sensor
    form_class = SensorForm
    template_name = 'sensors/sensor_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user  # ✅ important
        return kwargs

    def get_success_url(self):
        return reverse_lazy('sensors:sensor_detail', kwargs={'pk': self.object.pk})


class SensorDeleteView(LoginRequiredMixin, DeleteView):
    model = Sensor
    template_name = 'sensors/sensor_confirm_delete.html'

    def get_queryset(self):
        return super().get_queryset().filter(field__farm__owner=self.request.user)

    def get_success_url(self):
        return reverse_lazy('fields:field_detail', kwargs={'pk': self.object.field.pk})


@login_required
@require_http_methods(["GET"])
def get_sensor_type_details(request, sensor_type_id):
    try:
        sensor_type = get_object_or_404(SensorType, id=sensor_type_id)
        return JsonResponse({
            'success': True,
            'id': sensor_type.id,
            'name': sensor_type.name,
            'unit': sensor_type.unit,
            'min_value': sensor_type.min_value,
            'max_value': sensor_type.max_value,
            'description': sensor_type.description,
            'measurement_type': sensor_type.measurement_type,
        })
    except Exception as e:
        logger.error(f'Error fetching sensor type {sensor_type_id}: {str(e)}')
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def sensor_calibrate(request, pk):
    sensor = get_object_or_404(Sensor, pk=pk, field__farm__owner=request.user)
    try:
        data = json.loads(request.body)
        sensor.calibration_offset = float(data.get('offset', 0))
        sensor.calibration_slope = float(data.get('slope', 1))
        sensor.last_calibration = timezone.now()
        sensor.save()
        return JsonResponse({'success': True, 'message': 'Calibration successful'})
    except Exception as e:
        logger.error(f'Error calibrating sensor {pk}: {str(e)}')
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def sensor_toggle_status(request, pk):
    sensor = get_object_or_404(Sensor, pk=pk, field__farm__owner=request.user)
    try:
        sensor.is_active = not sensor.is_active
        sensor.save()
        return JsonResponse({
            'success': True,
            'is_active': sensor.is_active,
            'message': f'Sensor {"activated" if sensor.is_active else "deactivated"}'
        })
    except Exception as e:
        logger.error(f'Error toggling sensor status {pk}: {str(e)}')
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_farms_and_fields(request):
    try:
        farms = Farm.objects.filter(owner=request.user).prefetch_related('fields')
        farms_data = [
            {
                'id': farm.id,
                'name': farm.name,
                'fields': [{'id': field.id, 'name': field.name} for field in farm.fields.all()]
            }
            for farm in farms
        ]
        return JsonResponse({'success': True, 'farms': farms_data})
    except Exception as e:
        logger.error(f'Error fetching farms and fields: {str(e)}')
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
