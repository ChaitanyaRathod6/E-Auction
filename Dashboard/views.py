from django.shortcuts import render

from .decorators import role_required

# Create your views here.
@role_required(allowed_roles=['Admin'])
def AdminDashboard(request):
    return render(request,"Dashboard/AdminDashboard.html")

@role_required(allowed_roles=['Buyer'])
def BuyerDashboard(request):
    return render(request,"Dashboard/BuyerDashboard.html")

@role_required(allowed_roles=['Seller'])
def SellerDashboard(request):
    return render(request,"Dashboard/SellerDashboard.html")

def  privacypolicy(request):
    return render(request,"Dashboard/privacypolicy.html")

def  termsofservice(request):
    return render(request,"Dashboard/termsofservice.html")

def ContactUs(request): 
    return render(request,"Dashboard/contactus.html")

def HelpCenter(request):
    return render(request,"Dashboard/helpcenter.html")

def Security(request):
    return render(request,"Dashboard/security.html")  
  
def Community(request):
    return render(request,"Dashboard/community.html") 
   
def Support(request):
    return render(request,"Dashboard/support.html")    