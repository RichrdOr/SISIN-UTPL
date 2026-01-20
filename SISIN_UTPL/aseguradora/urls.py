from django.urls import path
from siniestros import views as siniestros_views
from . import views

app_name = 'aseguradora'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard_aseguradora'),
    path('bandeja/', views.bandeja_siniestros, name='bandeja_siniestros'), 
    path('detalle/<int:siniestro_id>/', views.detalle_siniestro, name='detalle_siniestro'),
    path('correo/', views.enviar_correo, name='enviar_correo'),
    path('liquidacion/', views.liquidacion, name='liquidacion'),
    path('pago/', views.registrar_pago, name='registrar_pago'),
    path('cerrar/', views.cerrar_siniestro, name='cerrar_siniestro'),
    path('polizas/', views.gestion_polizas, name='gestion_polizas'),
    path('alertas/', views.alertas, name='alertas'),
    path('nuevo/', siniestros_views.crear_siniestro, name='crear_siniestro'),
    path('bandeja_siniestros/', views.bandeja_siniestros, name='bandeja_siniestros'),


]