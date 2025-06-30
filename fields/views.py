
from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
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
    
        active_alerts = Alert.objects.filter(
            sensor__field__farm__owner=request.user, 
            sensor__is_active=True
        ).count()
    
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
                    return redirect('field_detail', field_id=field.id)
                    
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


logger = logging.getLogger(__name__)

@login_required
def sensor_create(request):
    """
    Create a new sensor
    """
    if request.method == 'POST':
        form = SensorForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    sensor = form.save(commit=False)
                    
                    # Set installation date to today if not provided
                    if not sensor.installation_date:
                        sensor.installation_date = timezone.now().date()
                    
                    sensor.save()
                    
                messages.success(request, f'Sensor "{sensor.name}" has been created successfully!')
                return redirect('field_detail', field_id=sensor.field.id)
                
            except ValidationError as e:
                messages.error(request, f'Validation error: {str(e)}')
            except Exception as e:
                logger.error(f'Error creating sensor: {str(e)}', exc_info=True)
                messages.error(request, 'An error occurred while creating the sensor. Please try again.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SensorForm(user=request.user)
        
        # Pre-populate field if provided in URL parameters
        field_id = request.GET.get('field_id')
        
        if field_id:
            try:
                field = Field.objects.get(id=field_id, farm__owner=request.user)
                form.fields['field'].initial = field
            except Field.DoesNotExist:
                pass
    
    context = {
        'form': form,
        'title': 'Create New Sensor',
    }
    
    return render(request, 'fields/sensor_create.html', context)

@login_required
def sensor_update(request, pk):
    """
    Update an existing sensor
    """
    sensor = get_object_or_404(Sensor, pk=pk, field__farm__owner=request.user)
    
    if request.method == 'POST':
        form = SensorForm(request.POST, instance=sensor)
        if form.is_valid():
            try:
                with transaction.atomic():
                    updated_sensor = form.save(commit=False)
                    updated_sensor.updated_at = timezone.now()
                    updated_sensor.save()
                    
                messages.success(request, f'Sensor "{updated_sensor.name}" has been updated successfully!')
                return redirect('field_detail', pk=updated_sensor.field.id)
                
            except ValidationError as e:
                messages.error(request, f'Validation error: {e.message}')
            except Exception as e:
                logger.error(f'Error updating sensor {pk}: {str(e)}')
                messages.error(request, 'An error occurred while updating the sensor. Please try again.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SensorForm(instance=sensor)
    
    # Filter farms to only show user's farms
    form.fields['farm'].queryset = Farm.objects.filter(owner=request.user)
    
    context = {
        'form': form,
        'sensor': sensor,
        'title': f'Update Sensor: {sensor.name}',
    }
    
    return render(request, 'sensors/sensor_create.html', context)


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


@login_required
@require_http_methods(["GET"])
def get_sensor_type_details(request, sensor_type_id):
    """
    API endpoint to get sensor type details
    """
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
        return JsonResponse({
            'success': False,
            'error': 'Failed to fetch sensor type details'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def test_sensor(request, sensor_id):
    """
    API endpoint to test a sensor connection and get latest reading
    """
    try:
        sensor = get_object_or_404(Sensor, id=sensor_id, field__farm__owner=request.user)
        
        if not sensor.is_active:
            return JsonResponse({
                'success': False,
                'message': 'Sensor is not active'
            })
        
        if sensor.status != 'active':
            return JsonResponse({
                'success': False,
                'message': f'Sensor status is {sensor.status}'
            })
        
        # Get the latest reading from the sensor
        latest_reading = sensor.readings.order_by('-timestamp').first()
        
        if latest_reading:
            # Calculate time since last reading
            time_diff = timezone.now() - latest_reading.timestamp
            hours_since = time_diff.total_seconds() / 3600
            
            if hours_since > 24:  # No reading in last 24 hours
                return JsonResponse({
                    'success': False,
                    'message': f'No recent readings. Last reading was {hours_since:.1f} hours ago.'
                })
            
            return JsonResponse({
                'success': True,
                'message': 'Sensor test successful',
                'reading': latest_reading.value,
                'unit': sensor.sensor_type.unit,
                'timestamp': latest_reading.timestamp.isoformat(),
                'hours_since_reading': round(hours_since, 1)
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'No readings found for this sensor'
            })
            
    except Exception as e:
        logger.error(f'Error testing sensor {sensor_id}: {str(e)}')
        return JsonResponse({
            'success': False,
            'message': 'Error occurred while testing sensor'
        }, status=500)


@login_required
def sensor_detail(request, pk):
    """
    Display detailed view of a sensor
    """
    sensor = get_object_or_404(Sensor, pk=pk, field__farm__owner=request.user)
    
    # Get recent readings (last 100)
    recent_readings = sensor.readings.order_by('-timestamp')[:100]
    
    # Calculate sensor statistics
    if recent_readings:
        readings_values = [r.value for r in recent_readings]
        stats = {
            'latest_reading': recent_readings[0],
            'avg_value': sum(readings_values) / len(readings_values),
            'min_value': min(readings_values),
            'max_value': max(readings_values),
            'total_readings': sensor.readings.count(),
        }
    else:
        stats = {
            'latest_reading': None,
            'avg_value': None,
            'min_value': None,
            'max_value': None,
            'total_readings': 0,
        }
    
    context = {
        'sensor': sensor,
        'recent_readings': recent_readings,
        'stats': stats,
    }
    
    return render(request, 'fileds/sensor_detail.html', context)


@login_required
def sensor_delete(request, pk):
    """
    Delete a sensor
    """
    sensor = get_object_or_404(Sensor, pk=pk, field__farm__owner=request.user)
    field_id = sensor.field.id
    
    if request.method == 'POST':
        try:
            sensor_name = sensor.name
            sensor.delete()
            messages.success(request, f'Sensor "{sensor_name}" has been deleted successfully!')
            return redirect('field_detail', pk=field_id)
        except Exception as e:
            logger.error(f'Error deleting sensor {pk}: {str(e)}')
            messages.error(request, 'An error occurred while deleting the sensor.')
            return redirect('sensor_detail', pk=pk)
    
    context = {
        'sensor': sensor,
    }
    
    return render(request, 'fields/sensor_confirm_delete.html', context)


@login_required
def sensor_list(request):
    """
    List all sensors for the current user
    """
    sensors = Sensor.objects.filter(
        field__farm__owner=request.user
    ).select_related(
        'field', 'field__farm', 'sensor_type'
    ).order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter and status_filter in ['active', 'inactive', 'maintenance']:
        sensors = sensors.filter(status=status_filter)
    
    # Filter by sensor type if provided
    sensor_type_filter = request.GET.get('sensor_type')
    if sensor_type_filter:
        sensors = sensors.filter(sensor_type_id=sensor_type_filter)
    
    # Filter by farm if provided
    farm_filter = request.GET.get('farm')
    if farm_filter:
        sensors = sensors.filter(field__farm_id=farm_filter)
    
    # Get available sensor types and farms for filters
    available_sensor_types = SensorType.objects.all()
    available_farms = Farm.objects.filter(owner=request.user)
    
    context = {
        'sensors': sensors,
        'available_sensor_types': available_sensor_types,
        'available_farms': available_farms,
        'current_status_filter': status_filter,
        'current_sensor_type_filter': sensor_type_filter,
        'current_farm_filter': farm_filter,
    }
    
    return render(request, 'fields/sensor_list.html', context)


@login_required
@require_http_methods(["POST"])
def sensor_calibrate(request, pk):
    """
    Calibrate a sensor with new offset and slope values
    """
    sensor = get_object_or_404(Sensor, pk=pk, field__farm__owner=request.user)
    
    try:
        data = json.loads(request.body)
        offset = float(data.get('offset', 0))
        slope = float(data.get('slope', 1))
        
        # Update calibration values
        sensor.calibration_offset = offset
        sensor.calibration_slope = slope
        sensor.last_calibration = timezone.now()
        sensor.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Sensor calibrated successfully',
            'offset': offset,
            'slope': slope,
            'last_calibration': sensor.last_calibration.isoformat()
        })
        
    except (json.JSONDecodeError, ValueError) as e:
        return JsonResponse({
            'success': False,
            'message': 'Invalid calibration data provided'
        }, status=400)
    except Exception as e:
        logger.error(f'Error calibrating sensor {pk}: {str(e)}')
        return JsonResponse({
            'success': False,
            'message': 'Error occurred while calibrating sensor'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def sensor_toggle_status(request, pk):
    """
    Toggle sensor active/inactive status
    """
    sensor = get_object_or_404(Sensor, pk=pk, field__farm__owner=request.user)
    
    try:
        sensor.is_active = not sensor.is_active
        sensor.save()
        
        status_text = "activated" if sensor.is_active else "deactivated"
        messages.success(request, f'Sensor "{sensor.name}" has been {status_text}.')
        
        return JsonResponse({
            'success': True,
            'is_active': sensor.is_active,
            'message': f'Sensor {status_text} successfully'
        })
        
    except Exception as e:
        logger.error(f'Error toggling sensor status {pk}: {str(e)}')
        return JsonResponse({
            'success': False,
            'message': 'Error occurred while updating sensor status'
        }, status=500)
    
