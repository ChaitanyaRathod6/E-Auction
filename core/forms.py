from django.contrib.auth.forms import UserCreationForm
from .models import User
from django import forms



from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class UserSignupForm(UserCreationForm):
    class Meta:
        model = User
        fields = [
            'Email',
            'First_name',
            'Last_name',
            'Gender',
            'Mobile_number',
            'Role',
            'password1',
            'password2'
        ]

        widgets = {
            'Email': forms.EmailInput(attrs={
                'class': 'input-style',
                'placeholder': 'Enter your email'
            }),
            'First_name': forms.TextInput(attrs={
                'class': 'input-style',
                'placeholder': 'First name'
            }),
            'Last_name': forms.TextInput(attrs={
                'class': 'input-style',
                'placeholder': 'Last name'
            }),
            'Gender': forms.Select(attrs={
                'class': 'input-style'
            }),
            'Mobile_number': forms.TextInput(attrs={
                'class': 'input-style',
                'placeholder': 'Mobile number'
            }),
            'Role': forms.Select(attrs={
                'class': 'input-style'
            }),
            'password1': forms.PasswordInput(attrs={
                'class': 'input-style',
                'placeholder': 'Create password'
            }),
            'password2': forms.PasswordInput(attrs={
                'class': 'input-style',
                'placeholder': 'Confirm password'
            }),
        }
        

class UserLoginForm(forms.Form):
    Email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all',
            'placeholder': 'Enter your email'
        })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-xl border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-all',
            'placeholder': 'Enter your password'
        })
    )
    