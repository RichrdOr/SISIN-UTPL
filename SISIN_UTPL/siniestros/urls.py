
# siniestros/urls.py

from django.urls import path
from .views import (
    crear_siniestro, 
    detalle_siniestro, 
    dashboard_siniestros, 
    dashboard_asesora, 
    siniestros_asesora,
    enviar_a_revision,
    aprobar_siniestro
)

urlpatterns = [
    # Dashboard mejorado de asesora
    path('dashboard/asesora/', dashboard_asesora, name='dashboard_asesora'),
    
    # O si prefieres que sea solo 'dashboard/'
    # path('dashboard/', dashboard_asesora, name='dashboard_asesora'),
    
    # Detalle de siniestro
    path('siniestro/<int:siniestro_id>/', detalle_siniestro, name='detalle_siniestro'),
    
    # Otras vistas que ya tenías
    path('crear/', crear_siniestro, name='crear_siniestro'),
    path('dashboard/siniestros/', dashboard_siniestros, name='dashboard_siniestros'),
    path('siniestros/asesora/', siniestros_asesora, name='siniestros_asesora'),
    path('siniestro/<int:siniestro_id>/revisar/', enviar_a_revision, name='enviar_a_revision'),
    path('siniestro/<int:siniestro_id>/aprobar/', aprobar_siniestro, name='aprobar_siniestro'),


]