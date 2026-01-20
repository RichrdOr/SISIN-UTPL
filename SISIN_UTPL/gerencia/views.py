import csv
import io
import openpyxl 
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db.models import Sum, Q, Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta, date
from django.core.files.base import ContentFile
from django.contrib import messages

# --- IMPORTACIONES CRÍTICAS PARA EVITAR CONFUSIONES ---
# 1. El usuario que inicia sesión y tiene permisos (Django default)
from django.contrib.auth.models import User as SystemUser, Group 
# 2. El cliente/titular que tiene pólizas (Tu modelo personalizado)
from usuarios.models import Usuario as ClienteUsuario 

# Librerías para PDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Importamos modelos del negocio
from siniestros.models import Siniestro
from polizas.models import Poliza
from reportes.models import Reporte
from .models import ParametroSistema, ReglaDeducible

# 1. DASHBOARD
def dashboard_gerencial(request):
    config, _ = ParametroSistema.objects.get_or_create(id=1)
    
    total_siniestros = Siniestro.objects.count()
    
    # Estados definidos en siniestros/models.py
    estados_abiertos = [
        'reportado', 'documentos_incompletos', 'documentos_completos', 
        'enviado_aseguradora', 'en_revision', 'aprobado', 'liquidado'
    ]
    estados_cerrados = [
        'rechazado', 'pagado', 'cerrado', 'fuera_plazo'
    ]
    
    abiertos_total = Siniestro.objects.filter(estado__in=estados_abiertos).count()
    cerrados = Siniestro.objects.filter(estado__in=estados_cerrados).count()
    
    # Cálculo de Vencidos
    dias_limite = config.dias_reporte_siniestro 
    fecha_limite = timezone.now().date() - timedelta(days=dias_limite)
    
    cantidad_vencidos_real = Siniestro.objects.filter(
        fecha_reporte__lt=fecha_limite
    ).exclude(estado__in=estados_cerrados).count()
    
    mostrar_vencidos = cantidad_vencidos_real if config.alerta_fuera_plazo else 0

    # Gráfica Dona
    abiertos_al_dia = abiertos_total - cantidad_vencidos_real
    if abiertos_al_dia < 0: abiertos_al_dia = 0
    data_estado_general = [cerrados, abiertos_al_dia, cantidad_vencidos_real]

    # Sumatorias Financieras
    raw_monto_siniestros = Siniestro.objects.aggregate(total=Sum('monto_aprobado'))['total'] or 0
    raw_monto_polizas = Poliza.objects.aggregate(total=Sum('prima'))['total'] or 0

    # --- Gráfica Comparativa (6 Meses) ---
    hoy = timezone.now().date()
    # Ajustamos el filtro para que coincida mejor con la gráfica (150 días aprox 5 meses)
    fecha_inicio_grafica = hoy - timedelta(days=180)

    # Agrupación por Mes - Siniestros
    siniestros_por_mes = Siniestro.objects.filter(fecha_reporte__gte=fecha_inicio_grafica)\
        .annotate(mes=TruncMonth('fecha_reporte')).values('mes').annotate(total=Count('id')).order_by('mes')

    # Agrupación por Mes - Pólizas (Usando fecha_inicio)
    polizas_por_mes = Poliza.objects.filter(fecha_inicio__gte=fecha_inicio_grafica)\
        .annotate(mes=TruncMonth('fecha_inicio')).values('mes').annotate(total=Count('id')).order_by('mes')

    # Consolidación (Crear casillas vacías para los últimos 6 meses)
    datos_consolidados = {}
    for i in range(5, -1, -1):
        # Usamos 30 días como aproximación de mes para generar las llaves
        mes_ref = (hoy.replace(day=1) - timedelta(days=30 * i))
        clave_mes = mes_ref.strftime("%Y-%m")
        datos_consolidados[clave_mes] = {'siniestros': 0, 'polizas': 0}

    # Llenado de datos con PROTECCIÓN (La corrección está aquí)
    for item in siniestros_por_mes:
        if item['mes']:
            clave = item['mes'].strftime("%Y-%m")
            # Solo guardamos si el mes existe en nuestra gráfica (evita KeyError)
            if clave in datos_consolidados:
                datos_consolidados[clave]['siniestros'] = item['total']

    for item in polizas_por_mes:
        if item['mes']:
            clave = item['mes'].strftime("%Y-%m")
            # Solo guardamos si el mes existe en nuestra gráfica
            if clave in datos_consolidados:
                datos_consolidados[clave]['polizas'] = item['total']

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
        'data_estado_general': data_estado_general
    }
    return render(request, 'gerencia/dashboard.html', context)

