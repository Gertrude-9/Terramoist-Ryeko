from django import forms
from farms.models import Farm
from fields.models import Field
from sensors.models import Sensor

class SensorForm(forms.ModelForm):
    # Add farm as a separate field for the dropdown
    farm = forms.ModelChoiceField(
        queryset=Farm.objects.none(),
        empty_label="Select a farm",
        required=True,
        widget=forms.Select(attrs={'id': 'farm'})
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        try:
            if self.user and self.user.is_authenticated:
                user_farms = Farm.objects.filter(owner=self.user)
                self.fields['farm'].queryset = user_farms
                # Initially set field queryset to none - will be populated via JavaScript
                self.fields['field'].queryset = Field.objects.none()
                # Set field widget attributes
                self.fields['field'].widget.attrs.update({
                    'id': 'field',
                    'disabled': True
                })
            else:
                self.fields['farm'].queryset = Farm.objects.none()
                self.fields['field'].queryset = Field.objects.none()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error setting queryset in SensorForm: {e}")
            self.fields['farm'].queryset = Farm.objects.none()
            self.fields['field'].queryset = Field.objects.none()

    class Meta:
        model = Sensor
        fields = [
            'farm',  # Add farm to the fields list
            'field',
            'name',
            'device_id',
            'latitude',
            'longitude',
            'depth',
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
            'latitude': forms.NumberInput(attrs={'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'step': '0.000001'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }