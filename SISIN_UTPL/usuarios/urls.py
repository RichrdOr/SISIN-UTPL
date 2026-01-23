from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('dashboard/gerente/', views.dashboard_gerente, name='dashboard_gerente'),
    path('dashboard/asesor/', views.dashboard_asesor, name='dashboard_asesor'),
    path('asegurado/', views.inicio_asegurado, name='inicio_asegurado'),
]