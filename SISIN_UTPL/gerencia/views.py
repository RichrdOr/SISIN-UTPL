import csv
import io
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db.models import Sum, Q, Count
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.core.files.base import ContentFile
from django.contrib import messages
from siniestros.models import Siniestro
from django.contrib.auth.models import User, Group
from polizas.models import Poliza
from .models import ParametroSistema
from datetime import date

from django.db.models.functions import TruncMonth
# Librerías para PDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Importamos modelos
from siniestros.models import Siniestro
from polizas.models import Poliza
from reportes.models import Reporte
from .models import ParametroSistema, ReglaDeducible

# 1. DASHBOARD
def dashboard_gerencial(request):
    # 1. Configuración y KPIs
    config, _ = ParametroSistema.objects.get_or_create(id=1)
    
    total_siniestros = Siniestro.objects.count()
    
    # Conteos básicos
    # Abiertos incluye TODO lo que no está cerrado (tanto al día como vencidos)
    abiertos_total = Siniestro.objects.filter(estado__in=['reportado', 'en_revision']).count()
    cerrados = Siniestro.objects.filter(estado__in=['pagado', 'rechazado']).count()
    
    # Cálculo de Vencidos Reales
    dias_limite = config.dias_reporte_siniestro 
    fecha_limite = timezone.now().date() - timedelta(days=dias_limite)
    cantidad_vencidos_real = Siniestro.objects.filter(
        fecha_reporte__lt=fecha_limite
    ).exclude(estado__in=['pagado', 'rechazado']).count()
    
    # KPI para la tarjeta de alerta (depende del checkbox)
    mostrar_vencidos = cantidad_vencidos_real if config.alerta_fuera_plazo else 0

    # --- LÓGICA PARA GRÁFICO CIRCULAR (ESTADO GENERAL) ---
    # Desglosamos "Abiertos" en "Al día" vs "Vencidos" para que el gráfico sume 100% perfecto
    # Abiertos (Al día) = Total Abiertos - Vencidos
    abiertos_al_dia = abiertos_total - cantidad_vencidos_real
    if abiertos_al_dia < 0: abiertos_al_dia = 0 # Seguridad
    
    # Lista de datos para el gráfico: [Verdes, Amarillos, Rojos]
    data_estado_general = [cerrados, abiertos_al_dia, cantidad_vencidos_real]
    # -----------------------------------------------------

    raw_monto_siniestros = Siniestro.objects.aggregate(total=Sum('monto_aprobado'))['total'] or 0
    raw_monto_polizas = Poliza.objects.aggregate(total=Sum('prima'))['total'] or 0

    # --- LÓGICA PARA GRÁFICA DE BARRAS (Siniestros vs Pólizas - 6 meses) ---
    hoy = timezone.now().date()
    fecha_inicio_grafica = hoy - timedelta(days=180)

    siniestros_por_mes = Siniestro.objects.filter(fecha_reporte__gte=fecha_inicio_grafica)\
        .annotate(mes=TruncMonth('fecha_reporte')).values('mes').annotate(total=Count('id')).order_by('mes')

    polizas_por_mes = Poliza.objects.filter(fecha_inicio__gte=fecha_inicio_grafica)\
        .annotate(mes=TruncMonth('fecha_inicio')).values('mes').annotate(total=Count('id')).order_by('mes')

    datos_consolidados = {}
    for i in range(5, -1, -1):
        mes_ref = (hoy.replace(day=1) - timedelta(days=30 * i))
        clave_mes = mes_ref.strftime("%Y-%m")
        datos_consolidados[clave_mes] = {'siniestros': 0, 'polizas': 0}

    for item in siniestros_por_mes:
        if item['mes']:
            clave = item['mes'].strftime("%Y-%m")
            if clave in datos_consolidados: datos_consolidados[clave]['siniestros'] = item['total']

    for item in polizas_por_mes:
        if item['mes']:
            clave = item['mes'].strftime("%Y-%m")
            if clave in datos_consolidados: datos_consolidados[clave]['polizas'] = item['total']

    chart_labels = sorted(datos_consolidados.keys())
    data_siniestros = [datos_consolidados[k]['siniestros'] for k in chart_labels]
    data_polizas = [datos_consolidados[k]['polizas'] for k in chart_labels]

    context = {
        'kpis': {
            'total': total_siniestros,
            'abiertos': abiertos_total,
            'cerrados': cerrados,
            'vencidos': mostrar_vencidos,
            'hay_vencidos_reales': cantidad_vencidos_real > 0,
            'monto_siniestros': "{:,.0f}".format(raw_monto_siniestros),
            'monto_polizas': "{:,.0f}".format(raw_monto_polizas),
        },
        'config': config,
        'chart_labels': chart_labels, 
        'data_siniestros': data_siniestros,
        'data_polizas': data_polizas,
        'data_estado_general': data_estado_general # <--- ENVIAMOS LOS DATOS NUEVOS
    }
    return render(request, 'gerencia/dashboard.html', context)

