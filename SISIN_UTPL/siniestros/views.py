from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db.models import Count, Avg, Sum, Q, F
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from datetime import date, timedelta
import json
from django.http import HttpResponse
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill

# Modelos y Forms
from .models import Siniestro, DocumentoSiniestro, RoboSiniestro
from .forms import SiniestroForm, DocumentoSiniestroForm, RoboSiniestroForm
from polizas.models import Poliza, RamoPoliza
from usuarios.models import AsesorUTPL
from notificaciones.models import Notificacion

# ==========================================
# VISTAS DE DASHBOARD Y LISTADOS (ASESORA)
# ==========================================

def dashboard_siniestros(request):
    """
    Dashboard principal con métricas, alertas y gráficos.
    """
    hoy = date.today()
    hace_8_dias = hoy - timedelta(days=8)
    hace_15_dias = hoy - timedelta(days=15)
    hace_72_horas = timezone.now() - timedelta(hours=72)
    
    # Métricas Principales
    total_siniestros = Siniestro.objects.count()
    siniestros_reportados = Siniestro.objects.filter(estado='reportado').count()
    siniestros_revision = Siniestro.objects.filter(estado='en_revision').count()
    siniestros_aprobados = Siniestro.objects.filter(estado='aprobado').count()
    siniestros_pagados = Siniestro.objects.filter(estado='pagado').count()
    siniestros_rechazados = Siniestro.objects.filter(estado='rechazado').count()
    
    polizas_activas = Poliza.objects.filter(estado='activa').count()
    
    # Tiempo promedio y Tasa de aprobación
    siniestros_cerrados = Siniestro.objects.filter(estado__in=['aprobado', 'pagado'], tiempo_resolucion_dias__isnull=False)
    tiempo_promedio = siniestros_cerrados.aggregate(promedio=Avg('tiempo_resolucion_dias'))['promedio'] or 0
    
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
        'tiempo_promedio': round(tiempo_promedio, 1),
        'tasa_aprobacion': tasa_aprobacion,
    }

    # Gráficos (JSON para Chart.js)
    chart_estados = {
        'labels': ['Reportados', 'Revisión', 'Aprobados', 'Pagados', 'Rechazados'],
        'data': [siniestros_reportados, siniestros_revision, siniestros_aprobados, siniestros_pagados, siniestros_rechazados],
        'colors': ['#f59e0b', '#3b82f6', '#10b981', '#22c55e', '#ef4444']
    }

    # Siniestros Recientes
    ultimos_siniestros = Siniestro.objects.all().order_by('-fecha_reporte')[:10]

    context = {
        'stats': stats,
        'chart_estados': json.dumps(chart_estados),
        'ultimos_siniestros': ultimos_siniestros,
    }
    return render(request, "asesora/dashboard.html", context)


def siniestros_asesora(request):
    """Listado general de siniestros para la asesora"""
    siniestros = Siniestro.objects.select_related('poliza', 'ramo', 'asesor_asignado').order_by('-fecha_reporte')
    
    # Calcular estadísticas
    siniestros_revision_count = siniestros.filter(estado='en_revision').count()
    siniestros_finalizados_count = siniestros.filter(estado__in=['aprobado', 'pagado', 'cerrado']).count()
    
    context = {
        'siniestros': siniestros,
        'siniestros_revision_count': siniestros_revision_count,
        'siniestros_finalizados_count': siniestros_finalizados_count,
    }
    return render(request, "asesora/siniestros.html", context)


# ==========================================
# CREACIÓN Y PROCESAMIENTO (REFORMULADO)
# ==========================================

def validar_archivo_pdf(archivo):
    """Valida que el archivo sea un PDF válido"""
    if not archivo:
        return True  # Si no hay archivo, no hay error (puede ser opcional)
    
    # Verificar extensión
    nombre = archivo.name.lower()
    if not nombre.endswith('.pdf'):
        return False
    
    # Verificar tipo MIME
    content_type = archivo.content_type
    if content_type != 'application/pdf':
        return False
    
    return True


