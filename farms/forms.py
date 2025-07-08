from django import forms
from farms.models import Farm

class FarmForm(forms.ModelForm):
    class Meta:
        model = Farm
        fields = ['name', 'owner', 'location', 'total_fields', 'total_area']  # Removed description, added new fields
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter farm name'
            }),
            'owner': forms.Select(attrs={
                'class': 'form-control'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter farm location'
            }),
            'total_fields': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Number of fields',
                'min': 0  # Ensures non-negative values
            }),
            'total_area': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Total area in acres',
                'min': 0,
                'step': '0.01'  # Allows decimal values with 2 decimal places
            })
        }