# 2. REPORTES (Con Exportación Directa)
# En gerencia/views.py

def reportes_gerencial(request):
    siniestros_list = Siniestro.objects.select_related('poliza', 'reclamante').all().order_by('-fecha_reporte')

    # --- 1. DATOS PARA LOS FILTROS (DINÁMICOS) ---
    lista_tipos = Siniestro.objects.values_list('tipo_bien', flat=True).distinct().order_by('tipo_bien')
    lista_estados = Siniestro.ESTADO_CHOICES 

    # --- 2. APLICAR FILTROS ---
    f_estado = request.GET.get('estado')
    f_tipo = request.GET.get('tipo')
    f_fecha = request.GET.get('fecha_inicio')

    if f_estado and f_estado != 'Todos':
        siniestros_list = siniestros_list.filter(estado=f_estado)
    
    if f_tipo and f_tipo != 'Todos':
        siniestros_list = siniestros_list.filter(tipo_bien=f_tipo)

    if f_fecha:
        siniestros_list = siniestros_list.filter(fecha_reporte__gte=f_fecha)

    # --- 3. EXPORTACIÓN (ESTO ES LO QUE FALTABA) ---
    export_format = request.GET.get('export') # Detectamos si el botón pulsado envió ?export=csv o pdf
    
    if export_format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="reporte_siniestros_{timezone.now().date()}.csv"'
        
        writer = csv.writer(response)
        # Encabezados del CSV
        writer.writerow(['N Caso', 'Estado', 'Bien', 'Poliza', 'Fecha', 'Reclamado', 'Aprobado'])
        # Datos filtrados
        for s in siniestros_list:
            writer.writerow([
                s.numero_siniestro, 
                s.estado, 
                s.tipo_bien, 
                s.poliza.numero_poliza, 
                s.fecha_reporte, 
                s.monto_reclamado, 
                s.monto_aprobado or 0
            ])
        return response # Retornamos el archivo DIRECTAMENTE, deteniendo la carga de la página

    elif export_format == 'pdf':
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="reporte_siniestros_{timezone.now().date()}.pdf"'
        
        p = canvas.Canvas(response, pagesize=letter)
        p.setFont("Helvetica-Bold", 14)
        p.drawString(30, 750, "Reporte de Siniestralidad")
        p.setFont("Helvetica", 10)
        p.drawString(30, 735, f"Generado: {timezone.now().strftime('%Y-%m-%d %H:%M')}")
        
        y = 700
        # Encabezados PDF
        p.drawString(30, y, "N Caso")
        p.drawString(100, y, "Estado")
        p.drawString(200, y, "Bien")
        p.drawString(350, y, "Monto Reclamado")
        p.line(30, y-5, 500, y-5)
        y -= 20
        
        for s in siniestros_list:
            if y < 50: # Nueva página si se acaba el espacio
                p.showPage()
                y = 750
            p.drawString(30, y, str(s.numero_siniestro))
            p.drawString(100, y, s.estado)
            p.drawString(200, y, str(s.tipo_bien)[:25]) # Recortamos texto largo
            p.drawString(350, y, f"${s.monto_reclamado}")
            y -= 15
            
        p.showPage()
        p.save()
        return response # Retornamos el archivo DIRECTAMENTE

    # --- 4. RENDERIZADO NORMAL (Solo si no se exporta) ---
    context = {
        'siniestros': siniestros_list,
        'filtros': request.GET,
        'lista_tipos': lista_tipos,
        'lista_estados': lista_estados
    }
    return render(request, 'gerencia/reportes.html', context)

