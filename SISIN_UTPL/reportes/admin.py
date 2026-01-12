from django.contrib import admin
from .models import Documento, Notificacion, Reporte
# Register your models here.

admin.site.register(Documento)
admin.site.register(Notificacion)
admin.site.register(Reporte)