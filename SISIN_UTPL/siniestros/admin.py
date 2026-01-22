from django.contrib import admin
from .models import (
    Siniestro,
    Broker,
    DocumentoSiniestro,
    RoboSiniestro,
    HistorialEstado
)


@admin.register(Siniestro)
class SiniestroAdmin(admin.ModelAdmin):
    list_display = ['numero_siniestro', 'poliza', 'estado', 'tipo_evento', 'fecha_reporte', 'monto_reclamado']
    list_filter = ['estado', 'tipo_evento', 'fecha_reporte']
    search_fields = ['numero_siniestro', 'poliza__numero_poliza', 'reclamante_nombre']
    date_hierarchy = 'fecha_reporte'
    readonly_fields = ['numero_siniestro', 'fecha_reporte', 'tiempo_resolucion_dias']


@admin.register(DocumentoSiniestro)
class DocumentoSiniestroAdmin(admin.ModelAdmin):
    list_display = ['siniestro', 'tipo', 'fecha_subida']
    list_filter = ['tipo', 'fecha_subida']
    search_fields = ['siniestro__numero_siniestro']


@admin.register(RoboSiniestro)
class RoboSiniestroAdmin(admin.ModelAdmin):
    list_display = ['siniestro', 'denuncia_policial', 'fiscalia', 'fecha_denuncia']
    search_fields = ['siniestro__numero_siniestro', 'denuncia_policial']


@admin.register(HistorialEstado)
class HistorialEstadoAdmin(admin.ModelAdmin):
    list_display = ['siniestro', 'estado_anterior', 'estado_nuevo', 'fecha_cambio', 'usuario']
    list_filter = ['estado_nuevo', 'fecha_cambio']
    search_fields = ['siniestro__numero_siniestro', 'usuario']
    date_hierarchy = 'fecha_cambio'


@admin.register(Broker)
class BrokerAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'correo', 'telefono', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre', 'correo']
