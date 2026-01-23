<<<<<<< Updated upstream
from django.urls import path
from .views import *

urlpatterns = [
    path('', ver_polizas, name='ver_polizas'),
    path('crear/', crear_poliza, name='crear_poliza'),
    path('editar/<int:poliza_id>/', editar_poliza, name='editar_poliza'),
    path('eliminar/<int:poliza_id>/', eliminar_poliza, name='eliminar_poliza'),
    path('obtener/<int:poliza_id>/', obtener_poliza, name='obtener_poliza'),
    path('descargar/<int:poliza_id>/', descargar_pdf, name='descargar_pdf'),
    path('exportar-excel/', exportar_excel, name='exportar_excel'),
    path('renovar-vencidas/', renovar_vencidas, name='renovar_vencidas'),
    path('crear_old/', crear_poliza_old, name='crear_poliza_old'),
=======
from django.urls import path
from .views import *

# Namespace for reverse URLs
app_name = 'polizas'

urlpatterns = [
    path('', ver_polizas, name='ver_polizas'),
    path('nueva/', formulario_crear_poliza, name='formulario_crear_poliza'),  # Formulario GET
    path('crear/', crear_poliza, name='crear_poliza'),  # POST para guardar
    path('editar/<int:poliza_id>/', formulario_editar_poliza, name='formulario_editar_poliza'),  # GET para mostrar formulario
    path('actualizar/<int:poliza_id>/', editar_poliza, name='editar_poliza'),  # POST para actualizar
    path('eliminar/<int:poliza_id>/', eliminar_poliza, name='eliminar_poliza'),
    path('obtener/<int:poliza_id>/', obtener_poliza, name='obtener_poliza'),
    path('descargar/<int:poliza_id>/', descargar_pdf, name='descargar_pdf'),
    path('exportar-excel/', exportar_excel, name='exportar_excel'),
    path('renovar-vencidas/', renovar_vencidas, name='renovar_vencidas'),
    path('<int:poliza_id>/detalle/', ver_poliza_detalle, name='detalle_poliza'),
>>>>>>> Stashed changes
]