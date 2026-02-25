from django.shortcuts import render

# Create your views here.
def AdminDashboard(request):
    return render(request,"Dashboard/AdminDashboard.html")

def BuyerDashboard(request):
    return render(request,"Dashboard/BuyerDashboard.html")

def SellerDashboard(request):
    return render(request,"Dashboard/SellerDashboard.html")