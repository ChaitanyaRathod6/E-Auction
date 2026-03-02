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
    path("create_auction/",views.create_auction,name = "create_auction"),
    path("auction_list/",views.auction_list,name = "auction_list"),
    path("auction/<int:pk>/",views.auction_detail,name = "auction_detail"),
    path("seller_profile/",views.seller_profile,name = "seller_profile"),
    path("buyer_profile/",views.buyer_profile,name = "buyer_profile"),
    path("admin_profile/",views.admin_profile,name = "admin_profile"),
    path("category_management/",views.category_management,name = "category_management"),
]