def crear_siniestro(request):
    """Vista optimizada para crear siniestros y procesar sus documentos (solo PDF)"""
    if request.method == "POST":
        form = SiniestroForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Validar que todos los archivos sean PDF antes de procesar
            tipos_documentos = {
                'doc_carta': 'carta',
                'doc_informe': 'informe',
                'doc_proforma': 'proforma',
                'doc_preexistencia': 'preexistencia',
                'doc_denuncia': 'denuncia'
            }
            
            archivos_invalidos = []
            for campo_html, tipo_db in tipos_documentos.items():
                archivo = request.FILES.get(campo_html)
                if archivo and not validar_archivo_pdf(archivo):
                    archivos_invalidos.append(f"{tipo_db.capitalize()}")
            
            if archivos_invalidos:
                messages.error(request, f"Los siguientes documentos no son archivos PDF válidos: {', '.join(archivos_invalidos)}. Solo se permiten archivos PDF.")
                return render(request, 'asesora/crear_siniestro.html', {
                    'form': form,
                    'today': date.today().isoformat(),
                    'polizas': Poliza.objects.filter(estado='activa'),
                })
            
            try:
                with transaction.atomic():
                    # 1. Guardar Siniestro Base
                    siniestro = form.save(commit=False)
                    siniestro.fecha_apertura = date.today()
                    
                    # Rescatamos el ramo si está disabled en el HTML
                    if not siniestro.ramo_id:
                        siniestro.ramo_id = request.POST.get('ramo')
                    
                    siniestro.save() # Aquí se genera el número de siniestro (SIN-202X-...)

                    # 2. Si es ROBO, guardamos los datos de texto en RoboSiniestro
                    if request.POST.get('tipo_evento') == 'robo':
                        RoboSiniestro.objects.create(
                            siniestro=siniestro,
                            denuncia_policial=request.POST.get('denuncia_policial'), # Texto
                            fiscalia=request.POST.get('fiscalia'),                   # Texto
                            fecha_denuncia=request.POST.get('fecha_denuncia') or date.today()
                        )

                    # 3. Procesar TODOS los archivos PDF subidos
                    for campo_html, tipo_db in tipos_documentos.items():
                        archivo = request.FILES.get(campo_html)
                        if archivo:
                            DocumentoSiniestro.objects.create(
                                siniestro=siniestro,
                                tipo=tipo_db,
                                archivo=archivo
                            )
                    
                    messages.success(request, f"¡Siniestro {siniestro.numero_siniestro} creado exitosamente con {len([f for f in tipos_documentos.keys() if request.FILES.get(f)])} documentos PDF!")
                    return redirect('siniestros_asesora')
                    
            except Exception as e:
                messages.error(request, f"Error crítico al guardar: {e}")
        else:
            # Mostrar errores específicos del formulario si no es válido
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error en {field}: {error}")
    else:
        form = SiniestroForm()

    return render(request, 'asesora/crear_siniestro.html', {
        'form': form,
        'today': date.today().isoformat(),
        'polizas': Poliza.objects.filter(estado='activa'),
    })

# ==========================================
# GESTIÓN DE ESTADOS Y DETALLE
# ==========================================

