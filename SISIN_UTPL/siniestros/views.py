from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from datetime import date

from .models import Siniestro
from .forms import SiniestroForm


def crear_siniestro(request):
    if request.method == "POST":
        form = SiniestroForm(request.POST, request.FILES)
        if form.is_valid():
            siniestro = form.save(commit=False)
            siniestro.fecha_apertura = date.today()
            siniestro.save()

            messages.success(request, "Siniestro creado correctamente.")
            return redirect('dashboard_siniestros')
    else:
        form = SiniestroForm()

    return render(request, 'asesora/crear_siniestro.html', {
        'form': form,
        'today': date.today().isoformat(),
    })




def dashboard_siniestros(request):
    siniestros = Siniestro.objects.all().order_by('-fecha_apertura')

    siniestros_data = []
    for s in siniestros:
        siniestros_data.append({
            "id": s.id,
            "tipo_bien": s.tipo_bien,
            "fecha": s.fecha_ocurrencia,
            "estado": s.get_estado_display(),
        })

    stats = {
        "total": siniestros.count(),
        "creados": siniestros.filter(estado='reportado').count(),
        "en_proceso": siniestros.filter(estado='en_revision').count(),
        "finalizados": siniestros.filter(estado__in=['aprobado', 'pagado']).count(),
    }

    return render(request, "siniestros/dashboard.html", {
        "siniestros": siniestros_data,
        "stats": stats,
    })



def detalle_siniestro(request, siniestro_id):
    siniestro = get_object_or_404(Siniestro, id=siniestro_id)

    return render(request, 'siniestros/detalle_siniestro.html', {
        'siniestro': siniestro,
        'documentos': siniestro.documentos.all(),
        'pagare': getattr(siniestro, 'pagare', None)
    })


from django.contrib import messages

def enviar_a_revision(request, siniestro_id):
    siniestro = get_object_or_404(Siniestro, id=siniestro_id)

    try:
        siniestro.revisar()
        siniestro.save()
        messages.info(request, "Siniestro enviado a revisión.")
    except:
        messages.error(request, "No se pudo cambiar el estado.")

    return redirect('detalle_siniestro', siniestro_id=siniestro.id)


def aprobar_siniestro(request, siniestro_id):
    siniestro = get_object_or_404(Siniestro, id=siniestro_id)

    try:
        siniestro.aprobar()
        siniestro.cobertura_valida = True
        siniestro.fecha_respuesta_aseguradora = date.today()
        siniestro.save()
        messages.success(request, "Siniestro aprobado.")
    except:
        messages.error(request, "No se pudo aprobar el siniestro.")

    return redirect('detalle_siniestro', siniestro_id=siniestro.id)


def dashboard_asesora(request):
    return render(request, "asesora/dashboard.html")

def siniestros_asesora(request):
    return render(request, "asesora/siniestros.html")
    

















from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Avg, Sum, Q, F
from django.utils import timezone
from datetime import date, timedelta
import json

from .models import Siniestro, DocumentoSiniestro
from polizas.models import Poliza
from notificaciones.models import Notificacion
from .forms import SiniestroForm


