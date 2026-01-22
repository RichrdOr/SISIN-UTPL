from django.urls import path
from .views import *

urlpatterns = [
    path('', ver_polizas, name='ver_polizas'),
    path('nueva/', formulario_crear_poliza, name='formulario_crear_poliza'),  # Formulario GET
    path('crear/', crear_poliza, name='crear_poliza'),  # POST para guardar
    path('editar/<int:poliza_id>/', editar_poliza, name='editar_poliza'),
    path('eliminar/<int:poliza_id>/', eliminar_poliza, name='eliminar_poliza'),
    path('obtener/<int:poliza_id>/', obtener_poliza, name='obtener_poliza'),
    path('descargar/<int:poliza_id>/', descargar_pdf, name='descargar_pdf'),
    path('exportar-excel/', exportar_excel, name='exportar_excel'),
    path('renovar-vencidas/', renovar_vencidas, name='renovar_vencidas'),
    path('crear_old/', crear_poliza_old, name='crear_poliza_old'),
]