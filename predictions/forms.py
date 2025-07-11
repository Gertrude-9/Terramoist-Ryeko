# forms.py
from django import forms
from predictions.models import SensorData

class SensorDataForm(forms.ModelForm):
    class Meta:
        model = SensorData
        fields = ['soil_moisture', 'temperature', 'humidity']
        widgets = {
            'soil_moisture': forms.NumberInput(attrs={
                'min': 0,
                'max': 100,
                'step': 0.1,
                'class': 'form-control'
            }),
            'temperature': forms.NumberInput(attrs={
                'step': 0.1,
                'class': 'form-control'
            }),
            'humidity': forms.NumberInput(attrs={
                'min': 0,
                'max': 100,
                'step': 0.1,
                'class': 'form-control'
            }),
        }