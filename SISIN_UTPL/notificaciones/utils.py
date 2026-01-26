from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


def enviar_correo_notificacion(notificacion, destinatarios_extra=None):
    """
    Envía un correo electrónico cuando se crea una notificación.
    
    Args:
        notificacion: Instancia de Notificacion
        destinatarios_extra: Lista opcional de emails adicionales
    
    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    try:
        # Obtener información del objeto relacionado
        objeto_info = None
        objeto_tipo = None
        objeto_url = None
        
        if notificacion.content_type and notificacion.object_id:
            try:
                from siniestros.models import Siniestro
                from polizas.models import Poliza
                
                objeto = notificacion.contenido
                
                if isinstance(objeto, Siniestro):
                    objeto_tipo = "Siniestro"
                    objeto_info = {
                        'numero': objeto.numero_siniestro,
                        'tipo': objeto.get_tipo_evento_display(),
                        'fecha': objeto.fecha_ocurrencia,
                        'estado': objeto.get_estado_display(),
                        'reclamante': objeto.reclamante_nombre,
                        'reclamante_email': objeto.reclamante_email,
                    }
                    objeto_url = f"{settings.SITE_URL}/siniestros/detalle/{objeto.id}/"
                    
                elif isinstance(objeto, Poliza):
                    objeto_tipo = "Póliza"
                    objeto_info = {
                        'numero': objeto.numero_poliza,
                        'tipo': objeto.tipo_poliza,
                        'titular': str(objeto.titular),
                        'vencimiento': objeto.fecha_vencimiento,
                        'estado': objeto.get_estado_display(),
                    }
                    objeto_url = f"{settings.SITE_URL}/polizas/detalle/{objeto.id}/"
            except Exception as e:
                logger.warning(f"Error al obtener información del objeto relacionado: {e}")
        
        # Preparar lista de destinatarios
        destinatarios = [notificacion.destinatario.email]
        
        # Agregar email del reclamante si es un siniestro
        if objeto_info and 'reclamante_email' in objeto_info:
            destinatarios.append(objeto_info['reclamante_email'])
        
        # Agregar destinatarios extras
        if destinatarios_extra:
            destinatarios.extend(destinatarios_extra)
        
        # Eliminar duplicados
        destinatarios = list(set(destinatarios))
        
        # Determinar el asunto según el tipo
        asunto_prefijo = {
            'critica': '🚨 URGENTE',
            'alerta': '⚠️ ALERTA',
            'info': 'ℹ️ INFO',
        }.get(notificacion.tipo, 'ℹ️')
        
        asunto = f"{asunto_prefijo} - {notificacion.titulo}"
        
        # Contexto para el template
        context = {
            'notificacion': notificacion,
            'asesor': notificacion.destinatario,
            'objeto_tipo': objeto_tipo,
            'objeto_info': objeto_info,
            'objeto_url': objeto_url,
            'site_url': settings.SITE_URL,
            'notificacion_url': f"{settings.SITE_URL}/notificaciones/detalle/{notificacion.id}/",
        }
        
        # Renderizar HTML
        html_content = render_to_string('notificaciones/emails/notificacion.html', context)
        
        # Crear versión de texto plano
        text_content = strip_tags(html_content)
        
        # Crear el mensaje
        email = EmailMultiAlternatives(
            subject=asunto,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=destinatarios,
        )
        
        email.attach_alternative(html_content, "text/html")
        
        # Enviar
        email.send()
        
        logger.info(f"Correo enviado exitosamente a {destinatarios} para notificación {notificacion.id}")
        return True
        
    except Exception as e:
        logger.error(f"Error al enviar correo de notificación {notificacion.id}: {e}")
        return False


def enviar_resumen_diario(asesor, notificaciones):
    """
    Envía un resumen diario con todas las notificaciones no leídas.
    
    Args:
        asesor: Instancia de AsesorUTPL
        notificaciones: QuerySet de notificaciones
    
    Returns:
        bool: True si se envió correctamente
    """
    try:
        if not notificaciones.exists():
            return False
        
        # Estadísticas
        criticas = notificaciones.filter(tipo='critica').count()
        alertas = notificaciones.filter(tipo='alerta').count()
        info = notificaciones.filter(tipo='info').count()
        
        context = {
            'asesor': asesor,
            'notificaciones': notificaciones,
            'total': notificaciones.count(),
            'criticas': criticas,
            'alertas': alertas,
            'info': info,
            'site_url': settings.SITE_URL,
        }
        
        html_content = render_to_string('notificaciones/emails/resumen_diario.html', context)
        text_content = strip_tags(html_content)
        
        email = EmailMultiAlternatives(
            subject=f"📊 Resumen diario - {notificaciones.count()} notificaciones pendientes",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[asesor.email],
        )
        
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"Resumen diario enviado a {asesor.email}")
        return True
        
    except Exception as e:
        logger.error(f"Error al enviar resumen diario: {e}")
        return False