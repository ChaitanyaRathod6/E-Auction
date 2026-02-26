from django.contrib.auth.forms import UserCreationForm
from .models import User
from django import forms



class UserSignupForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['Email', 'First_name', 'Last_name', 'Gender', 'Mobile_number', 'Role', 'password1', 'password2']
        widgets = {
            "Gender": forms.Select(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),  
        }
        
class UserLoginForm(forms.Form):
    First_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    Last_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    Email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    