from django.urls import path
from . import views

app_name = 'farms'

urlpatterns = [
    path('', views.farm_list, name='farm_list'),
    path('<int:farm_id>/', views.farm_detail, name='farm_detail'),
    path('create/', views.create_farm, name='create_farm'),
   
]