from django.urls import path
from . import views

app_name = 'irrigation'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('field/<int:pk>/', views.FieldDetailView.as_view(), name='field_detail'),
    path('irrigate/<int:field_id>/', views.manual_irrigation, name='manual_irrigation'),
    path('schedule/create/<int:pk>/', views.create_schedule, name='create_schedule'),
    path('schedule/', views.ScheduleListView.as_view(), name='schedule_list')

]