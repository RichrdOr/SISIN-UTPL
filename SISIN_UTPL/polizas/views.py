from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, FileResponse
from django.forms import inlineformset_factory
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from .models import Poliza, RamoPoliza, Deducible, BienAsegurado, Zona
from .forms import RamoPolizaForm, PolizaForm, DeducibleForm
from usuarios.models import Usuario
import os
import logging
import csv
import json
from datetime import datetime, timedelta
from django.conf import settings
from openpyxl import Workbook
from openpyxl.styles import Font
from django.db import transaction

logger = logging.getLogger(__name__)

# Create your views here.

def ver_polizas(request):
    polizas = Poliza.objects.select_related('titular', 'bien').prefetch_related('ramos', 'deducibles').all()
    
    # Calculate statistics
    total_polizas = polizas.count()
    polizas_activas = polizas.filter(estado='activa').count()
    polizas_por_vencer = polizas.filter(estado='suspendida').count()
    prima_total = sum(poliza.prima for poliza in polizas)
    
    context = {
        'polizas': polizas,
        'total_polizas': total_polizas,
        'polizas_activas': polizas_activas,
        'polizas_por_vencer': polizas_por_vencer,
        'prima_total': prima_total
    }
    
    return render(request, 'asesora/polizas.html', context)

def descargar_pdf(request, poliza_id):
    poliza = get_object_or_404(Poliza, id=poliza_id)
    
    if poliza.pdf_file:
        # Si existe un PDF, descargarlo
        response = FileResponse(poliza.pdf_file, as_attachment=True)
        response['Content-Disposition'] = f'attachment; filename="{poliza.numero_poliza}.pdf"'
        return response
    else:
        # Si no existe PDF, generar uno simple
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from io import BytesIO
        import tempfile
        
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Título
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, 750, f"PÓLIZA DE SEGURO")
        
        # Información de la póliza
        p.setFont("Helvetica", 12)
        p.drawString(100, 700, f"Número de Póliza: {poliza.numero_poliza}")
        p.drawString(100, 680, f"Tipo de Póliza: {poliza.tipo_poliza}")
        p.drawString(100, 660, f"Aseguradora: {poliza.aseguradora}")
        p.drawString(100, 640, f"Prima: ${poliza.prima}")
        p.drawString(100, 620, f"Fecha de Inicio: {poliza.fecha_inicio}")
        p.drawString(100, 600, f"Fecha de Fin: {poliza.fecha_fin}")
        
        # Deducibles
        p.drawString(100, 560, "DEDUCIBLES:")
        y_pos = 540
        for deducible in poliza.deducibles.all():
            p.drawString(120, y_pos, f"- {deducible.concepto}: {deducible.porcentaje}%" if deducible.porcentaje else f"- {deducible.concepto}: ${deducible.monto}")
            y_pos -= 20
        
        p.save()
        
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{poliza.numero_poliza}.pdf"'
        return response

