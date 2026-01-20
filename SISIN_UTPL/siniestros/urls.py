# siniestros/urls.py

from django.urls import path
from .views import (
    crear_siniestro, 
    detalle_siniestro, 
    dashboard_siniestros,
    dashboard_asesora,
    siniestros_asesora,
    enviar_a_revision,
    aprobar_siniestro,
    obtener_ramos_poliza,
    exportar_siniestros_excel,
    # Nuevas vistas para transiciones de estado
    marcar_docs_incompletos,
    confirmar_documentos,
    enviar_aseguradora,
    marcar_revision,
    aprobar_siniestro_modal,
    rechazar_siniestro,
    liquidar_siniestro,
    registrar_pago,
    cerrar_siniestro,
)

urlpatterns = [
    path('dashboard/', dashboard_asesora, name='dashboard_asesora'), 
    
    path('siniestro/<int:siniestro_id>/', detalle_siniestro, name='detalle_siniestro'),
    path('crear/', crear_siniestro, name='crear_siniestro'),
    path('siniestros/asesora/', siniestros_asesora, name='siniestros_asesora'),
    path('siniestro/<int:siniestro_id>/revisar/', enviar_a_revision, name='enviar_a_revision'),
    path('siniestro/<int:siniestro_id>/aprobar-simple/', aprobar_siniestro, name='aprobar_siniestro_simple'),
    path('siniestros/exportar/', exportar_siniestros_excel, name='exportar_siniestros_excel'),
    
    # Rutas para transiciones de estado (modals)
    path('siniestro/<int:siniestro_id>/docs-incompletos/', marcar_docs_incompletos, name='marcar_docs_incompletos'),
    path('siniestro/<int:siniestro_id>/confirmar-docs/', confirmar_documentos, name='confirmar_documentos'),
    path('siniestro/<int:siniestro_id>/enviar-aseguradora/', enviar_aseguradora, name='enviar_aseguradora'),
    path('siniestro/<int:siniestro_id>/marcar-revision/', marcar_revision, name='marcar_revision'),
    path('siniestro/<int:siniestro_id>/aprobar/', aprobar_siniestro_modal, name='aprobar_siniestro'),
    path('siniestro/<int:siniestro_id>/rechazar/', rechazar_siniestro, name='rechazar_siniestro'),
    path('siniestro/<int:siniestro_id>/liquidar/', liquidar_siniestro, name='liquidar_siniestro'),
    path('siniestro/<int:siniestro_id>/registrar-pago/', registrar_pago, name='registrar_pago'),
    path('siniestro/<int:siniestro_id>/cerrar/', cerrar_siniestro, name='cerrar_siniestro'),
    
    # Rutas API
    path('api/ramos/<int:poliza_id>/', obtener_ramos_poliza, name='obtener_ramos_poliza'),
]