"""
Core URL configuration.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('pending-approval/', views.pending_approval, name='pending_approval'),
]
