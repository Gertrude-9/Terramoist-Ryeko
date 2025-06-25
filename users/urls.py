from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    # path('register/farmer/', views.farmer_register, name='farmer_register'),
    # path('register/agronomist/', views.agronomist_register, name='agronomist_register'),
    # path('register/technician/', views.technician_register, name='technician_register'),
    # path('register/admin/', views.admin_register, name='admin_register'),
    path('login/', views.user_login, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
]