# 3. PARÁMETROS
def parametros_gerencial(request):
    config, created = ParametroSistema.objects.get_or_create(id=1)
    reglas = ReglaDeducible.objects.all()
    
    # --- NUEVO: Obtener tipos de póliza únicos de la BD ---
    # Esto busca en la tabla Polizas todos los 'tipo_poliza' distintos que se han registrado
    lista_tipos_poliza = Poliza.objects.values_list('tipo_poliza', flat=True).distinct().order_by('tipo_poliza')

    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'guardar_general':
            config.dias_reporte_siniestro = request.POST.get('dias_reporte')
            config.dias_respuesta_seguro = request.POST.get('dias_respuesta')
            config.dias_pago = request.POST.get('dias_pago')
            config.descuento_pronto_pago = request.POST.get('descuento_valor')
            config.plazo_max_descuento = request.POST.get('descuento_plazo')
            config.alerta_fuera_plazo = 'alerta_plazo' in request.POST
            config.alerta_pagos_vencidos = 'alerta_pagos' in request.POST
            config.save()
            messages.success(request, "Configuración guardada.")

        elif accion == 'nueva_regla':
            ReglaDeducible.objects.create(
                tipo_poliza=request.POST.get('tipo_poliza'),
                descripcion=request.POST.get('descripcion'),
                minimo=request.POST.get('minimo') or 0,
                maximo=request.POST.get('maximo') or 0
            )
            messages.success(request, "Regla agregada.")

        # C. Editar Regla (NUEVO)
        elif accion == 'editar_regla':
            id_regla = request.POST.get('regla_id')
            regla = get_object_or_404(ReglaDeducible, id=id_regla)
            
            regla.tipo_poliza = request.POST.get('tipo_poliza')
            regla.descripcion = request.POST.get('descripcion')
            regla.minimo = request.POST.get('minimo') or 0
            regla.maximo = request.POST.get('maximo') or 0
            regla.save()
            
            messages.success(request, "Regla actualizada correctamente.")

        elif accion == 'eliminar_regla':
            id_regla = request.POST.get('regla_id')
            ReglaDeducible.objects.filter(id=id_regla).delete()
            messages.warning(request, "Regla eliminada.")

        return redirect('gerencia:parametros_gerencial')
    
    context = {
        'config': config, 
        'reglas': reglas,
        'tipos_poliza': lista_tipos_poliza # <--- Enviamos la lista al HTML
    }
    return render(request, 'gerencia/parametros.html', context)

# 4. USUARIOS
def usuarios_gerencial(request):
    # --- 1. GARANTIZAR QUE EXISTAN ROLES (Solo para que no salga vacío al inicio) ---
    if not Group.objects.exists():
        roles_iniciales = ['Administrador', 'Gerente', 'Analista', 'Auditor']
        for role in roles_iniciales:
            Group.objects.create(name=role)
    
    # Obtener roles de la BD para el Select
    roles_db = Group.objects.all().order_by('name')

    if request.method == 'POST':
        nombre = request.POST.get('userName')
        email = request.POST.get('userEmail')
        rol_id = request.POST.get('userRole') # Ahora recibimos el ID del grupo
        
        if not User.objects.filter(username=email).exists():
            # Crear usuario
            nuevo_usuario = User.objects.create_user(username=email, email=email, password='password123')
            nuevo_usuario.first_name = nombre
            
            # Asignar Rol (Grupo) seleccionado
            if rol_id:
                grupo_seleccionado = Group.objects.get(id=rol_id)
                nuevo_usuario.groups.add(grupo_seleccionado)
                
                # Lógica de permisos según el nombre del grupo
                if grupo_seleccionado.name == 'Administrador':
                    nuevo_usuario.is_superuser = True
                    nuevo_usuario.is_staff = True
                else:
                    # Para que puedan entrar al panel, deben ser staff
                    nuevo_usuario.is_staff = True
            
            nuevo_usuario.save()
            messages.success(request, f"Usuario {nombre} creado con rol {grupo_seleccionado.name}.")
        else:
            messages.error(request, "El usuario ya existe.")
        
        return redirect('gerencia:usuarios_gerencial')

    # Listar usuarios y precargar sus grupos para mostrar en la tabla
    usuarios = User.objects.prefetch_related('groups').all().order_by('-date_joined')
    
    context = {
        'usuarios': usuarios,
        'roles': roles_db # <--- Enviamos la lista de roles al template
    }
    return render(request, 'gerencia/usuarios.html', context)

