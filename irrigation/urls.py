# irrigation/urls.py
from django.urls import path
from . import views

app_name = 'irrigation'

urlpatterns = [
    path('', views.irrigation_dashboard, name='dashboard'),
    path('schedules/', views.schedule_list, name='schedule_list'),
    path('schedules/create/', views.create_schedule, name='create_schedule'),
    path('immediate/', views.start_immediate_irrigation, name='immediate_irrigation'),
    path('history/', views.historical_data, name='historical_data'),
    path('auto-schedule/', views.auto_schedule_view, name='auto_schedule'),
    path('auto-schedule/generate/', views.generate_schedule, name='generate_schedule'),
    path('auto-schedule/confirm/<int:schedule_id>/', views.confirm_schedule, name='confirm_schedule'),
    path('auto-schedule/weather/', views.auto_schedule_weather, name='auto_schedule_weather'),
    # path('api/weather/', views.get_weather_data, name='get_weather_data'),
]