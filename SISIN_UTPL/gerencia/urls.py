from django.urls import path
from . import views

app_name = 'gerencia'

urlpatterns = [
    path('dashboard/', views.dashboard_gerencial, name='dashboard_gerencial'),
    path('reportes/', views.reportes_gerencial, name='reportes_gerencial'),
    path('parametros/', views.parametros_gerencial, name='parametros_gerencial'),
    path('usuarios/', views.usuarios_gerencial, name='usuarios_gerencial'),
    path('exportaciones/', views.exportaciones_gerencial, name='exportaciones_gerencial'),
    #path('dashboard/', views.dashboard_gerencial, name='dashboard_gerencial'),
]