from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User

class UserRegisterForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=User.USER_ROLES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Account Type'
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'password1', 'password2',
                 'first_name', 'last_name', 'phone_number']

# Add these admin forms at the bottom of forms.py
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'role')

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'role')