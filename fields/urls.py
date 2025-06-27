# fields/urls.py
from django.urls import path
from django.contrib.gis import admin
from .views import (
    FieldValidationAPI,
    FieldZoneDivisionAPI,
    FieldWaterRequirementsAPI,
    FieldSensorCoverageAPI
)

urlpatterns = [
    path('validate/', FieldValidationAPI.as_view()),
    path('<int:field_id>/zones/', FieldZoneDivisionAPI.as_view()),
    path('<int:field_id>/water-needs/', FieldWaterRequirementsAPI.as_view()),
    path('<int:field_id>/sensor-coverage/', FieldSensorCoverageAPI.as_view()),
    path('admin/', admin.site.urls),
]