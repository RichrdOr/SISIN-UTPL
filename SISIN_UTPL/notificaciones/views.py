from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from datetime import timedelta
from .models import Notificacion, Alerta
from polizas.models import Poliza
from siniestros.models import Siniestro
from usuarios.models import AsesorUTPL


@login_required
def notificaciones(request):
    """
    Vista principal de notificaciones
    Muestra todas las notificaciones del asesor con filtros
    """
    # Obtener o crear el asesor (ajustado según tu modelo)
    # Si AsesorUTPL no tiene relación con User, usa el primer asesor o ajusta según tu lógica
    try:
        asesor = AsesorUTPL.objects.first()
        if not asesor:
            # Crear un asesor de prueba si no existe ninguno
            asesor = AsesorUTPL.objects.create(
                nombre=request.user.username,
                email=request.user.email
            )
    except Exception as e:
        asesor = AsesorUTPL.objects.first()
    
    # Generar notificaciones automáticas antes de mostrar
    generar_notificaciones_automaticas(asesor)
    
    # Obtener filtro
    filtro = request.GET.get('filtro', 'todas')
    
    # Base queryset
    notificaciones_qs = Notificacion.objects.filter(destinatario=asesor)
    
    # Aplicar filtro
    if filtro == 'no-leidas':
        notificaciones_qs = notificaciones_qs.filter(leida=False)
    
    # Obtener estadísticas
    total = notificaciones_qs.count()
    no_leidas = notificaciones_qs.filter(leida=False).count()
    leidas = notificaciones_qs.filter(leida=True).count()
    criticas = notificaciones_qs.filter(tipo='critica').count()
    
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
            'leida': n.leida,
            'fecha': n.fecha_creacion.strftime('%d/%m/%Y'),
            'hora': n.fecha_creacion.strftime('%H:%M'),
            'siniestro_id': objeto_ref,
        })
    
    context = {
        'notificaciones': notificaciones_list,
        'no_leidas_count': no_leidas,
        'leidas_count': leidas,
        'criticas_count': criticas,
        'filtro': filtro,
        'alertas_recientes': alertas_recientes,
    }
    
    return render(request, 'asesora/notificaciones.html', context)


@login_required
def detalle_notificacion(request, notificacion_id):
    """
    Vista de detalle de una notificación específica
    Marca automáticamente como leída al acceder
    """
    asesor, created = AsesorUTPL.objects.get_or_create(
        usuario=request.user,
        defaults={'nombre': request.user.username}
    )
    
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
    
    context = {
        'notificacion': notificacion,
        'objeto_relacionado': objeto_relacionado,
        'tipo_objeto': tipo_objeto,
    }
    
    return render(request, 'asesora/detalle_notificacion.html', context)


@login_required
def marcar_todas_leidas(request):
    """
    Marca todas las notificaciones del asesor como leídas
    """
    if request.method == 'POST':
        asesor, created = AsesorUTPL.objects.get_or_create(
            usuario=request.user,
            defaults={'nombre': request.user.username}
        )
        
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
        asesor, created = AsesorUTPL.objects.get_or_create(
            usuario=request.user,
            defaults={'nombre': request.user.username}
        )
        
        notificacion = get_object_or_404(
            Notificacion,
            id=notificacion_id,
            destinatario=asesor
        )
        notificacion.marcar_leida()
    
    return redirect('notificaciones')


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