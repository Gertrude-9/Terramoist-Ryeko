from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegisterForm
from django.core import serializers
from sensors.models import Sensor 
from farms.models import Farm  # make sure you have imported your Farm model

def home(request):
    """Home page view"""
    return render(request, 'users/home.html')

def register(request):
    """Registration view"""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('users:dashboard')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})

def user_login(request):
    """Login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('users:dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'users/login.html')

@login_required
def dashboard(request):
    """Dashboard view showing farms and fields"""
    farms = Farm.objects.prefetch_related('fields').all()

    # Build a list of farms with nested fields
    farms_data = []
    for farm in farms:
        farm_data = {
            'id': farm.id,
            'name': farm.name,
            'fields': [{'id': field.id, 'name': field.name} for field in farm.fields.all()]
        }
        farms_data.append(farm_data)

    context = {
        'user': request.user,
        'farms': farms,  # keep original queryset if needed for other parts
        'farms_data': farms_data,  # JSON-ready list of farms + fields
        'alerts': [
            {'type': 'danger', 'message': 'CRITICAL: Low moisture in Field A (35%)'},
            {'type': 'warning', 'message': 'WARNING: Sensor offline in Field D'},
            {'type': 'primary', 'message': 'INFO: Irrigation completed in Field E'},
        ],
        'predictions': [
            {'type': 'success', 'message': 'Next 3 days: Optimal conditions for growth'},
            {'type': 'info', 'message': 'Irrigation recommendation: Water Field B tomorrow at 6AM'},
            {'type': 'warning', 'message': 'Pest alert: Increased risk of aphids in Field C'},
        ],
        'environment_data': {
            'temperature': {'value': 24, 'percent': 75},
            'humidity': {'value': 65, 'percent': 65},
            'rainfall': {'value': 5, 'percent': 30},
        },
        'moisture_data': {
            'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            'field_a': [65, 59, 70, 68, 62, 55, 60],
            'field_b': [55, 50, 62, 60, 58, 52, 57],
        }
    }
    return render(request, 'users/dashboard.html', context)


@login_required
def fields_view(request):
    return render(request, 'users/fields.html')

@login_required
def irrigation_view(request):
    return render(request, 'users/irrigation.html')

@login_required
def ai_insights_view(request):
    return render(request, 'users/ai_insights.html')

@login_required
def alerts_view(request):
    return render(request, 'users/alerts.html')


 # adjust the import to your actual app name

# @login_required
# def sensors_view(request):
#     """View to display all sensors"""
#     sensors = Sensor.objects.select_related('field').all()

#     context = {
#         'sensors': sensors,
#     }
#     return render(request, 'sensors/sensor_list.html', context)

