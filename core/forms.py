from django.contrib.auth.forms import UserCreationForm
from .models import User
from django import forms



from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class UserSignupForm(UserCreationForm):
    # Only define fields that need custom widgets
    # DO NOT redefine password1/password2 here if defined in Meta
    
    Gender = forms.ChoiceField(
        choices=[('', 'Select gender')] + list(User.choice),
        widget=forms.Select(attrs={
            'class': 'input-style rounded-full px-5 w-full py-3 border border-slate-200 bg-slate-50'
        })
    )
    
    Role = forms.ChoiceField(
        choices=[('', 'Select role'), ('Buyer', 'Buyer'), ('Seller', 'Seller')],
        widget=forms.Select(attrs={
            'class': 'input-style rounded-full px-5 w-full py-3 border border-slate-200 bg-slate-50'
        })
    )

    class Meta:
        model = User
        fields = [
            'Email', 'First_name', 'Last_name',
            'Gender', 'Mobile_number', 'Role',
            'password1', 'password2'
        ]
        widgets = {
            'Email': forms.EmailInput(attrs={
                'class': 'input-style rounded-full px-5 w-full py-3 border border-slate-200 bg-slate-50',
                'placeholder': 'Enter your email'
            }),
            'First_name': forms.TextInput(attrs={
                'class': 'input-style rounded-full px-5 w-full py-3 border border-slate-200 bg-slate-50',
                'placeholder': 'First name'
            }),
            'Last_name': forms.TextInput(attrs={
                'class': 'input-style rounded-full px-5 w-full py-3 border border-slate-200 bg-slate-50',
                'placeholder': 'Last name'
            }),
            'Mobile_number': forms.TextInput(attrs={
                'class': 'input-style rounded-full px-5 w-full py-3 border border-slate-200 bg-slate-50',
                'placeholder': 'Mobile number'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Fix password fields here — single place, no conflict
        self.fields['password1'].widget = forms.PasswordInput(attrs={
            'class': 'input-style rounded-full px-5 w-full py-3 border border-slate-200 bg-slate-50',
            'placeholder': 'Create password'
        })
        self.fields['password2'].widget = forms.PasswordInput(attrs={
            'class': 'input-style rounded-full px-5 w-full py-3 border border-slate-200 bg-slate-50',
            'placeholder': 'Confirm password'
        })

class UserLoginForm(forms.Form):
    Email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'input-style rounded-full px-5 w-full py-3 border border-slate-200 bg-slate-50 text-slate-900 text-sm',
            'placeholder': 'Enter your email'
        })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input-style rounded-full px-5 w-full py-3 border border-slate-200 bg-slate-50 text-slate-900 text-sm',
            'placeholder': 'Enter your password'
        })
    )
    