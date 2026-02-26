from django.shortcuts import render,redirect
from .forms import UserSignupForm,UserLoginForm
from django.contrib.auth import authenticate, login,logout

# Create your views here.

def UserSignUpViews(request):
    if request.method == 'POST':
        form = UserSignupForm(request.POST or None)
        if form.is_valid():
            form.save()
            return redirect("login")
        else:
            return render(request, 'core/signup.html', {'form': form})
    else:
        form = UserSignupForm()
    return render(request, 'core/signup.html', {'form': form})
   

def  UserLoginViews(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST or None)
        if form.is_valid():
            email = form.cleaned_data.get('Email')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user :
                login(request, user)
                if user.Role == 'Admin':
                    return redirect('AdminDashboard')  # Replace with your admin dashboard URL name
                elif user.Role == 'Seller':
                    return redirect('SellerDashboard')  # Replace with your seller dashboard URL name
                elif user.Role == 'Buyer':
                    return redirect('BuyerDashboard')  # Replace with your buyer dashboard URL name
            else:
                return render(request, 'core/login.html', {'form': form, 'error': 'Invalid email or password'})
        return render(request, 'core/login.html', {'form': form})
    else:
            form = UserLoginForm()
            return render(request, 'core/login.html', {'form': form})
    


def UserLogoutViews(request):
    logout(request)
    return redirect('login')        
   