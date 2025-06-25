from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegisterForm

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
            return redirect('dashboard')
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
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'users/login.html')

@login_required
def dashboard(request):
    """Dashboard view for all logged-in users"""
    return render(request, 'users/dashboard.html', {'user': request.user})

@login_required
def dashboard(request):
    # Sample data - replace with actual data from your models
    context = {
        'user': request.user,
        'soil_moisture': 65,
        'temperature': 24,
        'active_fields': '5/8',
        'alerts_count': 3,
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

