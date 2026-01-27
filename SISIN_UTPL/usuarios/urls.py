from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # path('asegurado/', views.inicio_asegurado, name='inicio_asegurado'),
    path('login/', auth_views.LoginView.as_view(
        template_name='usuarios/login.html',
        redirect_authenticated_user=True  # Si ya está logueado, lo manda directo al home
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('inicio/', views.redireccion_inicial, name='redireccion_inicial'),
    path('dashboard/asesora/', views.dashboard_asesora, name='dashboard_asesora'),
    path('dashboard/gerente/', views.dashboard_gerente, name='dashboard_gerente'),
]