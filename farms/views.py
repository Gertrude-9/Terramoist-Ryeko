
from fields.models import Farm, Field, Sensor
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from farms.forms import FarmForm  # We'll create this next

def farm_list(request):
    """List all farms"""
    farms = Farm.objects.all().prefetch_related('fields')
    context = {
        'farms': farms,
    }
    return render(request, 'farms/farm_list.html', context)

def farm_detail(request, farm_id):
    """Show details of a specific farm with its fields"""
    farm = get_object_or_404(Farm, id=farm_id)
    fields = farm.fields.all().prefetch_related('sensors')
    
    # Calculate total area
    total_area = sum(field.area for field in fields if field.area)
    
    context = {
        'farm': farm,
        'fields': fields,
        'total_area': total_area,
        'field_count': fields.count(),
    }
    return render(request, 'farms/farm_detail.html', context)

def field_detail(request, field_id):
    """Show details of a specific field with its sensors"""
    field = get_object_or_404(Field, id=field_id)
    sensors = field.sensors.all()
    
    context = {
        'field': field,
        'sensors': sensors,
    }
    return render(request, 'fields/field_detail.html', context)


@login_required
def create_farm(request):
    if request.method == 'POST':
        form = FarmForm(request.POST)
        if form.is_valid():
            farm = form.save(commit=False)
            farm.owner = request.user
            farm.save()
            messages.success(request, 'Farm created successfully!')
            # Use the namespaced URL in redirect
            return redirect('farms:farm_list')
    else:
        form = FarmForm()
    
    return render(request, 'farms/create_farm.html', {'form': form})
@login_required
def delete_farm(request, farm_id):
    farm = get_object_or_404(Farm, id=farm_id, owner=request.user)
    
    if request.method == 'POST':
        farm_name = farm.name
        farm.delete()
        messages.success(request, f'Farm "{farm_name}" was deleted successfully!')
        return redirect('farm_list')
    
    return render(request, 'farms/delete_farm.html', {'farm': farm})