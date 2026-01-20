"""
Utilidades para el módulo de siniestros.
Incluye el Notificador para envío de correos.
"""

from django.core.mail import send_mail
from django.conf import settings
import threading
import logging

logger = logging.getLogger(__name__)


class Notificador:
    """
    Clase para enviar notificaciones por correo electrónico.
    Los correos se envían en un hilo separado para no bloquear la respuesta.
    """
    
    PLANTILLAS = {
        'docs_incompletos': {
            'asunto': 'Documentos Incompletos - Siniestro #{numero}',
            'mensaje': '''
Se ha detectado que faltan documentos para procesar su siniestro.

Documentos faltantes:
{documentos_faltantes}

Por favor, envíe los documentos faltantes lo antes posible para continuar con el proceso.
'''
        },
        'docs_completos': {
            'asunto': 'Documentos Completos - Siniestro #{numero}',
            'mensaje': '''
Sus documentos han sido validados correctamente.

Su siniestro será enviado a la aseguradora para su revisión.
'''
        },
        'enviado': {
            'asunto': 'Siniestro Enviado a Aseguradora - #{numero}',
            'mensaje': '''
Su siniestro ha sido enviado a la aseguradora para su análisis.

Aseguradora: {aseguradora}
Fecha de envío: {fecha_envio}
Fecha límite de respuesta: {fecha_limite}

Le notificaremos cuando tengamos una respuesta.
'''
        },
        'en_revision': {
            'asunto': 'Siniestro en Revisión - #{numero}',
            'mensaje': '''
La aseguradora ha recibido su siniestro y está en proceso de revisión.

Le mantendremos informado sobre el avance.
'''
        },
        'aprobado': {
            'asunto': '¡Siniestro Aprobado! - #{numero}',
            'mensaje': '''
¡Buenas noticias! Su siniestro ha sido APROBADO por la aseguradora.

La cobertura ha sido validada. Próximamente recibirá información sobre la liquidación.
'''
        },
        'rechazado': {
            'asunto': 'Siniestro Rechazado - #{numero}',
            'mensaje': '''
Lamentamos informarle que su siniestro ha sido RECHAZADO por la aseguradora.

Razón del rechazo:
{razon_rechazo}

Si tiene dudas, puede contactarnos para más información.
'''
        },
        'liquidado': {
            'asunto': 'Liquidación de Siniestro - #{numero}',
            'mensaje': '''
Se ha procesado la liquidación de su siniestro.

Monto aprobado: ${monto_aprobado}
Deducible aplicado: ${deducible}
Monto a pagar: ${monto_a_pagar}

El pago será procesado en los próximos días.
'''
        },
        'pagado': {
            'asunto': '¡Pago Realizado! - Siniestro #{numero}',
            'mensaje': '''
¡Su pago ha sido procesado exitosamente!

Monto pagado: ${monto_a_pagar}
Fecha de pago: {fecha_pago}

Gracias por su paciencia durante el proceso.
'''
        },
        'cerrado': {
            'asunto': 'Siniestro Cerrado - #{numero}',
            'mensaje': '''
Su siniestro ha sido cerrado oficialmente.

Fecha de cierre: {fecha_cierre}
Tiempo total de resolución: {dias_resolucion} días

Gracias por confiar en nosotros.
'''
        },
        'recordatorio_docs': {
            'asunto': 'Recordatorio: Documentos Pendientes - Siniestro #{numero}',
            'mensaje': '''
Le recordamos que aún tiene documentos pendientes por entregar para su siniestro.

Documentos faltantes:
{documentos_faltantes}

Por favor, envíe los documentos lo antes posible para evitar retrasos en el proceso.
'''
        },
    }

    @staticmethod
    def enviar_correo(siniestro, asunto, mensaje):
        """
        Envía un correo electrónico al reclamante del siniestro.
        El envío se realiza en un hilo separado para no bloquear.
        
        Args:
            siniestro: Instancia del modelo Siniestro
            asunto: Asunto del correo
            mensaje: Cuerpo del mensaje
            
        Returns:
            bool: True si se inició el envío, False si no hay email
        """
        if not siniestro.reclamante_email:
            logger.warning(f"Siniestro {siniestro.numero_siniestro} no tiene email de reclamante")
            return False
        
        cuerpo = f"""Estimado/a {siniestro.reclamante_nombre}:

Referencia: #{siniestro.numero_siniestro}

{mensaje}

Estado actual: {siniestro.get_estado_display()}

---
Sistema de Gestión de Siniestros - UTPL
Este es un correo automático, por favor no responda directamente.
"""
        
        def _enviar():
            try:
                send_mail(
                    subject=f"[Seguros UTPL] {asunto}",
                    message=cuerpo,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[siniestro.reclamante_email],
                    fail_silently=True
                )
                logger.info(f"Correo enviado a {siniestro.reclamante_email} - Siniestro {siniestro.numero_siniestro}")
            except Exception as e:
                logger.error(f"Error enviando correo: {e}")
        
        email_thread = threading.Thread(target=_enviar)
        email_thread.start()
        return True

    @classmethod
    def notificar_cambio_estado(cls, siniestro, estado_nuevo, datos_extra=None):
        """
        Envía una notificación basada en el nuevo estado del siniestro.
        
        Args:
            siniestro: Instancia del modelo Siniestro
            estado_nuevo: El nuevo estado al que cambió
            datos_extra: Diccionario con datos adicionales para la plantilla
        """
        if estado_nuevo not in cls.PLANTILLAS:
            logger.warning(f"No hay plantilla para el estado: {estado_nuevo}")
            return False
        
        plantilla = cls.PLANTILLAS[estado_nuevo]
        datos = datos_extra or {}
        
        # Datos base del siniestro
        datos.update({
            'numero': siniestro.numero_siniestro,
            'documentos_faltantes': siniestro.documentos_faltantes or 'No especificados',
            'aseguradora': siniestro.aseguradora_destino or siniestro.poliza.aseguradora,
            'fecha_envio': siniestro.fecha_envio_aseguradora.strftime('%d/%m/%Y') if siniestro.fecha_envio_aseguradora else 'N/A',
            'fecha_limite': siniestro.fecha_limite_respuesta_aseguradora.strftime('%d/%m/%Y') if siniestro.fecha_limite_respuesta_aseguradora else 'N/A',
            'razon_rechazo': siniestro.razon_rechazo or 'No especificada',
            'monto_aprobado': f"{siniestro.monto_aprobado:,.2f}" if siniestro.monto_aprobado else '0.00',
            'deducible': f"{siniestro.deducible_aplicado:,.2f}" if siniestro.deducible_aplicado else '0.00',
            'monto_a_pagar': f"{siniestro.monto_a_pagar:,.2f}" if siniestro.monto_a_pagar else '0.00',
            'fecha_pago': siniestro.fecha_pago_real.strftime('%d/%m/%Y') if siniestro.fecha_pago_real else 'N/A',
            'fecha_cierre': siniestro.fecha_cierre.strftime('%d/%m/%Y') if siniestro.fecha_cierre else 'N/A',
            'dias_resolucion': siniestro.tiempo_resolucion_dias or 0,
        })
        
        asunto = plantilla['asunto'].format(**datos)
        mensaje = plantilla['mensaje'].format(**datos)
        
        return cls.enviar_correo(siniestro, asunto, mensaje)

    @classmethod
    def enviar_recordatorio_documentos(cls, siniestro):
        """
        Envía un recordatorio de documentos pendientes.
        """
        return cls.notificar_cambio_estado(siniestro, 'recordatorio_docs')

    @classmethod
    def enviar_correo_aseguradora(cls, siniestro, correo_destino, mensaje_personalizado):
        """
        Envía un correo a la aseguradora con los datos del siniestro.
        
        Args:
            siniestro: Instancia del modelo Siniestro
            correo_destino: Email de la aseguradora
            mensaje_personalizado: Mensaje adicional
        """
        asunto = f"Nuevo Siniestro - {siniestro.numero_siniestro} - {siniestro.poliza.numero_poliza}"
        
        cuerpo = f"""
NOTIFICACIÓN DE SINIESTRO
========================

Número de Siniestro: {siniestro.numero_siniestro}
Número de Póliza: {siniestro.poliza.numero_poliza}
Ramo: {siniestro.ramo.ramo}

DATOS DEL EVENTO
----------------
Tipo de Evento: {siniestro.get_tipo_evento_display()}
Fecha de Ocurrencia: {siniestro.fecha_ocurrencia.strftime('%d/%m/%Y')}
Ubicación: {siniestro.ubicacion}
Descripción: {siniestro.descripcion}

BIEN AFECTADO
-------------
Tipo: {siniestro.tipo_bien}
Marca: {siniestro.marca or 'N/A'}
Modelo: {siniestro.modelo or 'N/A'}
Serie/Placa: {siniestro.numero_serie}

DATOS DEL RECLAMANTE
--------------------
Nombre: {siniestro.reclamante_nombre}
Email: {siniestro.reclamante_email}
Teléfono: {siniestro.reclamante_telefono or 'N/A'}

MONTO RECLAMADO: ${siniestro.monto_reclamado:,.2f}

{mensaje_personalizado}

---
Sistema de Gestión de Siniestros - UTPL
"""
        
        def _enviar():
            try:
                send_mail(
                    subject=asunto,
                    message=cuerpo,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[correo_destino],
                    fail_silently=True
                )
                logger.info(f"Correo enviado a aseguradora {correo_destino} - Siniestro {siniestro.numero_siniestro}")
            except Exception as e:
                logger.error(f"Error enviando correo a aseguradora: {e}")
        
        email_thread = threading.Thread(target=_enviar)
        email_thread.start()
        return True
