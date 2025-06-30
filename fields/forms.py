# fields/forms.py

from django import forms
from .models import Field, Sensor, SensorType, Farm # Import all necessary models
from django.contrib.auth import get_user_model

User = get_user_model() # Get the active user model

class FieldCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # Pop the 'user' argument if it was passed
        self.user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)
        
        # If a user is provided, filter the 'farm' queryset
        if self.user:
            self.fields['farm'].queryset = Farm.objects.filter(owner=self.user)
        
        # Optional: Set initial farm if user has only one farm
        if self.user and self.fields['farm'].queryset.count() == 1:
            self.fields['farm'].initial = self.fields['farm'].queryset.first()


    class Meta:
        model = Field
        fields = [
            'farm',
            'name',
            'latitude',
            'longitude',
            'area',
            'crop_type',
            'soil_type',
            'description',
            'irrigation_system',
            'is_active',
            'planting_date',
            'geometry',
        ]
        widgets = {
            'planting_date': forms.DateInput(attrs={'type': 'date'}),
        }


class SensorForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        try:
            if self.user and self.user.is_authenticated:
                user_farms = Farm.objects.filter(owner=self.user)
                self.fields['field'].queryset = Field.objects.filter(farm__in=user_farms)
            else:
                self.fields['field'].queryset = Field.objects.none()
        except Exception as e:
            # Log the error if needed
            import logging
            logging.getLogger(__name__).error(f"Error setting queryset in SensorForm: {e}")
            # Fallback to empty queryset to avoid template crash
            self.fields['field'].queryset = Field.objects.none()

    class Meta:
        model = Sensor
        fields = [
            'field',
            'name',
            'sensor_type',
            'latitude',
            'longitude',
            'depth',
            'is_active',
            # 'installation_date', # Removed as it's auto_now_add=True and non-editable
            'device_id',
            'status',
            'description',
            'calibration_slope',
            'calibration_offset',
            'last_calibration',
            'reading_frequency',
            'battery_level',
            'min_threshold',
            'max_threshold',
        ]
        widgets = {
            'last_calibration': forms.DateInput(attrs={'type': 'date'}),
            # 'installation_date': forms.DateInput(attrs={'type': 'date'}), # No longer needed
        }
