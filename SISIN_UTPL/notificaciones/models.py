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

    CATEGORIA_CHOICES = [
        ('poliza_vencer', 'Póliza por Vencer'),
        ('siniestro_docs', 'Documentos Incompletos'),
        ('siniestro_plazo', 'Siniestro Fuera de Plazo'),
        ('aseguradora_plazo', 'Aseguradora Fuera de Plazo'),
        ('pago_pendiente', 'Pago Pendiente'),
        ('general', 'General'),
    ]

    titulo = models.CharField(max_length=150)
    mensaje = models.TextField()

    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='info'
    )
    
    categoria = models.CharField(
        max_length=30,
        choices=CATEGORIA_CHOICES,
        default='general'
    )

    # Relación genérica (siniestro, póliza, etc.)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    contenido = GenericForeignKey('content_type', 'object_id')

    destinatario = models.ForeignKey(
        AsesorUTPL,
        on_delete=models.CASCADE,
        related_name='notificaciones'
    )

    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.titulo} - {self.destinatario}"

    def marcar_leida(self):
        """Marca la notificación como leída"""
        self.leida = True
        self.save()


class Alerta(models.Model):
    """
    Registro de actividades/alertas del sistema
    para mostrar en la sección de actividad reciente
    """
    TIPO_ACTIVIDAD_CHOICES = [
        ('siniestro_creado', 'Siniestro Creado'),
        ('siniestro_actualizado', 'Siniestro Actualizado'),
        ('documento_subido', 'Documento Subido'),
        ('estado_cambiado', 'Estado Cambiado'),
        ('poliza_creada', 'Póliza Creada'),
        ('poliza_actualizada', 'Póliza Actualizada'),
        ('notificacion_enviada', 'Notificación Enviada'),
    ]

    tipo_actividad = models.CharField(
        max_length=30,
        choices=TIPO_ACTIVIDAD_CHOICES
    )
    
    descripcion = models.CharField(max_length=255)
    
    # Usuario que realizó la acción
    usuario = models.ForeignKey(
        AsesorUTPL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Relación genérica al objeto relacionado
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    objeto_relacionado = GenericForeignKey('content_type', 'object_id')
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Alerta"
        verbose_name_plural = "Alertas"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.get_tipo_actividad_display()} - {self.descripcion}"