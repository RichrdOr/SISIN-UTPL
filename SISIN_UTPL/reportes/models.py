 
# solooo Reportes, documentos y notificaciones

from django.db import models
from siniestros.models import Siniestro
from polizas.models import BienAsegurado
from usuarios.models import Gerente


class Documento(models.Model):
    autor = models.CharField(max_length=100)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    obligatorio = models.BooleanField()
    ruta_archivo = models.CharField(max_length=255)
    tipo_doc = models.CharField(max_length=50)

    siniestro = models.ForeignKey(Siniestro, on_delete=models.CASCADE)


class Notificacion(models.Model):
    descripcion = models.CharField(max_length=255)
    tipo_notificacion = models.CharField(max_length=50)

    siniestro = models.ForeignKey(Siniestro, on_delete=models.CASCADE)


class Reporte(models.Model):
    contenido = models.TextField()
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    tipo_reporte = models.CharField(max_length=50)

    gerente_autor = models.ForeignKey(Gerente, on_delete=models.SET_NULL, null=True)
    siniestro = models.ForeignKey(Siniestro, on_delete=models.SET_NULL, null=True)
    bien = models.ForeignKey(BienAsegurado, on_delete=models.SET_NULL, null=True)
