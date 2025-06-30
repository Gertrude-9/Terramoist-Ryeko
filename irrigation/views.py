from collections import defaultdict
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from .models import IrrigationZone, IrrigationSchedule, IrrigationLog, WeatherData
from .weather import get_weather_forecast
import requests
from .schedular import generate_auto_schedule
from django.db.models import Count, Avg, Sum
from datetime import datetime, timedelta

import json

@login_required
def irrigation_dashboard(request):
    """Main irrigation dashboard view"""
    zones = IrrigationZone.objects.all()
    active_schedules = IrrigationSchedule.objects.filter(status='active').count()
    recent_logs = IrrigationLog.objects.select_related('zone', 'schedule').order_by('-start_time')[:5]
    
    today = timezone.now().date()
    todays_schedules = IrrigationSchedule.objects.filter(
        status='active',
        start_date__lte=today
    ).select_related('zone')
    
    try:
        weather_today = WeatherData.objects.get(date=today)
    except WeatherData.DoesNotExist:
        weather_today = None
    
    context = {
        'zones': zones,
        'active_schedules': active_schedules,
        'recent_logs': recent_logs,
        'todays_schedules': todays_schedules,
        'weather_today': weather_today,
    }
    return render(request, 'irrigation/dashboard.html', context)

@login_required
def schedule_list(request):
    """List all irrigation schedules"""
    schedules = IrrigationSchedule.objects.select_related('zone', 'created_by').order_by('-created_at')
    
    status_filter = request.GET.get('status')
    if status_filter:
        schedules = schedules.filter(status=status_filter)
    
    zone_filter = request.GET.get('zone')
    if zone_filter:
        schedules = schedules.filter(zone_id=zone_filter)
    
    zones = IrrigationZone.objects.all()
    
    context = {
        'schedules': schedules,
        'zones': zones,
        'current_status': status_filter,
        'current_zone': zone_filter,
    }
    return render(request, 'irrigation/schedule_list.html', context)

@login_required
def create_schedule(request):
    if request.method == 'POST':
        try:
            zone = get_object_or_404(IrrigationZone, id=request.POST['zone'])

            schedule = IrrigationSchedule.objects.create(
                zone=zone,
                name=request.POST['name'],
                start_time=request.POST['start_time'],
                duration_minutes=int(request.POST['duration_minutes']),
                frequency=request.POST['frequency'],
                start_date=request.POST['start_date'],
                end_date=request.POST.get('end_date') or None,
                auto_weather_adjust=request.POST.get('auto_weather_adjust') == 'on',
                created_by=request.user
            )

            messages.success(request, f'Schedule "{schedule.name}" created successfully!')
            return redirect('irrigation:schedule_list')

        except Exception as e:
            messages.error(request, f'Error creating schedule: {str(e)}')

    zones = IrrigationZone.objects.all()
    return render(request, 'irrigation/create_schedule.html', {'zones': zones})

@login_required
def start_immediate_irrigation(request):
    """Start immediate irrigation for a zone"""
    if request.method == 'POST':
        try:
            zone_id = request.POST.get('zone_id')
            duration = int(request.POST.get('duration', 30))
            
            zone = get_object_or_404(IrrigationZone, id=zone_id)
            
            log = IrrigationLog.objects.create(
                zone=zone,
                schedule=None,
                start_time=timezone.now(),
                notes=f"Manual irrigation started by {request.user.username}"
            )
            
            messages.success(request, f'Immediate irrigation started for {zone.name}')
            return JsonResponse({'status': 'success', 'log_id': log.id})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    zones = IrrigationZone.objects.all()
    return render(request, 'irrigation/immediate_irrigation.html', {'zones': zones})

@login_required
def historical_data(request):
    """View historical irrigation data"""
    logs = IrrigationLog.objects.select_related('zone', 'schedule').order_by('-start_time')
    
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if date_from:
        logs = logs.filter(start_time__date__gte=date_from)
    if date_to:
        logs = logs.filter(start_time__date__lte=date_to)
    
    zone_filter = request.GET.get('zone')
    if zone_filter:
        logs = logs.filter(zone_id=zone_filter)
    
    total_volume = logs.aggregate(total=Sum('water_volume_liters'))['total'] or 0
    avg_duration = logs.aggregate(avg=Avg('duration_actual'))['avg'] or 0
    
    zones = IrrigationZone.objects.all()
    
    context = {
        'logs': logs[:50],
        'zones': zones,
        'total_volume': total_volume,
        'avg_duration': round(avg_duration, 1) if avg_duration else 0,
        'date_from': date_from,
        'date_to': date_to,
        'current_zone': zone_filter,
    }
    return render(request, 'irrigation/historical_data.html', context)

