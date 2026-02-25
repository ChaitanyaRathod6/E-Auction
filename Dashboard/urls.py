from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path("AdminDashboard/",views.AdminDashboard,name = "AdminDashboard"),
    path("BuyerDashboard/",views.AdminDashboard,name = "BuyerDashboard"),
    path("SellerDashboard/",views.AdminDashboard,name = "SellerDashboard"),
]