def detalle_siniestro(request, siniestro_id):
    siniestro = get_object_or_404(Siniestro, id=siniestro_id)
    
    # Definir los estados del timeline
    estados_orden = ['reportado', 'en_revision', 'aprobado', 'pagado']
    estado_actual = siniestro.estado
    
    # Calcular el índice del estado actual
    try:
        indice_actual = estados_orden.index(estado_actual)
    except ValueError:
        indice_actual = 0  # Si es rechazado u otro estado, mostrar al inicio
    
    # Calcular progreso (porcentaje)
    progreso_estado = (indice_actual / (len(estados_orden) - 1)) * 100 if len(estados_orden) > 1 else 0
    
    # Construir lista de estados para el timeline
    estados = [
        {'nombre': 'Reportado', 'icono': '📋', 'activo': indice_actual >= 0, 'actual': estado_actual == 'reportado'},
        {'nombre': 'En Revisión', 'icono': '🔍', 'activo': indice_actual >= 1, 'actual': estado_actual == 'en_revision'},
        {'nombre': 'Aprobado', 'icono': '✅', 'activo': indice_actual >= 2, 'actual': estado_actual == 'aprobado'},
        {'nombre': 'Pagado', 'icono': '💰', 'activo': indice_actual >= 3, 'actual': estado_actual == 'pagado'},
    ]
    
    # Si está rechazado, marcar todos como inactivos excepto el primero
    if estado_actual == 'rechazado':
        estados = [
            {'nombre': 'Reportado', 'icono': '📋', 'activo': True, 'actual': False},
            {'nombre': 'Rechazado', 'icono': '❌', 'activo': True, 'actual': True},
            {'nombre': '-', 'icono': '⬜', 'activo': False, 'actual': False},
            {'nombre': '-', 'icono': '⬜', 'activo': False, 'actual': False},
        ]
        progreso_estado = 25
    
    return render(request, 'asesora/detalle_siniestro.html', {
        'siniestro': siniestro,
        'documentos': siniestro.documentos.all(),
        'pagare': getattr(siniestro, 'pagare', None),
        'estados': estados,
        'progreso_estado': progreso_estado,
    })

def enviar_a_revision(request, siniestro_id):
    siniestro = get_object_or_404(Siniestro, id=siniestro_id)
    try:
        siniestro.revisar() # Asumiendo que existe este método en el modelo
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

@require_http_methods(["GET"])
def obtener_ramos_poliza(request, poliza_id):
    ramos = RamoPoliza.objects.filter(poliza_id=poliza_id).values('id', 'ramo', 'suma_asegurada')
    return JsonResponse({'success': True, 'ramos': list(ramos)})

def exportar_siniestros_excel(request):
    # 1. Crear el libro y la hoja
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Siniestros"

    # 2. Estilo para el encabezado
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid") # Color Primary
    alignment = Alignment(horizontal="center", vertical="center")

    # 3. Definir encabezados
    headers = [
        'Nº Siniestro', 'Póliza', 'Titular', 'Aseguradora', 
        'Tipo Evento', 'Fecha Ocurrencia', 'Monto Reclamado', 'Estado'
    ]
    
    for col_num, column_title in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=column_title)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = alignment
        # Ajustar ancho de columna básico
        ws.column_dimensions[openpyxl.utils.get_column_letter(col_num)].width = 20

    # 4. Obtener los datos (usamos la misma lógica que en el listado)
    siniestros = Siniestro.objects.select_related('poliza').all().order_by('-fecha_reporte')

    # 5. Escribir los datos
    for row_num, siniestro in enumerate(siniestros, 2):
        ws.cell(row=row_num, column=1, value=str(siniestro.id))
        ws.cell(row=row_num, column=2, value=siniestro.poliza.numero_poliza if siniestro.poliza else "N/A")
        ws.cell(row=row_num, column=3, value=siniestro.poliza.titular if siniestro.poliza else "N/A")
        ws.cell(row=row_num, column=4, value=siniestro.poliza.aseguradora if siniestro.poliza else "N/A")
        ws.cell(row=row_num, column=5, value=siniestro.get_tipo_evento_display() if hasattr(siniestro, 'get_tipo_evento_display') else siniestro.tipo_evento)
        ws.cell(row=row_num, column=6, value=siniestro.fecha_ocurrencia.strftime('%d/%m/%Y') if siniestro.fecha_ocurrencia else "N/A")
        ws.cell(row=row_num, column=7, value=float(siniestro.monto_reclamado or 0))
        ws.cell(row=row_num, column=8, value=siniestro.get_estado_display() if hasattr(siniestro, 'get_estado_display') else siniestro.estado)

    # 6. Preparar la respuesta del navegador
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="Reporte_Siniestros_{timezone.now().strftime("%Y%m%d")}.xlsx"'
    
    wb.save(response)
    return response