@login_required
def auto_schedule_weather(request):
    """Auto-schedule irrigation based on weather conditions"""
    if request.method == 'POST':
        try:
            zones = IrrigationZone.objects.all()
            schedules_created = 0
            
            for zone in zones:
                schedule = IrrigationSchedule.objects.create(
                    zone=zone,
                    name=f"Auto Weather Schedule - {zone.name}",
                    start_time="06:00",
                    duration_minutes=45,
                    frequency='daily',
                    start_date=timezone.now().date(),
                    end_date=timezone.now().date() + timedelta(days=7),
                    auto_weather_adjust=True,
                    created_by=request.user
                )
                schedules_created += 1
            
            messages.success(request, f'Created {schedules_created} weather-based schedules')
            return redirect('irrigation:schedule_list')
            
        except Exception as e:
            messages.error(request, f'Error creating auto schedules: {str(e)}')
    
    return render(request, 'irrigation/auto_schedule.html')

@login_required
def auto_schedule_view(request):
    """View for auto-scheduling interface"""
    zones = IrrigationZone.objects.all()
    city = 'Kampala'
    api_key = '03d758ad12df45f05330bc3d12f2f440'
    weather_forecast = get_weather_forecast(city, api_key, days=7) or []
    
    generated_schedules = request.session.get('generated_schedules', [])
    if generated_schedules:
        schedules = []
        for s in generated_schedules:
            try:
                zone = IrrigationZone.objects.get(id=s['zone_id'])
                schedule = IrrigationSchedule(
                    id=s['id'],
                    zone=zone,
                    start_time=s['start_time'],
                    duration=s['duration'],
                    status='pending'
                )
                schedules.append(schedule)
            except IrrigationZone.DoesNotExist:
                continue
        generated_schedules = schedules
    
    context = {
        'zones': zones,
        'weather_forecast': weather_forecast,
        'generated_schedules': generated_schedules,
    }
    return render(request, 'irrigation/auto_schedule.html', context)

@login_required
def generate_schedule(request):
    """Generate schedules based on parameters"""
    if request.method == 'POST':
        schedule_type = request.POST.get('schedule_type', 'weather')
        duration_days = int(request.POST.get('duration', 7))
        zone_ids = request.POST.getlist('zones')
        water_saving = request.POST.get('water_saving', 'moderate')
        
        zones = IrrigationZone.objects.filter(id__in=zone_ids)
        
        generated_schedules = generate_auto_schedule(
            zones=zones,
            schedule_type=schedule_type,
            duration_days=duration_days,
            water_saving=water_saving
        )
        
        serialized_schedules = []
        for i, schedule in enumerate(generated_schedules):
            serialized_schedules.append({
                'id': i + 1,
                'zone_id': schedule['zone'].id,
                'start_time': schedule['start_time'].isoformat(),
                'duration': schedule['duration'],
            })
        
        request.session['generated_schedules'] = serialized_schedules
        return redirect('irrigation:auto_schedule')
    
    return redirect('irrigation:auto_schedule')

@login_required
def confirm_schedule(request, schedule_id):
    """Confirm an auto-generated schedule"""
    if request.method == 'POST':
        generated_schedules = request.session.get('generated_schedules', [])
        
        schedule_to_confirm = None
        for s in generated_schedules:
            if s['id'] == schedule_id:
                schedule_to_confirm = s
                break
        
        if schedule_to_confirm:
            try:
                zone = IrrigationZone.objects.get(id=schedule_to_confirm['zone_id'])
                IrrigationSchedule.objects.create(
                    zone=zone,
                    start_time=schedule_to_confirm['start_time'],
                    duration_minutes=schedule_to_confirm['duration'],
                    status='pending',
                    is_auto_scheduled=True,
                    created_by=request.user
                )
                
                messages.success(request, f'Schedule for {zone.name} confirmed!')
            except Exception as e:
                messages.error(request, f'Error confirming schedule: {str(e)}')
        
        return redirect('irrigation:auto_schedule')
    
    return redirect('irrigation:auto_schedule')


def get_weather_data(request):
    api_key = '03d758ad12df45f05330bc3d12f2f440'
    city = 'Kampala'
    url = f'https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric'

    response = requests.get(url)
    data = response.json()

    # Group forecasts by day
    daily_data = defaultdict(list)
    for entry in data['list']:
        date_str = entry['dt_txt'].split(' ')[0]
        daily_data[date_str].append(entry)

    forecast = []
    for date_str, entries in daily_data.items():
        temps_max = [e['main']['temp_max'] for e in entries]
        temps_min = [e['main']['temp_min'] for e in entries]
        # take first icon & precip for the day
        icon = entries[0]['weather'][0]['icon']
        precip = sum(e.get('rain', {}).get('3h', 0) for e in entries)

        forecast.append({
            'date': date_str,
            'temperature_max': round(max(temps_max)),
            'temperature_min': round(min(temps_min)),
            'icon': icon,
            'precip': round(precip)
        })

    # Return next 7 days (including today)
    forecast = sorted(forecast, key=lambda x: x['date'])[:7]

    return JsonResponse(forecast, safe=False)
