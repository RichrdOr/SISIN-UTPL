from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from siniestros.models import Siniestro, DocumentoSiniestro, HistorialEstado
from polizas.models import Poliza
from .models import Alerta, Notificacion
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Notificacion)
def enviar_email_notificacion(sender, instance, created, **kwargs):
    """
    Envía un correo cuando se crea una notificación crítica o alerta
    """
    if created and instance.tipo in ['critica', 'alerta']:
        try:
            # Importar aquí para evitar circular imports
            from .views import enviar_correo_notificacion
            enviar_correo_notificacion(instance)
            logger.info(f"Correo enviado para notificación {instance.id}")
        except Exception as e:
            logger.error(f"Error al enviar correo para notificación {instance.id}: {e}")


@receiver(post_save, sender=Siniestro)
def crear_alerta_siniestro(sender, instance, created, **kwargs):
    """Crea una alerta cuando se crea o actualiza un siniestro"""
    if created:
        Alerta.objects.create(
            tipo_actividad='siniestro_creado',
            descripcion=f'Nuevo siniestro {instance.numero_siniestro} creado',
            usuario=instance.asesor_asignado,
            content_type=ContentType.objects.get_for_model(Siniestro),
            object_id=instance.id
        )
    else:
        Alerta.objects.create(
            tipo_actividad='siniestro_actualizado',
            descripcion=f'Siniestro {instance.numero_siniestro} actualizado',
            usuario=instance.asesor_asignado,
            content_type=ContentType.objects.get_for_model(Siniestro),
            object_id=instance.id
        )


@receiver(post_save, sender=DocumentoSiniestro)
def crear_alerta_documento(sender, instance, created, **kwargs):
    """Crea una alerta cuando se sube un documento"""
    if created:
        Alerta.objects.create(
            tipo_actividad='documento_subido',
            descripcion=f'Documento {instance.get_tipo_display()} subido para {instance.siniestro.numero_siniestro}',
            usuario=instance.siniestro.asesor_asignado,
            content_type=ContentType.objects.get_for_model(DocumentoSiniestro),
            object_id=instance.id
        )


@receiver(post_save, sender=HistorialEstado)
def crear_alerta_cambio_estado(sender, instance, created, **kwargs):
    """Crea una alerta cuando cambia el estado de un siniestro"""
    if created:
        Alerta.objects.create(
            tipo_actividad='estado_cambiado',
            descripcion=f'{instance.siniestro.numero_siniestro}: {instance.estado_anterior} → {instance.estado_nuevo}',
            usuario=instance.siniestro.asesor_asignado,
            content_type=ContentType.objects.get_for_model(Siniestro),
            object_id=instance.siniestro.id
        )


@receiver(post_save, sender=Poliza)
def crear_alerta_poliza(sender, instance, created, **kwargs):
    """Crea una alerta cuando se crea o actualiza una póliza"""
    if created:
        Alerta.objects.create(
            tipo_actividad='poliza_creada',
            descripcion=f'Nueva póliza {instance.numero_poliza} creada',
            content_type=ContentType.objects.get_for_model(Poliza),
            object_id=instance.id
        )
    else:
        Alerta.objects.create(
            tipo_actividad='poliza_actualizada',
            descripcion=f'Póliza {instance.numero_poliza} actualizada',
            content_type=ContentType.objects.get_for_model(Poliza),
            object_id=instance.id
        )