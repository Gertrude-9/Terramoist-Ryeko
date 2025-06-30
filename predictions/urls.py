# urls.py
from django.urls import path
from . import views

app_name = 'predictions'

urlpatterns = [
    # Dashboard views
    path('ai-insights/', views.ai_insights_dashboard, name='ai_insights_dashboard'),
    path('sensor/<str:sensor_id>/insights/', views.sensor_insights, name='sensor_insights'),
    path('ai-preferences/', views.ai_preferences, name='ai_preferences'),
    
    # API endpoints
    path('api/insights/', views.insights_api, name='insights_api'),
    path('api/insights/summary/', views.insights_summary_api, name='insights_summary_api'),
    path('api/insight/<int:insight_id>/', views.insight_detail_api, name='insight_detail_api'),
    path('api/sensor/<str:sensor_id>/generate-insights/', views.generate_insights_api, name='generate_insights_api'),
    path('api/sensor/<str:sensor_id>/moisture-trends/', views.moisture_trends_api, name='moisture_trends_api'),
    
    # Insight actions
    path('api/insight/<int:insight_id>/mark-read/', views.mark_insight_read, name='mark_insight_read'),
    path('api/insight/<int:insight_id>/dismiss/', views.dismiss_insight, name='dismiss_insight'),
]