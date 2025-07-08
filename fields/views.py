
from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction
import json
import logging

from .models import Sensor, Farm, Field, SensorType
from .forms import FieldCreateForm, SensorForm

logger = logging.getLogger(__name__)

from fields.models import Field, Alert, Farm, SensorReading, SensorType
from data_collection.models import Sensor

@login_required
def dashboard(request):
    farms = Farm.objects.prefetch_related('fields__sensors').filter(owner=request.user)
    total_fields = Field.objects.filter(farm__owner=request.user).count()
    total_sensors = Sensor.objects.filter(farm__owner=request.user).count()

    # Fix here: Alert relates to Sensor, then Field, then Farm, then owner
    active_alerts = Alert.objects.filter(sensor__field__farm__owner=request.user, is_resolved=False).count()

    
    context = {
        'farms': farms,
        'total_fields': total_fields,
        'total_sensors': total_sensors,
        'active_alerts': active_alerts,
    }
    return render(request, 'fields/dashboard.html', context)

@login_required
def field_detail(request, field_id):
    field = get_object_or_404(Field, id=field_id, farm__owner=request.user)
    sensors = field.sensors.filter(is_active=True)
    
    sensor_data = []
    for sensor in sensors:
        latest_reading = sensor.readings.first()
        recent_readings = sensor.readings.filter(
            timestamp__gte=timezone.now() - timedelta(hours=24)
        )[:20]
        
        sensor_data.append({
            'sensor': sensor,
            'latest_reading': latest_reading,
            'recent_readings': list(recent_readings.values('value', 'timestamp')),
            'active_alerts': sensor.alerts.filter(is_resolved=False).count()
        })

    # ✅ Move this outside the loop:
    active_alerts = Alert.objects.filter(sensor__field=field, is_resolved=False)

    context = {
        'field': field,
        'sensor_data': sensor_data,
        'active_alerts': active_alerts,
    }
    return render(request, 'fields/field_detail.html', context)

@login_required
def sensor_readings_api(request, sensor_id):
    sensor = get_object_or_404(Sensor, id=sensor_id, field__farm__owner=request.user)
    hours = int(request.GET.get('hours', 24))
    
    readings = sensor.readings.filter(
        timestamp__gte=timezone.now() - timedelta(hours=hours)
    ).values('value', 'timestamp')
    
    data = []
    for reading in readings:
        data.append({
            'timestamp': reading['timestamp'].isoformat(),
            'value': float(reading['value'])
        })
    
    return JsonResponse({
        'sensor_id': str(sensor.id),
        'sensor_type': sensor.sensor_type.name,
        'unit': sensor.sensor_type.unit,
        'readings': data
    })