# 2. REPORTES
def reportes_gerencial(request):
    # Relación: Siniestro -> Poliza
    # Siniestro -> Reclamante (ClienteUsuario)
    siniestros_list = Siniestro.objects.select_related('poliza', 'reclamante').all().order_by('-fecha_reporte')

    # Filtros
    lista_tipos = Siniestro.objects.values_list('tipo_bien', flat=True).distinct().order_by('tipo_bien')
    lista_estados = Siniestro.ESTADO_CHOICES 

    f_estado = request.GET.get('estado')
    f_tipo = request.GET.get('tipo')
    f_fecha = request.GET.get('fecha_inicio')

    if f_estado and f_estado != 'Todos':
        siniestros_list = siniestros_list.filter(estado=f_estado)
    if f_tipo and f_tipo != 'Todos':
        siniestros_list = siniestros_list.filter(tipo_bien=f_tipo)
    if f_fecha:
        siniestros_list = siniestros_list.filter(fecha_reporte__gte=f_fecha)

    # Exportación Directa (Botones rápidos en la tabla)
    export_format = request.GET.get('export')
    
    if export_format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="reporte_siniestros_{timezone.now().date()}.csv"'
        writer = csv.writer(response)
        writer.writerow(['N Caso', 'Estado', 'Bien', 'Poliza', 'Fecha', 'Reclamado', 'Aprobado'])
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
        return response

    elif export_format == 'pdf':
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="reporte_siniestros_{timezone.now().date()}.pdf"'
        p = canvas.Canvas(response, pagesize=letter)
        p.setFont("Helvetica-Bold", 14)
        p.drawString(30, 750, "Reporte de Siniestralidad")
        p.setFont("Helvetica", 10)
        p.drawString(30, 735, f"Generado: {timezone.now().strftime('%Y-%m-%d %H:%M')}")
        y = 700
        p.drawString(30, y, "N Caso")
        p.drawString(100, y, "Estado")
        p.drawString(200, y, "Bien")
        p.drawString(350, y, "Monto Reclamado")
        p.line(30, y-5, 500, y-5)
        y -= 20
        for s in siniestros_list:
            if y < 50:
                p.showPage()
                y = 750
            p.drawString(30, y, str(s.numero_siniestro))
            p.drawString(100, y, s.estado)
            p.drawString(200, y, str(s.tipo_bien)[:25])
            p.drawString(350, y, f"${s.monto_reclamado}")
            y -= 15
        p.showPage()
        p.save()
        return response

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
        
        elif accion == 'editar_regla':
            id_regla = request.POST.get('regla_id')
            regla = get_object_or_404(ReglaDeducible, id=id_regla)
            regla.tipo_poliza = request.POST.get('tipo_poliza')
            regla.descripcion = request.POST.get('descripcion')
            regla.minimo = request.POST.get('minimo') or 0
            regla.maximo = request.POST.get('maximo') or 0
            regla.save()
            messages.success(request, "Regla actualizada.")

        elif accion == 'eliminar_regla':
            id_regla = request.POST.get('regla_id')
            ReglaDeducible.objects.filter(id=id_regla).delete()
            messages.warning(request, "Regla eliminada.")

        return redirect('gerencia:parametros_gerencial')
    
    context = {
        'config': config, 
        'reglas': reglas,
        'tipos_poliza': lista_tipos_poliza
    }
    return render(request, 'gerencia/parametros.html', context)

# 4. USUARIOS (GESTIÓN DE ACCESO AL SISTEMA)
def usuarios_gerencial(request):
    # Aquí gestionamos SystemUsers (los que se loguean)
    if not Group.objects.exists():
        roles_iniciales = ['Administrador', 'Gerente', 'Analista', 'Auditor']
        for role in roles_iniciales:
            Group.objects.create(name=role)
    roles_db = Group.objects.all().order_by('name')

    if request.method == 'POST':
        nombre = request.POST.get('userName')
        email = request.POST.get('userEmail')
        rol_id = request.POST.get('userRole')
        
        # Usamos SystemUser porque necesitamos password y login
        if not SystemUser.objects.filter(username=email).exists():
            nuevo_usuario = SystemUser.objects.create_user(username=email, email=email, password='password123')
            nuevo_usuario.first_name = nombre
            if rol_id:
                grupo = Group.objects.get(id=rol_id)
                nuevo_usuario.groups.add(grupo)
                nuevo_usuario.is_staff = True # Permiso para entrar al admin
            nuevo_usuario.save()
            messages.success(request, f"Usuario de sistema creado exitosamente.")
        else:
            messages.error(request, "El usuario ya existe en el sistema.")
        return redirect('gerencia:usuarios_gerencial')

    usuarios = SystemUser.objects.prefetch_related('groups').all().order_by('-date_joined')
    context = {'usuarios': usuarios, 'roles': roles_db}
    return render(request, 'gerencia/usuarios.html', context)