def dashboard_asesora(request):
    """
    Dashboard principal de la asesora con todas las métricas,
    alertas, gráficos y listados del sistema.
    """
    
    hoy = date.today()
    hace_30_dias = hoy - timedelta(days=30)
    hace_8_dias = hoy - timedelta(days=8)
    hace_15_dias = hoy - timedelta(days=15)
    hace_72_horas = timezone.now() - timedelta(hours=72)
    
    # ==========================================
    # SECCIÓN 1: MÉTRICAS PRINCIPALES
    # ==========================================
    
    # Conteo por estados
    total_siniestros = Siniestro.objects.count()
    siniestros_reportados = Siniestro.objects.filter(estado='reportado').count()
    siniestros_revision = Siniestro.objects.filter(estado='en_revision').count()
    siniestros_aprobados = Siniestro.objects.filter(estado='aprobado').count()
    siniestros_pagados = Siniestro.objects.filter(estado='pagado').count()
    siniestros_rechazados = Siniestro.objects.filter(estado='rechazado').count()
    
    # Pólizas
    polizas_activas = Poliza.objects.filter(estado='activa').count()
    polizas_por_vencer = Poliza.objects.filter(
        estado='activa',
        fecha_vencimiento__lte=hoy + timedelta(days=30),
        fecha_vencimiento__gte=hoy
    ).count()
    
    # Tiempo promedio de resolución (solo cerrados)
    siniestros_cerrados = Siniestro.objects.filter(
        estado__in=['aprobado', 'pagado'],
        tiempo_resolucion_dias__isnull=False
    )
    tiempo_promedio = siniestros_cerrados.aggregate(
        promedio=Avg('tiempo_resolucion_dias')
    )['promedio'] or 0
    
    # Tasa de aprobación
    total_procesados = siniestros_aprobados + siniestros_pagados + siniestros_rechazados
    tasa_aprobacion = round((siniestros_aprobados + siniestros_pagados) / total_procesados * 100, 1) if total_procesados > 0 else 0
    
    stats = {
        'total': total_siniestros,
        'reportados': siniestros_reportados,
        'en_revision': siniestros_revision,
        'aprobados': siniestros_aprobados,
        'pagados': siniestros_pagados,
        'rechazados': siniestros_rechazados,
        'polizas_activas': polizas_activas,
        'polizas_por_vencer': polizas_por_vencer,
        'tiempo_promedio': round(tiempo_promedio, 1),
        'tasa_aprobacion': tasa_aprobacion,
    }
    
    # ==========================================
    # SECCIÓN 2: ALERTAS CRÍTICAS
    # ==========================================
    
    alertas = []
    
    # 1. Siniestros sin respuesta de aseguradora (+8 días)
    sin_respuesta = Siniestro.objects.filter(
        estado='en_revision',
        fecha_envio_aseguradora__lte=hace_8_dias,
        fecha_respuesta_aseguradora__isnull=True
    )
    if sin_respuesta.exists():
        alertas.append({
            'tipo': 'critica',
            'icono': 'alert-triangle',
            'titulo': f'{sin_respuesta.count()} siniestro(s) sin respuesta',
            'mensaje': 'La aseguradora no ha respondido en 8+ días hábiles',
            'url': None,
            'count': sin_respuesta.count()
        })
    
    # 2. Pólizas por vencer (próximos 30 días)
    if polizas_por_vencer > 0:
        alertas.append({
            'tipo': 'alerta',
            'icono': 'calendar',
            'titulo': f'{polizas_por_vencer} póliza(s) por vencer',
            'mensaje': 'Renovaciones pendientes en los próximos 30 días',
            'url': None,
            'count': polizas_por_vencer
        })
    
    # 3. Documentos faltantes (siniestros en revisión sin todos los docs)
    DOCS_REQUERIDOS = ['carta', 'informe', 'proforma', 'preexistencia']
    siniestros_sin_docs = []
    
    for siniestro in Siniestro.objects.filter(estado__in=['reportado', 'en_revision']):
        docs_actuales = set(siniestro.documentos.values_list('tipo', flat=True))
        docs_faltantes = set(DOCS_REQUERIDOS) - docs_actuales
        if docs_faltantes:
            siniestros_sin_docs.append(siniestro)
    
    if siniestros_sin_docs:
        alertas.append({
            'tipo': 'alerta',
            'icono': 'file-warning',
            'titulo': f'{len(siniestros_sin_docs)} siniestro(s) con documentos faltantes',
            'mensaje': 'Completar documentación para enviar a aseguradora',
            'url': None,
            'count': len(siniestros_sin_docs)
        })
    
    # 4. Siniestros fuera de plazo de reporte (>15 días desde ocurrencia)
    fuera_plazo = Siniestro.objects.filter(
        fecha_ocurrencia__lte=hace_15_dias,
        fecha_reporte__gt=F('fecha_ocurrencia') + timedelta(days=15)
    )
    if fuera_plazo.exists():
        alertas.append({
            'tipo': 'critica',
            'icono': 'clock-alert',
            'titulo': f'{fuera_plazo.count()} siniestro(s) reportado(s) tarde',
            'mensaje': 'Reportados después de 15 días - Posible rechazo de cobertura',
            'url': None,
            'count': fuera_plazo.count()
        })
    
    # 5. Pagos pendientes (+72 horas post-finiquito)
    # Asumimos que si tiene finiquito cargado pero no está en estado 'pagado'
    con_finiquito_sin_pago = Siniestro.objects.filter(
        estado='aprobado',
        documentos__tipo='finiquito',
        documentos__fecha_subida__lte=hace_72_horas
    ).exclude(estado='pagado').distinct()
    
    if con_finiquito_sin_pago.exists():
        alertas.append({
            'tipo': 'critica',
            'icono': 'dollar-sign',
            'titulo': f'{con_finiquito_sin_pago.count()} pago(s) pendiente(s)',
            'mensaje': 'Finiquito firmado hace +72 horas sin registro de pago',
            'url': None,
            'count': con_finiquito_sin_pago.count()
        })
    
    # ==========================================
    # SECCIÓN 3: DATOS PARA GRÁFICOS
    # ==========================================
    
    # Gráfico 1: Siniestros por estado (Donut)
    chart_estados = {
        'labels': ['Reportados', 'En Revisión', 'Aprobados', 'Pagados', 'Rechazados'],
        'data': [
            siniestros_reportados,
            siniestros_revision,
            siniestros_aprobados,
            siniestros_pagados,
            siniestros_rechazados
        ],
        'colors': ['#f59e0b', '#3b82f6', '#10b981', '#22c55e', '#ef4444']
    }
    
    # Gráfico 2: Evolución mensual (últimos 6 meses)
    meses_labels = []
    meses_data = []
    
    for i in range(5, -1, -1):
        mes_inicio = (hoy.replace(day=1) - timedelta(days=i*30)).replace(day=1)
        if i > 0:
            mes_fin = (mes_inicio + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        else:
            mes_fin = hoy
        
        count = Siniestro.objects.filter(
            fecha_reporte__gte=mes_inicio,
            fecha_reporte__lte=mes_fin
        ).count()
        
        meses_labels.append(mes_inicio.strftime('%b %Y'))
        meses_data.append(count)
    
    chart_evolucion = {
        'labels': meses_labels,
        'data': meses_data
    }
    
    # Gráfico 3: Siniestros por tipo de evento
    tipos_evento = Siniestro.objects.values('tipo_evento').annotate(
        total=Count('id')
    ).order_by('-total')[:5]
    
    chart_tipos = {
        'labels': [t['tipo_evento'].capitalize() for t in tipos_evento],
        'data': [t['total'] for t in tipos_evento],
        'colors': ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
    }
    
    # Gráfico 4: Montos reclamados vs aprobados
    montos = Siniestro.objects.aggregate(
        total_reclamado=Sum('monto_reclamado'),
        total_aprobado=Sum('monto_aprobado')
    )
    
    chart_montos = {
        'labels': ['Monto Reclamado', 'Monto Aprobado'],
        'data': [
            float(montos['total_reclamado'] or 0),
            float(montos['total_aprobado'] or 0)
        ],
        'colors': ['#f59e0b', '#10b981']
    }
    
    # ==========================================
    # SECCIÓN 4: TABLAS Y LISTADOS
    # ==========================================
    
    # Últimos 10 siniestros reportados
    ultimos_siniestros = Siniestro.objects.all().order_by('-fecha_reporte')[:10]
    
    ultimos_siniestros_data = []
    for s in ultimos_siniestros:
        # Mapeo de estados para colores
        estado_styles = {
            'reportado': {'bg': '#fef3c7', 'color': '#92400e', 'label': 'Reportado'},
            'en_revision': {'bg': '#dbeafe', 'color': '#1e40af', 'label': 'En Revisión'},
            'aprobado': {'bg': '#d1fae5', 'color': '#065f46', 'label': 'Aprobado'},
            'pagado': {'bg': '#dcfce7', 'color': '#14532d', 'label': 'Pagado'},
            'rechazado': {'bg': '#fee2e2', 'color': '#991b1b', 'label': 'Rechazado'},
        }
        
        style = estado_styles.get(s.estado, {'bg': '#f3f4f6', 'color': '#374151', 'label': s.get_estado_display()})
        
        ultimos_siniestros_data.append({
            'id': s.id,
            'numero_siniestro': s.numero_siniestro,
            'poliza': s.poliza.numero_poliza,
            'tipo_evento': s.tipo_evento.capitalize(),
            'fecha_reporte': s.fecha_reporte,
            'estado': s.estado,
            'estado_bg': style['bg'],
            'estado_color': style['color'],
            'estado_label': style['label']
        })
    
    # Siniestros pendientes de acción (reportados o en revisión)
    pendientes = Siniestro.objects.filter(
        estado__in=['reportado', 'en_revision']
    ).order_by('-fecha_reporte')[:5]
    
    pendientes_data = []
    for s in pendientes:
        # Calcular días desde reporte
        dias_transcurridos = (hoy - s.fecha_reporte).days
        
        pendientes_data.append({
            'id': s.id,
            'numero_siniestro': s.numero_siniestro,
            'tipo_evento': s.tipo_evento.capitalize(),
            'fecha_reporte': s.fecha_reporte,
            'dias_transcurridos': dias_transcurridos,
            'estado': s.get_estado_display()
        })
    
    # Próximas pólizas a vencer
    proximas_vencer = Poliza.objects.filter(
        estado='activa',
        fecha_vencimiento__gte=hoy,
        fecha_vencimiento__lte=hoy + timedelta(days=60)
    ).order_by('fecha_vencimiento')[:5]
    
    proximas_vencer_data = []
    for p in proximas_vencer:
        dias_para_vencer = (p.fecha_vencimiento - hoy).days
        
        # Color según urgencia
        if dias_para_vencer <= 15:
            urgencia_color = '#ef4444'  # Rojo
        elif dias_para_vencer <= 30:
            urgencia_color = '#f59e0b'  # Naranja
        else:
            urgencia_color = '#10b981'  # Verde
        
        proximas_vencer_data.append({
            'numero_poliza': p.numero_poliza,
            'aseguradora': p.aseguradora,
            'fecha_vencimiento': p.fecha_vencimiento,
            'dias_para_vencer': dias_para_vencer,
            'urgencia_color': urgencia_color
        })
    
    # Notificaciones recientes (no leídas)
    if hasattr(request.user, 'asesorutpl'):
        notificaciones = Notificacion.objects.filter(
            destinatario=request.user.asesorutpl,
            leida=False
        ).order_by('-fecha_creacion')[:5]
    else:
        notificaciones = []
    
    notificaciones_data = []
    for n in notificaciones:
        # Mapeo de tipos
        tipo_styles = {
            'info': {'icono': 'info', 'color': '#3b82f6'},
            'alerta': {'icono': 'alert-circle', 'color': '#f59e0b'},
            'critica': {'icono': 'alert-triangle', 'color': '#ef4444'},
        }
        
        style = tipo_styles.get(n.tipo, {'icono': 'bell', 'color': '#6b7280'})
        
        notificaciones_data.append({
            'id': n.id,
            'titulo': n.titulo,
            'mensaje': n.mensaje,
            'tipo': n.tipo,
            'icono': style['icono'],
            'color': style['color'],
            'fecha': n.fecha_creacion
        })
    
    # ==========================================
    # CONTEXTO COMPLETO
    # ==========================================
    
    context = {
        'stats': stats,
        'alertas': alertas,
        'chart_estados': json.dumps(chart_estados),
        'chart_evolucion': json.dumps(chart_evolucion),
        'chart_tipos': json.dumps(chart_tipos),
        'chart_montos': json.dumps(chart_montos),
        'ultimos_siniestros': ultimos_siniestros_data,
        'pendientes': pendientes_data,
        'proximas_vencer': proximas_vencer_data,
        'notificaciones': notificaciones_data,
    }
    
    return render(request, "asesora/dashboard.html", context)


# ==========================================
# VISTAS ADICIONALES (mantener las existentes)
# ==========================================

def crear_siniestro(request):
    if request.method == "POST":
        form = SiniestroForm(request.POST, request.FILES)
        if form.is_valid():
            siniestro = form.save(commit=False)
            siniestro.fecha_apertura = date.today()
            siniestro.save()

            messages.success(request, "Siniestro creado correctamente.")
            return redirect('dashboard_asesora')
    else:
        form = SiniestroForm()

    return render(request, 'asesora/crear_siniestro.html', {
        'form': form,
        'today': date.today().isoformat(),
    })


def detalle_siniestro(request, siniestro_id):
    siniestro = get_object_or_404(Siniestro, id=siniestro_id)

    return render(request, 'siniestros/detalle_siniestro.html', {
        'siniestro': siniestro,
        'documentos': siniestro.documentos.all(),
        'pagare': getattr(siniestro, 'pagare', None)
    })


def enviar_a_revision(request, siniestro_id):
    siniestro = get_object_or_404(Siniestro, id=siniestro_id)

    try:
        siniestro.revisar()
        siniestro.save()
        messages.info(request, "Siniestro enviado a revisión.")
    except:
        messages.error(request, "No se pudo cambiar el estado.")

    return redirect('detalle_siniestro', siniestro_id=siniestro.id)


def aprobar_siniestro(request, siniestro_id):
    siniestro = get_object_or_404(Siniestro, id=siniestro_id)

    try:
        siniestro.aprobar()
        siniestro.cobertura_valida = True
        siniestro.fecha_respuesta_aseguradora = date.today()
        siniestro.save()
        messages.success(request, "Siniestro aprobado.")
    except:
        messages.error(request, "No se pudo aprobar el siniestro.")

    return redirect('detalle_siniestro', siniestro_id=siniestro.id)


def siniestros_asesora(request):
    return render(request, "asesora/siniestros.html")