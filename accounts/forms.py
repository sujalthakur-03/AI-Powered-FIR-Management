from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import PoliceUser

class PoliceUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = PoliceUser
        fields = ('username', 'first_name', 'last_name', 'email', 'role', 
                 'jurisdiction_area', 'badge_number', 'phone_number')

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