# 5. EXPORTACIONES (REPORTES DE NEGOCIO)
def exportaciones_gerencial(request):
    tipos_reporte = Reporte.TIPO_CHOICES

    if request.method == 'POST':
        tipo_reporte = request.POST.get('report_type')
        formato = request.POST.get('format')
        
        # El responsable es el SystemUser (Logueado)
        usuario_responsable = request.user if request.user.is_authenticated else SystemUser.objects.first()
        if not usuario_responsable:
            usuario_responsable = SystemUser.objects.create_user('admin_sistema', 'admin@sys.com', 'admin')

        archivo_final = None
        nombre_archivo = ""
        
        headers = []
        data_rows = []
        
        if tipo_reporte == 'siniestros':
            headers = ['N°', 'Estado', 'Bien', 'Póliza', 'Fecha', 'Monto Reclamado', 'Monto Aprobado']
            objetos = Siniestro.objects.select_related('poliza').all().order_by('-fecha_reporte')
            for obj in objetos:
                data_rows.append([
                    str(obj.numero_siniestro), 
                    obj.estado, 
                    obj.tipo_bien[:20], 
                    obj.poliza.numero_poliza, 
                    str(obj.fecha_reporte), 
                    f"${obj.monto_reclamado}", 
                    f"${obj.monto_aprobado or 0}"
                ])
                
        elif tipo_reporte == 'polizas':
            # Reportamos Pólizas y sus Titulares (ClienteUsuario)
            headers = ['N° Póliza', 'Tipo', 'Titular', 'Inicio', 'Fin', 'Prima', 'Estado']
            objetos = Poliza.objects.select_related('titular').all().order_by('-fecha_inicio')
            for obj in objetos:
                # obj.titular es ClienteUsuario (tiene nombre y apellido)
                nombre_titular = f"{obj.titular.nombre} {obj.titular.apellido}" if obj.titular else "N/A"
                data_rows.append([
                    obj.numero_poliza,
                    obj.tipo_poliza,
                    nombre_titular[:25],
                    str(obj.fecha_inicio),
                    str(obj.fecha_fin),
                    f"${obj.prima}",
                    obj.estado
                ])

        elif tipo_reporte == 'usuarios':
             # ¡OJO! Aquí reportamos CLIENTES (ClienteUsuario), que es la cartera de negocio
             headers = ['Nombre', 'Apellido', 'Email', 'Teléfono']
             objetos = ClienteUsuario.objects.all().order_by('apellido')
             for obj in objetos:
                 data_rows.append([
                    obj.nombre, 
                    obj.apellido, 
                    obj.email, 
                    obj.telefono
                ])

        # --- GENERAR EXCEL ---
        if formato == 'excel':
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = tipo_reporte.capitalize()
            ws.append(['REPORTE', tipo_reporte.upper()])
            ws.append(['GENERADO POR', usuario_responsable.username])
            ws.append(['FECHA', str(timezone.now().date())])
            ws.append([])
            ws.append(headers)
            for row in data_rows:
                ws.append(row)
            
            buffer = io.BytesIO()
            wb.save(buffer)
            buffer.seek(0)
            archivo_final = ContentFile(buffer.getvalue())
            nombre_archivo = f"{tipo_reporte}_{timezone.now().strftime('%H%M%S')}.xlsx"
            
        # --- GENERAR PDF ---
        elif formato == 'pdf':
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
            
        # --- GENERAR CSV ---
        else:
            buffer = io.StringIO()
            writer = csv.writer(buffer)
            writer.writerow(['REPORTE', tipo_reporte.upper()])
            writer.writerow(headers)
            writer.writerows(data_rows)
            archivo_final = ContentFile(buffer.getvalue().encode('utf-8'))
            nombre_archivo = f"{tipo_reporte}_{timezone.now().strftime('%H%M%S')}.csv"

        # Guardamos el registro en Reportes
        nuevo_reporte = Reporte(
            titulo=f"Reporte {tipo_reporte.capitalize()}",
            tipo=tipo_reporte,
            generado_por=usuario_responsable, # SystemUser
            descripcion=f"Exportación de {len(data_rows)} registros."
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