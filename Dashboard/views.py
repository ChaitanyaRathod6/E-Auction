from django.shortcuts import render

# Create your views here.
def AdminDashboard(request):
    return render(request,"Dashboard/AdminDashboard.html")

def BuyerDashboard(request):
    return render(request,"Dashboard/BuyerDashboard.html")

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