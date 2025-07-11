from django import forms
from .models import IrrigationLog

class IrrigationScheduleForm(forms.ModelForm):
    class Meta:
        model = IrrigationLog
        fields = [
            'name',
            'start_time',
            'duration_minutes',
            'frequency',
            'auto_weather_adjust',
            'is_active',
        ]
        widgets = {
            'start_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
            'frequency': forms.Select(choices=[
                ('daily', 'Daily'),
                ('weekly', 'Weekly'),
                ('monthly', 'Monthly'),
                ('custom', 'Custom')
            ])
        }
