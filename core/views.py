from django.shortcuts import render,redirect
from .forms import UserSignupForm,UserLoginForm
from django.contrib.auth import authenticate, login,logout
from django.core.mail import send_mail
from django.conf import settings      
from Dashboard.models import ActivityLog
# Create your views here.
def log_activity(user, action):
    ActivityLog.objects.create(user=user, action=action)

def UserSignUpViews(request):
    if request.method == 'POST':
        form = UserSignupForm(request.POST or None)
        if form.is_valid():
            user = form.save(commit=False)
            if user.Role not in ['Buyer', 'Seller']:
                user.Role = 'Buyer'
            user.save()
            
            # Create profile based on role
            from Dashboard.models import Buyer, Seller
            if user.Role == 'Buyer':
                Buyer.objects.get_or_create(user=user)
            elif user.Role == 'Seller':
                Seller.objects.get_or_create(user=user)

            try:
                email = form.cleaned_data['Email']
                send_mail(
                    subject='Welcome to E-Auction',
                    message='Thank you for signing up for E-Auction!',
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[email]
                )
            except Exception as e:
                print("Email error:", e)  # Don't block signup if email fails

            return redirect("login")
        else:
            print("FORM ERRORS:", form.errors)  # ← check terminal for errors
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
                log_activity(user, f"Logged in")
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
   