@login_required
def add_sensor_reading(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        sensor_id = data.get('sensor_id')
        value = data.get('value')
        
        try:
            # Fix: get single sensor instance by id and ownership
            sensor = Sensor.objects.get(id=sensor_id, farm__owner=request.user)
            reading = SensorReading.objects.create(sensor=sensor, value=value)
            
            return JsonResponse({
                'success': True,
                'message': 'Reading added successfully',
                'reading_id': reading.id
            })
        except Sensor.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Sensor not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
def alerts_view(request):
    alerts = Alert.objects.filter(sensor__is_active=True, is_resolved=False)

    status = request.GET.get('status', 'all')
    sensor_type = request.GET.get('sensor_type', 'all')
    
    if status == 'active':
        alerts = alerts.filter(is_resolved=False)
    elif status == 'resolved':
        alerts = alerts.filter(is_resolved=True)
    
    if sensor_type != 'all':
        alerts = alerts.filter(sensor__sensor_type__name=sensor_type)
    
    context = {
        'alerts': alerts,
        'sensor_types': SensorType.objects.all(),
        'current_status': status,
        'current_sensor_type': sensor_type,
    }
    return render(request, 'fields/alerts.html', context)


@login_required
def resolve_alert(request, alert_id):
    alert = get_object_or_404(Alert, id=alert_id, sensor__field__farm__owner=request.user)
    alert.resolve(user=request.user)
    messages.success(request, 'Alert resolved successfully.')
    return redirect('alerts')


def field_list(request):
    fields = Field.objects.all()
    return render(request, 'fields/field_list.html', {'fields': fields})


@login_required
def field_create(request):
    """
    Create a new field for the authenticated user's farm.
    """
    if request.method == 'POST':
        form = FieldCreateForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    field = form.save(commit=False)
                    # Ensure the field belongs to a farm owned by the current user
                    if field.farm.owner != request.user:
                        messages.error(request, 'You can only create fields for your own farms.')
                        return render(request, 'fields/field_create.html', {'form': form})
                    
                    field.save()
                    messages.success(request, f'Field "{field.name}" has been created successfully!')
                    return redirect(reverse('farms:farm_detail', kwargs={'farm_id': field.farm.id}))
                    
            except ValidationError as e:
                messages.error(request, f'Error creating field: {e.message}')
            except Exception as e:
                messages.error(request, f'An unexpected error occurred: {str(e)}')
    else:
        form = FieldCreateForm(user=request.user)
    
    context = {
        'form': form,
        'title': 'Create New Field',
    }
    return render(request, 'fields/field_create.html', context)


@login_required 
def field_update(request, field_id):
    """
    Update an existing field owned by the authenticated user.
    """
    field = get_object_or_404(Field, id=field_id, farm__owner=request.user)
    
    if request.method == 'POST':
        form = FieldCreateForm(request.POST, instance=field, user=request.user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    updated_field = form.save(commit=False)
                    # Ensure the field still belongs to a farm owned by the current user
                    if updated_field.farm.owner != request.user:
                        messages.error(request, 'You can only update fields for your own farms.')
                        return render(request, 'fields/field_create.html', {'form': form, 'field': field})
                    
                    updated_field.save()
                    messages.success(request, f'Field "{updated_field.name}" has been updated successfully!')
                    return redirect('field_detail', field_id=updated_field.id)
                    
            except ValidationError as e:
                messages.error(request, f'Error updating field: {e.message}')
            except Exception as e:
                messages.error(request, f'An unexpected error occurred: {str(e)}')
    else:
        form = FieldCreateForm(instance=field, user=request.user)
    
    context = {
        'form': form,
        'field': field,
        'title': f'Update Field: {field.name}',
    }
    return render(request, 'fields/field_create.html', context)


@login_required
def field_delete(request, field_id):
    """
    Delete a field owned by the authenticated user.
    """
    field = get_object_or_404(Field, id=field_id, farm__owner=request.user)
    
    if request.method == 'POST':
        field_name = field.name
        try:
            field.delete()
            messages.success(request, f'Field "{field_name}" has been deleted successfully!')
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, f'Error deleting field: {str(e)}')
            return redirect('field_detail', field_id=field.id)
    
    context = {
        'field': field,
        'title': f'Delete Field: {field.name}',
    }
    return render(request, 'fields/field_confirm_delete.html', context)


# Also add this to your existing field_list view to filter by user
@login_required
def field_list(request):
    """
    List all fields owned by the authenticated user.
    """
    fields = Field.objects.filter(farm__owner=request.user).select_related('farm').prefetch_related('sensors')
    
    # Add filtering options
    farm_id = request.GET.get('farm')
    crop_type = request.GET.get('crop_type')
    is_active = request.GET.get('is_active')
    
    if farm_id:
        fields = fields.filter(farm_id=farm_id)
    
    if crop_type:
        fields = fields.filter(crop_type__icontains=crop_type)
    
    if is_active is not None:
        is_active_bool = is_active.lower() == 'true'
        fields = fields.filter(is_active=is_active_bool)
    
    # Get user's farms for filtering dropdown
    user_farms = Farm.objects.filter(owner=request.user)
    
    # Get unique crop types for filtering
    crop_types = Field.objects.filter(farm__owner=request.user).values_list('crop_type', flat=True).distinct()
    crop_types = [ct for ct in crop_types if ct]  # Remove empty values
    
    context = {
        'fields': fields,
        'user_farms': user_farms,
        'crop_types': crop_types,
        'current_farm': farm_id,
        'current_crop_type': crop_type,
        'current_is_active': is_active,
        'title': 'My Fields',
    }
    return render(request, 'fields/field_list.html', context)

@login_required
@require_http_methods(["GET"])
def get_farm_fields(request, farm_id):
    """
    API endpoint to get fields for a specific farm
    """
    try:
        farm = get_object_or_404(Farm, id=farm_id, owner=request.user)
        fields = Field.objects.filter(farm=farm).values('id', 'name', 'area_hectares')
        
        return JsonResponse({
            'success': True,
            'fields': list(fields)
        })
    except Exception as e:
        logger.error(f'Error fetching fields for farm {farm_id}: {str(e)}')
        return JsonResponse({
            'success': False,
            'error': 'Failed to fetch fields'
        }, status=500)