# ==========================================
# VISTAS DE TRANSICIÓN DE ESTADOS (MODALS)
# ==========================================

@require_http_methods(["POST"])
def marcar_docs_incompletos(request, siniestro_id):
    """
    Marca el siniestro como documentos incompletos.
    Transición: reportado -> documentos_incompletos
    """
    siniestro = get_object_or_404(Siniestro, id=siniestro_id)
    
    try:
        # Obtener documentos faltantes del formulario
        docs_faltantes = request.POST.getlist('docs_faltantes')
        observaciones = request.POST.get('observaciones', '')
        
        # Mapeo de valores a nombres legibles
        docs_nombres = {
            'cedula': 'Cédula de identidad',
            'poliza': 'Copia de la póliza',
            'denuncia': 'Denuncia policial',
            'facturas': 'Facturas o comprobantes',
            'fotos': 'Fotografías del siniestro',
            'certificado_medico': 'Certificado médico',
            'otros': 'Otros documentos'
        }
        
        # Convertir a texto legible
        docs_texto = ', '.join([docs_nombres.get(d, d) for d in docs_faltantes])
        
        # Ejecutar transición FSM
        siniestro.marcar_documentos_incompletos()
        siniestro.documentos_faltantes = docs_texto
        if observaciones:
            siniestro.observaciones_internas += f"\n[{timezone.now().strftime('%d/%m/%Y %H:%M')}] Docs incompletos: {observaciones}"
        siniestro.save()
        
        messages.warning(request, f"Siniestro marcado como 'Documentos Incompletos'. Faltan: {docs_texto}")
        
    except Exception as e:
        messages.error(request, f"Error al cambiar estado: {str(e)}")
    
    return redirect('detalle_siniestro', siniestro_id=siniestro.id)


@require_http_methods(["POST"])
def confirmar_documentos(request, siniestro_id):
    """
    Confirma que los documentos están completos.
    Transición: reportado/documentos_incompletos -> documentos_completos
    """
    siniestro = get_object_or_404(Siniestro, id=siniestro_id)
    
    try:
        siniestro.marcar_documentos_completos()
        siniestro.documentos_faltantes = ''  # Limpiar documentos faltantes
        siniestro.save()
        
        messages.success(request, "Documentos marcados como completos. El siniestro está listo para enviar a la aseguradora.")
        
    except ValueError as e:
        messages.error(request, str(e))
    except Exception as e:
        messages.error(request, f"Error al confirmar documentos: {str(e)}")
    
    return redirect('detalle_siniestro', siniestro_id=siniestro.id)


@require_http_methods(["POST"])
def enviar_aseguradora(request, siniestro_id):
    """
    Envía el siniestro a la aseguradora.
    Transición: documentos_completos -> enviado_aseguradora
    """
    siniestro = get_object_or_404(Siniestro, id=siniestro_id)
    
    try:
        aseguradora = request.POST.get('aseguradora', '')
        correo = request.POST.get('correo_aseguradora', '')
        mensaje = request.POST.get('mensaje', '')
        
        # Ejecutar transición FSM
        siniestro.enviar_a_aseguradora()
        siniestro.aseguradora_destino = aseguradora
        siniestro.correo_aseguradora = correo
        siniestro.mensaje_aseguradora = mensaje
        siniestro.save()
        
        # TODO: Aquí se podría implementar el envío real del correo
        # send_mail(...)
        
        messages.success(request, f"Siniestro enviado a la aseguradora ({aseguradora}). Fecha límite de respuesta: {siniestro.fecha_limite_respuesta_aseguradora}")
        
    except Exception as e:
        messages.error(request, f"Error al enviar a aseguradora: {str(e)}")
    
    return redirect('detalle_siniestro', siniestro_id=siniestro.id)


