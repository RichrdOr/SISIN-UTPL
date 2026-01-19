from django.urls import path
from . import views

urlpatterns = [
    path('asegurado/', views.inicio_asegurado, name='inicio_asegurado'),
]