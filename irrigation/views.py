from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, DetailView
from fields.models import Field
from irrigation.models import IrrigationLog, SensorReading
from .services import IrrigationService
from .forms import IrrigationScheduleForm

def dashboard(request):
    fields = Field.objects.all()
    recent_logs = IrrigationLog.objects.order_by('-start_time')[:10]
    recent_readings = SensorReading.objects.order_by('-timestamp')[:10]
    
    context = {
        'fields': fields,
        'recent_logs': recent_logs,
        'recent_readings': recent_readings,
    }
    return render(request, 'irrigation/dashboard.html', context)

def manual_irrigation(request, field_id):
    field = Field.objects.get(pk=field_id)
    
    if request.method == 'POST':
        duration = int(request.POST.get('duration', 30))
        reason = request.POST.get('reason', 'Manual irrigation')
        
        IrrigationService.start_irrigation(field, duration, reason)
        messages.success(request, f"Irrigation started for {field.name}")
        return redirect('dashboard')
    
    return render(request, 'irrigation/manual_irrigation.html', {'field': field})

class FieldDetailView(DetailView):
    model = Field
    template_name = 'irrigation/field_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        field = self.get_object()
        
        context['sensors'] = field.sensors.all()
        context['logs'] = field.irrigation_logs.order_by('-start_time')[:20]
        context['readings'] = SensorReading.objects.filter(
            sensor__field=field
        ).order_by('-timestamp')[:50] 
        return context
    
def create_schedule(request, pk):
    field = get_object_or_404(Field, pk=pk)

    if request.method == 'POST':
        form = IrrigationScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.field = field
            schedule.status = 'pending'  # default status
            schedule.save()
            messages.success(request, 'Irrigation schedule created successfully!')
            return redirect('irrigation:schedule_list')
    else:
        # you can prefill some defaults if you want
        form = IrrigationScheduleForm(initial={
            'duration_minutes': 30,
            'auto_weather_adjust': True,
            'is_active': True,
            'frequency': 'daily',
        })

    return render(request, 'irrigation/create_schedule.html', {
        'field': field,
        'form': form,
        'fields': Field.objects.all()
    })
class ScheduleListView(ListView):
    model = IrrigationLog
    template_name = 'irrigation/schedule_list.html'
    context_object_name = 'schedules'

    def get_queryset(self):
        return IrrigationLog.objects.filter(status='pending').order_by('start_time')
