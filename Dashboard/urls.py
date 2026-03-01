from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path("AdminDashboard/",views.AdminDashboard,name = "AdminDashboard"),
    path("BuyerDashboard/",views.BuyerDashboard,name = "BuyerDashboard"),
    path("SellerDashboard/",views.SellerDashboard,name = "SellerDashboard"),
    path("privacypolicy/",views.privacypolicy,name = "privacypolicy"),
    path("termsofservice/",views.termsofservice,name = "termsofservice"),   
    path("contactus/",views.ContactUs,name = "ContactUs"),
    path("helpcenter/",views.HelpCenter,name = "HelpCenter"),
    path("security/",views.Security,name = "Security"),
    path("community/",views.Community,name = "Community"),
    path("support/",views.Support,name = "Support"),
    path("aboutus/",views.AboutUs,name = "AboutUs"),
    path("careers/",views.Careers,name = "Careers"),
    path("howitworks/",views.HowItWorks,name = "HowItWorks"),
    
]