@require_http_methods(["POST"])
def marcar_revision(request, siniestro_id):
    """
    Marca el siniestro como en revisión por la aseguradora.
    Transición: enviado_aseguradora -> en_revision
    """
    siniestro = get_object_or_404(Siniestro, id=siniestro_id)
    
    try:
        nota = request.POST.get('nota', '')
        
        siniestro.marcar_en_revision()
        if nota:
            siniestro.observaciones_internas += f"\n[{timezone.now().strftime('%d/%m/%Y %H:%M')}] En revisión: {nota}"
        siniestro.save()
        
        messages.info(request, "Siniestro marcado como 'En Revisión' por la aseguradora.")
        
    except Exception as e:
        messages.error(request, f"Error al marcar en revisión: {str(e)}")
    
    return redirect('detalle_siniestro', siniestro_id=siniestro.id)


@require_http_methods(["POST"])
def aprobar_siniestro_modal(request, siniestro_id):
    """
    Aprueba el siniestro con montos y documento de liquidación.
    Transición: en_revision -> aprobado
    """
    siniestro = get_object_or_404(Siniestro, id=siniestro_id)
    
    try:
        monto_aprobado = request.POST.get('monto_aprobado', 0)
        deducible = request.POST.get('deducible', 0)
        monto_final = request.POST.get('monto_final', 0)
        observaciones = request.POST.get('observaciones', '')
        documento = request.FILES.get('documento_liquidacion')
        
        # Validar que el documento sea PDF
        if documento and not validar_archivo_pdf(documento):
            messages.error(request, "El documento de liquidación debe ser un archivo PDF.")
            return redirect('detalle_siniestro', siniestro_id=siniestro.id)
        
        # Ejecutar transición FSM
        siniestro.aprobar()
        siniestro.monto_aprobado = float(monto_aprobado)
        siniestro.deducible_aplicado = float(deducible)
        siniestro.monto_liquidado_aseguradora = float(monto_final)
        siniestro.monto_a_pagar = float(monto_final)
        
        if observaciones:
            siniestro.observaciones_internas += f"\n[{timezone.now().strftime('%d/%m/%Y %H:%M')}] Aprobación: {observaciones}"
        
        siniestro.save()
        
        # Guardar documento de liquidación
        if documento:
            DocumentoSiniestro.objects.create(
                siniestro=siniestro,
                tipo='liquidacion',
                archivo=documento,
                descripcion='Documento de liquidación de aseguradora'
            )
        
        messages.success(request, f"Siniestro aprobado. Monto a pagar: ${monto_final}")
        
    except Exception as e:
        messages.error(request, f"Error al aprobar siniestro: {str(e)}")
    
    return redirect('detalle_siniestro', siniestro_id=siniestro.id)


@require_http_methods(["POST"])
def rechazar_siniestro(request, siniestro_id):
    """
    Rechaza el siniestro con razón y documento de respaldo.
    Transición: en_revision -> rechazado
    """
    siniestro = get_object_or_404(Siniestro, id=siniestro_id)
    
    try:
        razon_rechazo = request.POST.get('razon_rechazo', '')
        detalles = request.POST.get('detalles', '')
        documento = request.FILES.get('documento_respaldo')
        
        # Mapeo de razones
        razones_nombres = {
            'documentacion_insuficiente': 'Documentación insuficiente',
            'fuera_cobertura': 'Evento fuera de cobertura',
            'poliza_vencida': 'Póliza vencida o suspendida',
            'fraude_detectado': 'Posible fraude detectado',
            'informacion_incorrecta': 'Información incorrecta o inconsistente',
            'no_cumple_requisitos': 'No cumple requisitos de póliza',
            'otros': 'Otros'
        }
        
        razon_texto = razones_nombres.get(razon_rechazo, razon_rechazo)
        razon_completa = f"{razon_texto}: {detalles}"
        
        # Ejecutar transición FSM
        siniestro.rechazar(razon=razon_completa)
        siniestro.save()
        
        # Guardar documento de respaldo si existe
        if documento:
            DocumentoSiniestro.objects.update_or_create(
                siniestro=siniestro,
                tipo='otro',
                defaults={
                    'archivo': documento,
                    'descripcion': 'Documento de respaldo de rechazo'
                }
            )
        
        messages.error(request, f"Siniestro rechazado. Razón: {razon_texto}")
        
    except Exception as e:
        messages.error(request, f"Error al rechazar siniestro: {str(e)}")
    
    return redirect('detalle_siniestro', siniestro_id=siniestro.id)


