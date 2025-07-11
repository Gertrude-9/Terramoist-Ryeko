# urls.py
from . import views
from django.urls import path
from predictions.views import (
    HomeView,
    IrrigationInsightsView,
    PredictionView,
    PredictionAPIView,
    InsightsAPIView
)

app_name = 'predictions'

urlpatterns = [
    path('', HomeView.as_view(), name='prediction_home'),
    path('ai-insights/', views.AIInsightsView.as_view(), name='ai_insights'),
    path('field/<int:field_id>/insights/', IrrigationInsightsView.as_view(), name='field_insights'),
    path('field/<int:field_id>/predict/', PredictionView.as_view(), name='prediction_view'),
    path('api/predict/', PredictionAPIView.as_view(), name='prediction_api'),
    path('api/field/<int:field_id>/insights/', InsightsAPIView.as_view(), name='insights_api'),
]