from django.contrib.contenttypes.models import ContentType
from notificaciones.models import Notificacion
from siniestros.models import Siniestro


def notificar_siniestro(
    siniestro: Siniestro,
    titulo: str,
    mensaje: str,
    tipo: str = 'info'
):
    if not siniestro.asesor_asignado:
        return

    Notificacion.objects.create(
        titulo=titulo,
        mensaje=mensaje,
        tipo=tipo,
        content_type=ContentType.objects.get_for_model(Siniestro),
        object_id=siniestro.id,
        destinatario=siniestro.asesor_asignado
    )
