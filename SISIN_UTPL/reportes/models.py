 
# solooo Reportes, documentos y notificaciones

from django.db import models
from django.contrib.auth.models import User

class Reporte(models.Model):
    TIPO_CHOICES = [
        ('polizas', 'Pólizas'),
        ('siniestros', 'Siniestros'),
        ('usuarios', 'Usuarios'),
        ('financiero', 'Financiero'),
    ]

    titulo = models.CharField(max_length=100, verbose_name="Título")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    fecha_generacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Generación")
    generado_por = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Generado Por")
    archivo = models.FileField(upload_to='reportes/', null=True, blank=True, verbose_name="Archivo")

    class Meta:
        verbose_name = "Reporte"
        verbose_name_plural = "Reportes"

    def __str__(self):
        return f"{self.titulo} - {self.fecha_generacion.date()}"
