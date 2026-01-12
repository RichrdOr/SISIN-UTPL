from django.urls import path
from . import views

urlpatterns = [
    path('asegurado/', views.inicio_asegurado, name='inicio_asegurado'),
    path('asegurado/generarSiniestro/', views.generarSiniestro, name='generar_siniestro'),
    path('asegurado/detalleSiniestro/', views.detalleSiniestro, name='detalle_siniestro'),
]