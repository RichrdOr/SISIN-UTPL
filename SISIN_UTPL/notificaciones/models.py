from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from usuarios.models import AsesorUTPL

class Notificacion(models.Model):
    TIPO_CHOICES = [
        ('info', 'Información'),
        ('alerta', 'Alerta'),
        ('critica', 'Crítica'),
    ]

    titulo = models.CharField(max_length=150)
    mensaje = models.TextField()

    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='info'
    )

    # Relación genérica (siniestro, póliza, pagaré, etc.)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE
    )
    object_id = models.PositiveIntegerField()
    contenido = GenericForeignKey('content_type', 'object_id')

    destinatario = models.ForeignKey(
        AsesorUTPL,
        on_delete=models.CASCADE
    )

    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"

    def __str__(self):
        return self.titulo
