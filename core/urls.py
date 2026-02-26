from django.contrib import admin
from django.urls import path, include
from . import views


urlpatterns = [
    path('signup/', views.UserSignUpViews, name='signup'),
    path('login/', views.UserLoginViews, name='login'),
    path('logout/', views.UserLogoutViews, name='logout'),
]