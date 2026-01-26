from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from datetime import timedelta
import logging

from .models import Notificacion, Alerta
from polizas.models import Poliza
from siniestros.models import Siniestro
from usuarios.models import AsesorUTPL

logger = logging.getLogger(__name__)


# =============================================
# FUNCIONES AUXILIARES
# =============================================

def obtener_asesor_actual(request):
    """
    Obtiene el asesor actual. Si no existe ninguno, crea uno por defecto.
    """
    # Intentar obtener por email del usuario autenticado
    asesor = None
    if request.user.is_authenticated and request.user.email:
        try:
            asesor = AsesorUTPL.objects.get(email=request.user.email)
        except AsesorUTPL.DoesNotExist:
            pass
    
    # Si no existe, usar el primer asesor disponible
    if not asesor:
        asesor = AsesorUTPL.objects.first()
    
    # Si no hay ningún asesor, crear uno por defecto
    if not asesor:
        asesor = AsesorUTPL.objects.create(
            nombre=request.user.first_name or request.user.username,
            apellido=request.user.last_name or '',
            email=request.user.email or f'{request.user.username}@utpl.edu.ec',
            telefono=''
        )
    
    return asesor


def enviar_correo_notificacion(notificacion, destinatarios_extra=None):
    """
    Envía un correo electrónico cuando se crea una notificación.
    Retorna (success: bool, error_message: str)
    """
    try:
        # Verificar configuración de email
        if not hasattr(settings, 'EMAIL_HOST_USER') or not settings.EMAIL_HOST_USER:
            error_msg = "Configuración de email no encontrada en settings.py"
            logger.error(error_msg)
            return False, error_msg
        
        # Obtener información del objeto relacionado
        objeto_info = None
        objeto_tipo = None
        objeto_url = None
        
        if notificacion.content_type and notificacion.object_id:
            try:
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
                    objeto_url = f"{getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')}/siniestros/detalle/{objeto.id}/"
                    
                elif isinstance(objeto, Poliza):
                    objeto_tipo = "Póliza"
                    objeto_info = {
                        'numero': objeto.numero_poliza,
                        'tipo': objeto.tipo_poliza,
                        'titular': str(objeto.titular),
                        'vencimiento': objeto.fecha_vencimiento,
                        'estado': objeto.get_estado_display(),
                    }
                    objeto_url = f"{getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')}/polizas/detalle/{objeto.id}/"
            except Exception as e:
                logger.warning(f"Error al obtener información del objeto relacionado: {e}")
        
        # Preparar lista de destinatarios
        destinatarios = []
        
        # Validar email del destinatario
        if notificacion.destinatario and notificacion.destinatario.email:
            destinatarios.append(notificacion.destinatario.email)
        else:
            error_msg = "El destinatario no tiene email configurado"
            logger.error(error_msg)
            return False, error_msg
        
        # Agregar email del reclamante si es un siniestro
        if objeto_info and 'reclamante_email' in objeto_info and objeto_info['reclamante_email']:
            destinatarios.append(objeto_info['reclamante_email'])
        
        # Agregar destinatarios extras
        if destinatarios_extra:
            destinatarios.extend([d for d in destinatarios_extra if d])
        
        # Eliminar duplicados y emails vacíos
        destinatarios = list(set([d for d in destinatarios if d]))
        
        if not destinatarios:
            error_msg = "No hay destinatarios válidos para enviar el correo"
            logger.error(error_msg)
            return False, error_msg
        
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
            'site_url': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000'),
            'notificacion_url': f"{getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')}/notificaciones/detalle/{notificacion.id}/",
        }
        
        # Renderizar HTML
        try:
            html_content = render_to_string('notificaciones/emails/notificacion.html', context)
        except Exception as e:
            # Si no existe el template, usar un HTML simple
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2>{notificacion.titulo}</h2>
                    <p>{notificacion.mensaje}</p>
                    <p><strong>Tipo:</strong> {notificacion.get_tipo_display()}</p>
                    <p><strong>Fecha:</strong> {notificacion.fecha_creacion.strftime('%d/%m/%Y %H:%M')}</p>
                </body>
            </html>
            """
            logger.warning(f"Template de email no encontrado, usando HTML simple: {e}")
        
        # Crear versión de texto plano
        text_content = strip_tags(html_content)
        
        # Crear el mensaje
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER)
        
        email = EmailMultiAlternatives(
            subject=asunto,
            body=text_content,
            from_email=from_email,
            to=destinatarios,
        )
        
        email.attach_alternative(html_content, "text/html")
        
        # Enviar
        email.send(fail_silently=False)
        
        # Registrar el envío
        notificacion.registrar_envio_correo()
        
        logger.info(f"Correo enviado exitosamente a {destinatarios} para notificación {notificacion.id}")
        return True, f"Correo enviado a: {', '.join(destinatarios)}"
        
    except Exception as e:
        error_msg = f"Error al enviar correo: {str(e)}"
        logger.error(f"Error en notificación {notificacion.id}: {error_msg}")
        return False, error_msg


def generar_notificaciones_automaticas(asesor):
    """
    Genera notificaciones automáticas basadas en reglas de negocio
    """
    hoy = timezone.now().date()
    
    # 1. PÓLIZAS POR VENCER (30, 15, 7 días)
    for dias in [30, 15, 7]:
        fecha_limite = hoy + timedelta(days=dias)
        
        polizas_por_vencer = Poliza.objects.filter(
            estado='activa',
            fecha_vencimiento=fecha_limite
        )
        
        for poliza in polizas_por_vencer:
            # Verificar si ya existe notificación para esta póliza y este plazo
            ct_poliza = ContentType.objects.get_for_model(Poliza)
            existe = Notificacion.objects.filter(
                destinatario=asesor,
                content_type=ct_poliza,
                object_id=poliza.id,
                categoria='poliza_vencer',
                titulo__contains=f'{dias} días'
            ).exists()
            
            if not existe:
                tipo_notif = 'critica' if dias <= 7 else 'alerta'
                Notificacion.objects.create(
                    destinatario=asesor,
                    titulo=f'Póliza {poliza.numero_poliza} vence en {dias} días',
                    mensaje=f'La póliza {poliza.numero_poliza} del titular {poliza.titular} vencerá el {poliza.fecha_vencimiento.strftime("%d/%m/%Y")}. Se requiere renovación urgente.',
                    tipo=tipo_notif,
                    categoria='poliza_vencer',
                    content_type=ct_poliza,
                    object_id=poliza.id
                )
    
    # 2. SINIESTROS CON DOCUMENTOS INCOMPLETOS
    siniestros_docs_incompletos = Siniestro.objects.filter(
        estado='docs_incompletos'
    )
    
    ct_siniestro = ContentType.objects.get_for_model(Siniestro)
    
    for siniestro in siniestros_docs_incompletos:
        # Verificar si ya existe notificación reciente (últimas 24 horas)
        hace_24h = timezone.now() - timedelta(hours=24)
        existe = Notificacion.objects.filter(
            destinatario=asesor,
            content_type=ct_siniestro,
            object_id=siniestro.id,
            categoria='siniestro_docs',
            fecha_creacion__gte=hace_24h
        ).exists()
        
        if not existe:
            Notificacion.objects.create(
                destinatario=asesor,
                titulo=f'Documentos incompletos - {siniestro.numero_siniestro}',
                mensaje=f'El siniestro {siniestro.numero_siniestro} tiene documentos faltantes: {siniestro.documentos_faltantes or "No especificados"}',
                tipo='alerta',
                categoria='siniestro_docs',
                content_type=ct_siniestro,
                object_id=siniestro.id
            )
    
    # 3. SINIESTROS REPORTADOS FUERA DE PLAZO
    siniestros_fuera_plazo = Siniestro.objects.filter(
        fuera_de_plazo=True,
        estado='reportado'
    )
    
    for siniestro in siniestros_fuera_plazo:
        existe = Notificacion.objects.filter(
            destinatario=asesor,
            content_type=ct_siniestro,
            object_id=siniestro.id,
            categoria='siniestro_plazo'
        ).exists()
        
        if not existe:
            Notificacion.objects.create(
                destinatario=asesor,
                titulo=f'Siniestro fuera de plazo - {siniestro.numero_siniestro}',
                mensaje=f'El siniestro {siniestro.numero_siniestro} fue reportado {siniestro.dias_transcurridos_reporte} días después del evento. Plazo máximo: 15 días.',
                tipo='critica',
                categoria='siniestro_plazo',
                content_type=ct_siniestro,
                object_id=siniestro.id
            )
    
    # 4. ASEGURADORAS FUERA DE PLAZO DE RESPUESTA
    siniestros_aseg_plazo = Siniestro.objects.filter(
        estado__in=['enviado', 'en_revision'],
        fecha_limite_respuesta_aseguradora__lt=hoy,
        fecha_respuesta_aseguradora__isnull=True
    )
    
    for siniestro in siniestros_aseg_plazo:
        dias_retraso = (hoy - siniestro.fecha_limite_respuesta_aseguradora).days
        existe = Notificacion.objects.filter(
            destinatario=asesor,
            content_type=ct_siniestro,
            object_id=siniestro.id,
            categoria='aseguradora_plazo'
        ).exists()
        
        if not existe:
            Notificacion.objects.create(
                destinatario=asesor,
                titulo=f'Aseguradora sin respuesta - {siniestro.numero_siniestro}',
                mensaje=f'La aseguradora lleva {dias_retraso} días de retraso en responder el siniestro {siniestro.numero_siniestro}. Fecha límite: {siniestro.fecha_limite_respuesta_aseguradora.strftime("%d/%m/%Y")}',
                tipo='critica',
                categoria='aseguradora_plazo',
                content_type=ct_siniestro,
                object_id=siniestro.id
            )
    
    # 5. PAGOS PENDIENTES (próximos a vencer en 72 horas)
    siniestros_pago_pendiente = Siniestro.objects.filter(
        estado='liquidado',
        fecha_limite_pago__lte=hoy + timedelta(days=3),
        fecha_pago_real__isnull=True
    )
    
    for siniestro in siniestros_pago_pendiente:
        dias_restantes = (siniestro.fecha_limite_pago - hoy).days
        existe = Notificacion.objects.filter(
            destinatario=asesor,
            content_type=ct_siniestro,
            object_id=siniestro.id,
            categoria='pago_pendiente'
        ).exists()
        
        if not existe:
            tipo_notif = 'critica' if dias_restantes <= 1 else 'alerta'
            Notificacion.objects.create(
                destinatario=asesor,
                titulo=f'Pago pendiente - {siniestro.numero_siniestro}',
                mensaje=f'El pago del siniestro {siniestro.numero_siniestro} debe realizarse antes del {siniestro.fecha_limite_pago.strftime("%d/%m/%Y")} ({dias_restantes} días restantes). Monto: ${siniestro.monto_a_pagar}',
                tipo=tipo_notif,
                categoria='pago_pendiente',
                content_type=ct_siniestro,
                object_id=siniestro.id
            )


# =============================================
# VISTAS PRINCIPALES
# =============================================

@login_required
def notificaciones(request):
    """
    Vista principal de notificaciones con filtros avanzados
    """
    # Obtener asesor actual
    asesor = obtener_asesor_actual(request)
    
    # Generar notificaciones automáticas antes de mostrar
    generar_notificaciones_automaticas(asesor)
    
    # Obtener parámetros de filtro
    filtro = request.GET.get('filtro', 'todas')
    tipo_filtro = request.GET.get('tipo', '')
    categoria_filtro = request.GET.get('categoria', '')
    busqueda = request.GET.get('busqueda', '')
    
    # Base queryset
    notificaciones_qs = Notificacion.objects.filter(destinatario=asesor)
    
    # Aplicar filtro de estado (leídas/no leídas)
    if filtro == 'no-leidas':
        notificaciones_qs = notificaciones_qs.filter(leida=False)
    elif filtro == 'leidas':
        notificaciones_qs = notificaciones_qs.filter(leida=True)
    
    # Aplicar filtro de tipo
    if tipo_filtro:
        notificaciones_qs = notificaciones_qs.filter(tipo=tipo_filtro)
    
    # Aplicar filtro de categoría
    if categoria_filtro:
        notificaciones_qs = notificaciones_qs.filter(categoria=categoria_filtro)
    
    # Aplicar búsqueda por título, mensaje o número de póliza/siniestro
    if busqueda:
        try:
            ct_poliza = ContentType.objects.get_for_model(Poliza)
            ct_siniestro = ContentType.objects.get_for_model(Siniestro)
            
            polizas_ids = Poliza.objects.filter(
                numero_poliza__icontains=busqueda
            ).values_list('id', flat=True)
            
            siniestros_ids = Siniestro.objects.filter(
                numero_siniestro__icontains=busqueda
            ).values_list('id', flat=True)
            
            notificaciones_qs = notificaciones_qs.filter(
                Q(titulo__icontains=busqueda) |
                Q(mensaje__icontains=busqueda) |
                (Q(content_type=ct_poliza) & Q(object_id__in=polizas_ids)) |
                (Q(content_type=ct_siniestro) & Q(object_id__in=siniestros_ids))
            )
        except:
            pass
    
    # Obtener estadísticas
    todas = Notificacion.objects.filter(destinatario=asesor)
    total = todas.count()
    no_leidas = todas.filter(leida=False).count()
    leidas = todas.filter(leida=True).count()
    criticas = todas.filter(tipo='critica').count()
    
    # Contar por tipo
    info_count = todas.filter(tipo='info').count()
    alerta_count = todas.filter(tipo='alerta').count()
    
    # Contar por categoría
    categorias_count = {}
    for cat_key, cat_label in Notificacion.CATEGORIA_CHOICES:
        categorias_count[cat_key] = {
            'label': cat_label,
            'count': todas.filter(categoria=cat_key).count()
        }
    
    # Obtener alertas recientes (últimas 10)
    alertas_recientes = Alerta.objects.all()[:10]
    
    # Preparar datos para el template
    notificaciones_list = []
    for n in notificaciones_qs:
        # Obtener referencia al objeto relacionado
        objeto_ref = None
        if n.content_type and n.object_id:
            try:
                objeto = n.contenido
                if isinstance(objeto, Siniestro):
                    objeto_ref = objeto.numero_siniestro
                elif isinstance(objeto, Poliza):
                    objeto_ref = objeto.numero_poliza
            except:
                pass
        
        notificaciones_list.append({
            'id': n.id,
            'titulo': n.titulo,
            'mensaje': n.mensaje,
            'tipo': n.tipo,
            'categoria': n.get_categoria_display(),
            'leida': n.leida,
            'fecha': n.fecha_creacion.strftime('%d/%m/%Y'),
            'hora': n.fecha_creacion.strftime('%H:%M'),
            'referencia': objeto_ref,
        })
    
    context = {
        'notificaciones': notificaciones_list,
        'total_count': total,
        'no_leidas_count': no_leidas,
        'leidas_count': leidas,
        'criticas_count': criticas,
        'info_count': info_count,
        'alerta_count': alerta_count,
        'categorias_count': categorias_count,
        'filtro': filtro,
        'tipo_filtro': tipo_filtro,
        'categoria_filtro': categoria_filtro,
        'busqueda': busqueda,
        'alertas_recientes': alertas_recientes,
        'tipo_choices': Notificacion.TIPO_CHOICES,
        'categoria_choices': Notificacion.CATEGORIA_CHOICES,
    }
    
    return render(request, 'asesora/notificaciones.html', context)


@login_required
def detalle_notificacion(request, notificacion_id):
    """
    Vista de detalle de una notificación específica
    Marca automáticamente como leída al acceder
    """
    asesor = obtener_asesor_actual(request)
    
    notificacion = get_object_or_404(
        Notificacion,
        id=notificacion_id,
        destinatario=asesor
    )
    
    # Marcar como leída
    if not notificacion.leida:
        notificacion.marcar_leida()
    
    # Obtener objeto relacionado
    objeto_relacionado = None
    tipo_objeto = None
    
    if notificacion.content_type and notificacion.object_id:
        try:
            objeto_relacionado = notificacion.contenido
            tipo_objeto = notificacion.content_type.model
        except:
            pass
    
    # Verificar si se debe mostrar confirmación de reenvío
    mostrar_confirmacion = request.session.get('mostrar_confirmacion_' + str(notificacion_id), False)
    
    context = {
        'notificacion': notificacion,
        'objeto_relacionado': objeto_relacionado,
        'tipo_objeto': tipo_objeto,
        'mostrar_confirmacion': mostrar_confirmacion,
    }
    
    return render(request, 'asesora/detalle_notificacion.html', context)


@login_required
def marcar_todas_leidas(request):
    """
    Marca todas las notificaciones del asesor como leídas
    """
    if request.method == 'POST':
        asesor = obtener_asesor_actual(request)
        
        Notificacion.objects.filter(
            destinatario=asesor,
            leida=False
        ).update(leida=True)
    
    return redirect('notificaciones')


@login_required
def marcar_leida(request, notificacion_id):
    """
    Marca una notificación específica como leída
    """
    if request.method == 'POST':
        asesor = obtener_asesor_actual(request)
        
        notificacion = get_object_or_404(
            Notificacion,
            id=notificacion_id,
            destinatario=asesor
        )
        notificacion.marcar_leida()
    
    return redirect('notificaciones')


@login_required
def eliminar_notificacion(request, notificacion_id):
    """
    Elimina una notificación específica
    """
    if request.method == 'POST':
        asesor = obtener_asesor_actual(request)
        
        notificacion = get_object_or_404(
            Notificacion,
            id=notificacion_id,
            destinatario=asesor
        )
        notificacion.delete()
    
    return redirect('notificaciones')


@login_required
def reenviar_correo_notificacion(request, notificacion_id):
    """
    Reenvía el correo de una notificación específica
    Requiere confirmación si ya se envió anteriormente
    """
    notificacion = get_object_or_404(Notificacion, id=notificacion_id)
    confirmar = request.POST.get('confirmar', 'no')
    
    # Si ya se envió y no hay confirmación, mostrar advertencia
    if notificacion.correo_enviado and confirmar != 'si':
        messages.warning(
            request,
            f'⚠️ Este correo ya fue enviado {notificacion.veces_enviado} vez/veces '
            f'(última vez: {notificacion.fecha_envio_correo.strftime("%d/%m/%Y %H:%M")}). '
            f'¿Estás seguro de querer enviarlo nuevamente?'
        )
        # Agregar flag en session para mostrar botón de confirmación
        request.session['mostrar_confirmacion_' + str(notificacion_id)] = True
        return redirect('detalle_notificacion', notificacion_id=notificacion_id)
    
    # Enviar el correo
    if request.method == 'POST':
        try:
            asesor = obtener_asesor_actual(request)
            
            # Enviar correo
            exito, mensaje = enviar_correo_notificacion(notificacion)
            
            if exito:
                messages.success(request, f'✓ {mensaje}')
                # Limpiar flag de confirmación
                if 'mostrar_confirmacion_' + str(notificacion_id) in request.session:
                    del request.session['mostrar_confirmacion_' + str(notificacion_id)]
            else:
                messages.error(request, f'✗ {mensaje}')
        
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return redirect('detalle_notificacion', notificacion_id=notificacion_id)


@login_required
def probar_email(request):
    """
    Vista temporal para probar la configuración de email
    """
    from django.core.mail import send_mail
    from django.http import JsonResponse
    
    try:
        # Verificar configuración
        config_info = {
            'EMAIL_BACKEND': getattr(settings, 'EMAIL_BACKEND', 'No configurado'),
            'EMAIL_HOST': getattr(settings, 'EMAIL_HOST', 'No configurado'),
            'EMAIL_PORT': getattr(settings, 'EMAIL_PORT', 'No configurado'),
            'EMAIL_USE_TLS': getattr(settings, 'EMAIL_USE_TLS', False),
            'EMAIL_HOST_USER': getattr(settings, 'EMAIL_HOST_USER', 'No configurado'),
            'DEFAULT_FROM_EMAIL': getattr(settings, 'DEFAULT_FROM_EMAIL', 'No configurado'),
        }
        
        # Intentar enviar correo de prueba
        asesor = obtener_asesor_actual(request)
        
        if not asesor.email:
            return JsonResponse({
                'success': False,
                'error': 'El asesor no tiene email configurado',
                'config': config_info
            })
        
        send_mail(
            subject='Prueba de correo - SISIN UTPL',
            message='Este es un correo de prueba del sistema de notificaciones.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[asesor.email],
            fail_silently=False,
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Correo de prueba enviado exitosamente a {asesor.email}',
            'config': config_info
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'config': config_info
        })
    
@login_required
def eliminar_notificacion(request, notificacion_id):
    if request.method == 'POST':
        asesor = obtener_asesor_actual(request)
        
        notificacion = get_object_or_404(
            Notificacion,
            id=notificacion_id,
            destinatario=asesor
        )
        
        titulo = notificacion.titulo  # para el mensaje
        notificacion.delete()
        
        messages.success(request, f'Notificación eliminada: "{titulo}"')
    
    return redirect('notificaciones')  # o redirect('detalle_notificacion', ...) si vienes de detalle

@login_required
def eliminar_todas_leidas(request):
    if request.method == 'POST':
        asesor = obtener_asesor_actual(request)
        count = Notificacion.objects.filter(
            destinatario=asesor,
            leida=True
        ).count()
        
        Notificacion.objects.filter(
            destinatario=asesor,
            leida=True
        ).delete()
        
        messages.success(request, f'Se eliminaron {count} notificaciones leídas.')
    
    return redirect('notificaciones')


@login_required
def eliminar_alerta(request, alerta_id):
    """Elimina una alerta específica"""
    if request.method == 'POST':
        try:
            alerta = get_object_or_404(Alerta, id=alerta_id)
            descripcion = alerta.descripcion
            alerta.delete()
            messages.success(request, f'Alerta eliminada: "{descripcion[:50]}..."')
        except Exception as e:
            messages.error(request, f'Error al eliminar alerta: {str(e)}')
    
    # Redirigir a la página anterior o al dashboard
    return redirect(request.META.get('HTTP_REFERER', 'dashboard_asesora'))


@login_required
def eliminar_todas_alertas(request):
    """Elimina todas las alertas"""
    if request.method == 'POST':
        try:
            count = Alerta.objects.count()
            Alerta.objects.all().delete()
            messages.success(request, f'Se eliminaron {count} alertas correctamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar alertas: {str(e)}')
    
    return redirect(request.META.get('HTTP_REFERER', 'dashboard_asesora'))