# 5. EXPORTACIONES (Con Tipos Dinámicos)
def exportaciones_gerencial(request):
    tipos_reporte = Reporte.TIPO_CHOICES

    if request.method == 'POST':
        tipo_reporte = request.POST.get('report_type')
        formato = request.POST.get('format')
        
        usuario_responsable = request.user if request.user.is_authenticated else User.objects.first()
        if not usuario_responsable:
            usuario_responsable = User.objects.create_user('admin_sistema', 'admin@sys.com', 'admin')

        archivo_final = None
        nombre_archivo = ""
        
        # --- 1. OBTENER LOS DATOS REALES DE LA BD (Igual que antes) ---
        headers = []
        data_rows = []
        
        if tipo_reporte == 'siniestros':
            headers = ['N°', 'Estado', 'Bien', 'Póliza', 'Fecha', 'Reclamado', 'Aprobado']
            objetos = Siniestro.objects.select_related('poliza').all().order_by('-fecha_reporte')
            for obj in objetos:
                data_rows.append([str(obj.numero_siniestro), obj.estado, obj.tipo_bien[:15], obj.poliza.numero_poliza, str(obj.fecha_reporte), f"${obj.monto_reclamado}", f"${obj.monto_aprobado or 0}"])
                
        elif tipo_reporte == 'polizas':
            headers = ['N° Póliza', 'Tipo', 'Asegurado', 'Inicio', 'Fin', 'Prima', 'Estado']
            objetos = Poliza.objects.select_related('asegurado').all().order_by('-fecha_inicio')
            for obj in objetos:
                nombre = f"{obj.asegurado.first_name} {obj.asegurado.last_name}" if obj.asegurado else "N/A"
                data_rows.append([obj.numero_poliza, obj.tipo_poliza, nombre[:20], str(obj.fecha_inicio), str(obj.fecha_fin), f"${obj.prima}", obj.estado])

        elif tipo_reporte == 'usuarios':
             headers = ['Usuario', 'Email', 'Nombre', 'Staff', 'Activo', 'Registro']
             objetos = User.objects.all().order_by('-date_joined')
             for obj in objetos:
                 data_rows.append([obj.username, obj.email, obj.first_name, "SI" if obj.is_staff else "NO", "SI" if obj.is_active else "NO", str(obj.date_joined.date())])

        # --- 2. GENERAR PDF (Igual que antes) ---
        if formato == 'pdf':
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            p.setFont("Helvetica-Bold", 14)
            p.drawString(30, 750, f"REPORTE: {tipo_reporte.upper()}")
            p.setFont("Helvetica", 10)
            p.drawString(30, 735, f"Generado por: {usuario_responsable.username}")
            
            y = 700
            p.setFont("Helvetica-Bold", 8)
            ancho_columna = 550 / (len(headers) or 1)
            x_offset = 30
            for h in headers:
                p.drawString(x_offset, y, h)
                x_offset += ancho_columna
            p.line(30, y-5, 580, y-5)
            y -= 20
            
            p.setFont("Helvetica", 8)
            for row in data_rows:
                if y < 50:
                    p.showPage()
                    y = 750
                    p.setFont("Helvetica", 8)
                x_offset = 30
                for cell in row:
                    p.drawString(x_offset, y, str(cell))
                    x_offset += ancho_columna
                y -= 15
            
            p.save()
            buffer.seek(0)
            archivo_final = ContentFile(buffer.getvalue())
            nombre_archivo = f"{tipo_reporte}_{timezone.now().strftime('%H%M%S')}.pdf"

        # --- 3. GENERAR EXCEL REAL (.xlsx) ---
        elif formato == 'excel':
            import openpyxl # Importamos aquí para no fallar si no lo usas en otro lado
            
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = tipo_reporte.capitalize()
            
            # Encabezados de reporte
            ws.append(['REPORTE DEL SISTEMA', tipo_reporte.upper()])
            ws.append(['GENERADO POR', usuario_responsable.username])
            ws.append(['FECHA', str(timezone.now().date())])
            ws.append([]) # Fila vacía
            
            # Tabla de datos
            ws.append(headers) # Cabeceras de columna
            for row in data_rows:
                ws.append(row) # Filas
            
            # Guardar en binario
            buffer = io.BytesIO()
            wb.save(buffer)
            buffer.seek(0)
            archivo_final = ContentFile(buffer.getvalue())
            nombre_archivo = f"{tipo_reporte}_{timezone.now().strftime('%H%M%S')}.xlsx"

        # --- 4. GENERAR CSV (Respaldo) ---
        else:
            buffer = io.StringIO()
            writer = csv.writer(buffer)
            writer.writerow(['REPORTE', tipo_reporte.upper()])
            writer.writerow(headers)
            writer.writerows(data_rows)
            archivo_final = ContentFile(buffer.getvalue().encode('utf-8'))
            nombre_archivo = f"{tipo_reporte}_{timezone.now().strftime('%H%M%S')}.csv"

        # Guardar y Redirigir
        nuevo_reporte = Reporte(
            titulo=f"Reporte {tipo_reporte.capitalize()}",
            tipo=tipo_reporte,
            generado_por=usuario_responsable
        )
        nuevo_reporte.archivo.save(nombre_archivo, archivo_final)
        nuevo_reporte.save()
        
        messages.success(request, f"Reporte generado exitosamente.")
        return redirect('gerencia:exportaciones_gerencial')

    reportes = Reporte.objects.select_related('generado_por').all().order_by('-fecha_generacion')
    
    context = {
        'reportes': reportes,
        'tipos_reporte': tipos_reporte
    }
    return render(request, 'gerencia/exportaciones.html', context)
