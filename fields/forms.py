from django import forms
from .models import Field, Sensor

class FieldForm(forms.ModelForm):
    class Meta:
        model = Field
        fields = ['name', 'boundary', 'crop_type', 'planting_date', 'harvest_date', 'area', 'soil_type']
        widgets = {
            'planting_date': forms.DateInput(attrs={'type': 'date'}),
            'harvest_date': forms.DateInput(attrs={'type': 'date'}),
        }

class SensorForm(forms.ModelForm):
    class Meta:
        model = Sensor
        fields = ['field', 'name', 'location', 'sensor_type', 'installation_date', 'last_maintenance']
        widgets = {
            'installation_date': forms.DateInput(attrs={'type': 'date'}),
            'last_maintenance': forms.DateInput(attrs={'type': 'date'}),
        }