@csrf_exempt
@require_http_methods(["POST"])
def crear_poliza(request):
    try:
        with transaction.atomic():  # Si algo falla, no se guarda nada
            data = request.POST
            files = request.FILES
            
            logger.info(f"Datos recibidos: {dict(data)}")
            
            # 1. Obtener o crear la Zona
            zona_nombre = data.get('zona', 'Sin especificar')
            zona, _ = Zona.objects.get_or_create(nombre=zona_nombre)
            
            # 2. Mapear tipo de bien a entero
            tipo_bien_map = {
                'Residencial': 1,
                'Comercial': 2,
                'Industrial': 3,
            }
            tipo_bien_str = data.get('tipo_bien', 'Residencial')
            tipo_bien_int = tipo_bien_map.get(tipo_bien_str, 1)
            
            # 3. Crear el Bien Asegurado
            bien = BienAsegurado.objects.create(
                descripcion=data.get('descripcion_bien', ''),
                estado=1,  # Estado activo por defecto
                tipo_bien=tipo_bien_int,
                zona=zona,
                valor=data.get('valor_bien', 0) or 0
            )

            # 4. Obtener o crear un usuario titular
            # Primero intentamos obtener el primer usuario existente
            titular = Usuario.objects.first()
            if not titular:
                # Si no existe ningún usuario, creamos uno por defecto
                titular, created = Usuario.objects.get_or_create(
                    email='usuario@default.com',
                    defaults={
                        'nombre': 'Usuario',
                        'apellido': 'Por Defecto',
                        'telefono': ''
                    }
                )
                if created:
                    logger.info(f"Usuario por defecto creado con id: {titular.id}")

            # 5. Crear la Póliza
            poliza = Poliza.objects.create(
                numero_poliza=data.get('numero_poliza'),
                aseguradora=data.get('aseguradora', ''),
                tipo_poliza=tipo_bien_str,  # Usar el tipo de bien como tipo de póliza
                fecha_emision=data.get('fecha_emision'),
                fecha_vencimiento=data.get('fecha_fin'),  # fecha_vencimiento = fecha_fin
                fecha_inicio=data.get('fecha_inicio'),
                fecha_fin=data.get('fecha_fin'),
                prima=data.get('total_prima', 0) or 0,
                cobertura=data.get('descripcion_bien', ''),  # Usar descripción como cobertura
                bien=bien,
                titular=titular,  # Usar el usuario obtenido o creado
                pdf_file=files.get('pdf_file')
            )

            # 6. Procesar Ramos (JSON enviado desde JS)
            ramos_data = json.loads(data.get('ramos_json', '[]'))
            for item in ramos_data:
                RamoPoliza.objects.create(
                    poliza=poliza,
                    grupo=item.get('grupo', ''),
                    subgrupo=item.get('subgrupo', ''),
                    ramo=item.get('ramo', ''),
                    suma_asegurada=item.get('suma_asegurada', 0) or 0,
                    prima=0,  # Valor por defecto
                    base_imponible=0,
                    iva=0,
                    total_facturado=0,
                    deducible_minimo=0,
                    deducible_porcentaje=item.get('deducible_porcentaje', 0) or 0
                )

            # 7. Procesar Deducibles (JSON enviado desde JS)
            deducibles_data = json.loads(data.get('deducibles_json', '[]'))
            for item in deducibles_data:
                # Intentar convertir monto a decimal, si falla usar 0
                monto_str = item.get('monto', '0')
                try:
                    # Remover caracteres no numéricos excepto punto y coma
                    monto_clean = ''.join(c for c in str(monto_str) if c.isdigit() or c in '.,')
                    monto_clean = monto_clean.replace(',', '.')
                    monto = float(monto_clean) if monto_clean else 0
                except (ValueError, TypeError):
                    monto = 0
                    
                Deducible.objects.create(
                    poliza=poliza,
                    concepto=item.get('concepto', ''),
                    monto=monto
                )

            logger.info(f"Póliza {poliza.numero_poliza} creada exitosamente")
            # Agregar mensaje de éxito para mostrar después de la redirección
            messages.success(request, f'¡Póliza {poliza.numero_poliza} creada exitosamente!')
            return JsonResponse({'success': True, 'message': 'Póliza y Bien creados con éxito', 'poliza_id': poliza.id})

    except Exception as e:
        logger.error(f"Error al crear póliza: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        messages.error(request, f'Error al crear la póliza: {str(e)}')
        return JsonResponse({'success': False, 'message': str(e)})

@csrf_exempt
@require_http_methods(["DELETE"])
def eliminar_poliza(request, poliza_id):
    try:
        poliza = get_object_or_404(Poliza, id=poliza_id)
        logger.info(f"Intentando eliminar póliza {poliza_id}: {poliza.numero_poliza}")
        
        # Eliminar deducibles relacionados primero
        poliza.deducibles.all().delete()
        
        # Eliminar la póliza
        poliza.delete()
        
        logger.info(f"Póliza {poliza_id} eliminada exitosamente")
        return JsonResponse({'success': True, 'message': 'Póliza eliminada exitosamente'})
    except Poliza.DoesNotExist:
        logger.error(f"La póliza {poliza_id} no existe")
        return JsonResponse({'success': False, 'message': 'La póliza no existe'})
    except Exception as e:
        logger.error(f"Error al eliminar póliza {poliza_id}: {str(e)}")
        return JsonResponse({'success': False, 'message': f'Error al eliminar la póliza: {str(e)}'})

@csrf_exempt
@require_http_methods(["POST"])
def editar_poliza(request, poliza_id):
    poliza = get_object_or_404(Poliza, id=poliza_id)
    
    try:
        data = request.POST
        pdf_file = request.FILES.get('pdf_file')
        
        # Actualizar póliza
        poliza.tipo_poliza = data.get('tipo_poliza', poliza.tipo_poliza)
        poliza.fecha_inicio = data.get('fecha_inicio', poliza.fecha_inicio)
        poliza.fecha_fin = data.get('fecha_fin', poliza.fecha_fin)
        poliza.prima = data.get('prima', poliza.prima)
        
        # Actualizar PDF si se sube uno nuevo
        if pdf_file:
            poliza.pdf_file = pdf_file
            
        poliza.save()
        
        # Actualizar deducibles
        poliza.deducibles.all().delete()
        deducibles_data = request.POST.getlist('deducibles')
        for ded_data in deducibles_data:
            if ded_data:
                Deducible.objects.create(
                    poliza=poliza,
                    concepto=ded_data.get('concepto', ''),
                    monto=ded_data.get('monto', 0),
                    porcentaje=ded_data.get('porcentaje')
                )
        
        return JsonResponse({'success': True, 'message': 'Póliza actualizada exitosamente'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

def obtener_poliza(request, poliza_id):
    poliza = get_object_or_404(Poliza, id=poliza_id)
    
    data = {
        'id': poliza.id,
        'numero_poliza': poliza.numero_poliza,
        'tipo_poliza': poliza.tipo_poliza,
        'fecha_inicio': poliza.fecha_inicio.strftime('%Y-%m-%d') if poliza.fecha_inicio else '',
        'fecha_fin': poliza.fecha_fin.strftime('%Y-%m-%d') if poliza.fecha_fin else '',
        'prima': str(poliza.prima),
        'deducibles': [
            {
                'concepto': d.concepto,
                'monto': str(d.monto),
                'porcentaje': str(d.porcentaje) if d.porcentaje else None
            } for d in poliza.deducibles.all()
        ]
    }
    
    return JsonResponse(data)


def formulario_crear_poliza(request):
    """Vista para mostrar el formulario de crear póliza"""
    return render(request, 'asesora/crear_poliza.html')


def crear_poliza_old(request):
    # 1. Definimos el formset
    RamoFormSet = inlineformset_factory(
        Poliza, 
        RamoPoliza, 
        form=RamoPolizaForm,
        extra=1, 
        can_delete=True
    )
    
    if request.method == 'POST':
        # Aquí recibimos los datos
        form = PolizaForm(request.POST)
        formset = RamoFormSet(request.POST)
        
        # Por ahora, como solo quieres que redirija sin guardar:
        return redirect('nombre_de_tu_url_de_exito') 
        
    else:
        # Carga inicial (GET)
        form = PolizaForm()
        formset = RamoFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'clientes': [], # O Cliente.objects.all()
    }
    
    return render(request, 'asesora/crear_poliza.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def exportar_excel(request):
    try:
        polizas = Poliza.objects.select_related('titular', 'bien').prefetch_related('deducibles').all()
        
        # Crear archivo Excel
        wb = Workbook()
        ws = wb.active
        ws.title = "Pólizas"
        
        # Estilos
        header_font = Font(bold=True)
        
        # Encabezados
        headers = ['Nº Póliza', 'Tipo Póliza', 'Titular', 'Fecha Inicio', 'Fecha Fin', 'Prima', 'Estado', 'Aseguradora']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
        
        # Datos
        for row, poliza in enumerate(polizas, 2):
            ws.cell(row=row, column=1, value=poliza.numero_poliza)
            ws.cell(row=row, column=2, value=poliza.tipo_poliza)
            ws.cell(row=row, column=3, value=str(poliza.titular))
            ws.cell(row=row, column=4, value=poliza.fecha_inicio.strftime('%d/%m/%Y') if poliza.fecha_inicio else '')
            ws.cell(row=row, column=5, value=poliza.fecha_fin.strftime('%d/%m/%Y') if poliza.fecha_fin else '')
            ws.cell(row=row, column=6, value=float(poliza.prima))
            ws.cell(row=row, column=7, value=poliza.get_estado_display())
            ws.cell(row=row, column=8, value=poliza.aseguradora)
        
        # Guardar en memoria
        from io import BytesIO
        excel_buffer = BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)
        
        # Respuesta
        response = HttpResponse(
            excel_buffer.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="polizas_export.xlsx"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error exportando Excel: {e}")
        return JsonResponse({'success': False, 'message': f'Error al exportar: {str(e)}'})

@csrf_exempt
@require_http_methods(["POST"])
def renovar_vencidas(request):
    try:
        # Buscar pólizas vencidas o por vencer
        today = datetime.now().date()
        expired_policies = Poliza.objects.filter(
            fecha_fin__lt=today,
            estado__in=['activa', 'suspendida']
        )
        
        renewed_count = 0
        for poliza in expired_policies:
            # Renovar por 1 año
            new_end_date = poliza.fecha_fin + timedelta(days=365)
            poliza.fecha_fin = new_end_date
            poliza.fecha_inicio = poliza.fecha_fin  # Ajustar fecha de inicio
            poliza.estado = 'activa'
            poliza.numero_poliza = f"REN-{poliza.numero_poliza}"
            poliza.save()
            renewed_count += 1
        
        logger.info(f"Se renovaron {renewed_count} pólizas")
        
        return JsonResponse({
            'success': True, 
            'message': f'Se renovaron {renewed_count} pólizas exitosamente',
            'renewed_count': renewed_count
        })
        
    except Exception as e:
        logger.error(f"Error renovando pólizas vencidas: {e}")
        return JsonResponse({'success': False, 'message': f'Error al renovar: {str(e)}'})