@require_http_methods(["POST"])
def liquidar_siniestro(request, siniestro_id):
    """
    Confirma la liquidación del siniestro.
    Transición: aprobado -> liquidado
    """
    siniestro = get_object_or_404(Siniestro, id=siniestro_id)
    
    try:
        notas = request.POST.get('notas_liquidacion', '')
        
        # Ejecutar transición FSM
        monto = siniestro.monto_aprobado or 0
        deducible = siniestro.deducible_aplicado or 0
        siniestro.liquidar(monto_aprobado=monto, deducible=deducible)
        siniestro.notas_liquidacion = notas
        siniestro.save()
        
        messages.success(request, f"Siniestro liquidado. Monto a pagar: ${siniestro.monto_a_pagar}")
        
    except Exception as e:
        messages.error(request, f"Error al liquidar siniestro: {str(e)}")
    
    return redirect('detalle_siniestro', siniestro_id=siniestro.id)


@require_http_methods(["POST"])
def registrar_pago(request, siniestro_id):
    """
    Registra el pago del siniestro.
    Transición: liquidado -> pagado
    """
    siniestro = get_object_or_404(Siniestro, id=siniestro_id)
    
    try:
        fecha_pago = request.POST.get('fecha_pago')
        comprobante = request.FILES.get('comprobante_pago')
        pago_fuera_plazo = request.POST.get('pago_fuera_plazo') == 'on'
        observaciones = request.POST.get('observaciones', '')
        
        # Validar comprobante
        if comprobante and not (comprobante.name.lower().endswith('.pdf') or 
                                comprobante.name.lower().endswith('.jpg') or 
                                comprobante.name.lower().endswith('.jpeg') or
                                comprobante.name.lower().endswith('.png')):
            messages.error(request, "El comprobante debe ser PDF o imagen (JPG, PNG).")
            return redirect('detalle_siniestro', siniestro_id=siniestro.id)
        
        # Ejecutar transición FSM
        siniestro.registrar_pago()
        if fecha_pago:
            siniestro.fecha_pago_real = fecha_pago
        siniestro.pago_fuera_de_plazo = pago_fuera_plazo
        
        if observaciones:
            siniestro.observaciones_internas += f"\n[{timezone.now().strftime('%d/%m/%Y %H:%M')}] Pago: {observaciones}"
        
        siniestro.save()
        
        # Guardar comprobante de pago
        if comprobante:
            DocumentoSiniestro.objects.update_or_create(
                siniestro=siniestro,
                tipo='comprobante_pago',
                defaults={
                    'archivo': comprobante,
                    'descripcion': 'Comprobante de pago al reclamante'
                }
            )
        
        messages.success(request, "Pago registrado exitosamente. El siniestro puede ser cerrado.")
        
    except Exception as e:
        messages.error(request, f"Error al registrar pago: {str(e)}")
    
    return redirect('detalle_siniestro', siniestro_id=siniestro.id)


@require_http_methods(["POST"])
def cerrar_siniestro(request, siniestro_id):
    """
    Cierra el siniestro.
    Transición: pagado/rechazado -> cerrado
    """
    siniestro = get_object_or_404(Siniestro, id=siniestro_id)
    
    try:
        notas_cierre = request.POST.get('notas_cierre', '')
        
        # Ejecutar transición FSM
        siniestro.cerrar()
        siniestro.notas_cierre = notas_cierre
        siniestro.save()
        
        messages.success(request, f"Siniestro {siniestro.numero_siniestro} cerrado exitosamente.")
        
    except Exception as e:
        messages.error(request, f"Error al cerrar siniestro: {str(e)}")
    
    return redirect('detalle_siniestro', siniestro_id=siniestro.id)