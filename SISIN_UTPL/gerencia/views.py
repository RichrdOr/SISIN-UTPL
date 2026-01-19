import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db.models import Sum, Q
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.core.files.base import ContentFile
from django.contrib import messages
from siniestros.models import Siniestro
from django.contrib.auth.models import User, Group
from polizas.models import Poliza
from .models import ParametroSistema
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
    # 1. Configuración y KPIs (Lo que ya tenías)
    config, _ = ParametroSistema.objects.get_or_create(id=1)
    
    total_siniestros = Siniestro.objects.count()
    abiertos = Siniestro.objects.filter(estado__in=['reportado', 'en_revision']).count()
    cerrados = Siniestro.objects.filter(estado__in=['pagado', 'rechazado']).count()
    
    dias_limite = config.dias_reporte_siniestro 
    fecha_limite = timezone.now().date() - timedelta(days=dias_limite)
    cantidad_vencidos_real = Siniestro.objects.filter(
        fecha_reporte__lt=fecha_limite
    ).exclude(estado__in=['pagado', 'rechazado']).count()
    mostrar_vencidos = cantidad_vencidos_real if config.alerta_fuera_plazo else 0

    raw_monto_siniestros = Siniestro.objects.aggregate(total=Sum('monto_aprobado'))['total'] or 0
    raw_monto_polizas = Poliza.objects.aggregate(total=Sum('prima'))['total'] or 0

    # --- NUEVO: LÓGICA PARA LA GRÁFICA (Últimos 6 meses) ---
    seis_meses_atras = timezone.now().date() - timedelta(days=180)
    
    # Agrupamos los siniestros por mes
    grafica_query = Siniestro.objects.filter(fecha_reporte__gte=seis_meses_atras)\
        .annotate(mes=TruncMonth('fecha_reporte'))\
        .values('mes')\
        .annotate(total=Count('id'))\
        .order_by('mes')
    
    # Preparamos las listas para Chart.js
    chart_labels = []
    chart_data = []
    
    for item in grafica_query:
        if item['mes']:
            # Formato de etiqueta: "2026-01" (Año-Mes)
            chart_labels.append(item['mes'].strftime("%Y-%m")) 
            chart_data.append(item['total'])
    # -------------------------------------------------------

    context = {
        'kpis': {
            'total': total_siniestros,
            'abiertos': abiertos,
            'cerrados': cerrados,
            'vencidos': mostrar_vencidos,
            'hay_vencidos_reales': cantidad_vencidos_real > 0,
            'monto_siniestros': "{:,.0f}".format(raw_monto_siniestros),
            'monto_polizas': "{:,.0f}".format(raw_monto_polizas),
        },
        'config': config,
        # Enviamos los datos de la gráfica al template
        'chart_labels': chart_labels, 
        'chart_data': chart_data
    }
    return render(request, 'gerencia/dashboard.html', context)

# 2. REPORTES (Con Exportación Directa)
def reportes_gerencial(request):
    siniestros_list = Siniestro.objects.select_related('poliza', 'reclamante').all().order_by('-fecha_reporte')

    # --- 1. DATOS PARA LOS FILTROS (DINÁMICOS) ---
    # Obtener lista única de tipos de bienes registrados en siniestros
    # values_list saca solo el campo 'tipo_bien', flat=True lo hace lista plana, distinct() elimina duplicados
    lista_tipos = Siniestro.objects.values_list('tipo_bien', flat=True).distinct().order_by('tipo_bien')
    
    # Obtener los estados definidos en el Modelo (Tuplas: ('reportado', 'Reportado'))
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

    # --- 3. EXPORTACIÓN (Se mantiene igual, la omito para ahorrar espacio visual) ---
    # ... (Tu código de exportación CSV/PDF va aquí igual que antes) ...

    context = {
        'siniestros': siniestros_list,
        'filtros': request.GET,
        'lista_tipos': lista_tipos,   # <--- Enviamos los tipos reales
        'lista_estados': lista_estados # <--- Enviamos los estados reales
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

# 5. EXPORTACIONES (Historial)
# ... (asegúrate de tener las importaciones arriba) ...

# 5. EXPORTACIONES (Con Tipos Dinámicos)
def exportaciones_gerencial(request):
    # 1. Obtener las opciones de tipos directamente del Modelo
    # Esto devuelve la tupla: [('polizas', 'Pólizas'), ('siniestros', 'Siniestros')...]
    tipos_reporte = Reporte.TIPO_CHOICES

    if request.method == 'POST':
        tipo_reporte = request.POST.get('report_type')
        formato = request.POST.get('format')
        
        usuario_responsable = request.user if request.user.is_authenticated else User.objects.first()
        if not usuario_responsable:
            usuario_responsable = User.objects.create_user('admin_sistema', 'admin@sys.com', 'admin')

        # Generación del archivo (Simulación)
        archivo_final = None
        nombre_archivo = ""
        
        # Lógica PDF
        if formato == 'pdf':
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            p.drawString(30, 750, f"REPORTE: {tipo_reporte.upper()}")
            p.drawString(30, 730, f"Generado por: {usuario_responsable.username}")
            p.save()
            buffer.seek(0)
            archivo_final = ContentFile(buffer.getvalue())
            nombre_archivo = f"{tipo_reporte}_{timezone.now().strftime('%H%M%S')}.pdf"
        
        # Lógica Excel/CSV
        else:
            buffer = io.StringIO()
            writer = csv.writer(buffer)
            writer.writerow(['REPORTE', tipo_reporte.upper()])
            writer.writerow(['FECHA', timezone.now()])
            archivo_final = ContentFile(buffer.getvalue().encode('utf-8'))
            ext = 'csv' if formato == 'csv' else 'xlsx'
            nombre_archivo = f"{tipo_reporte}_{timezone.now().strftime('%H%M%S')}.{ext}"

        # Guardar en BD
        nuevo_reporte = Reporte(
            titulo=f"Reporte {tipo_reporte.capitalize()}",
            tipo=tipo_reporte,
            generado_por=usuario_responsable
        )
        nuevo_reporte.archivo.save(nombre_archivo, archivo_final)
        nuevo_reporte.save()
        
        messages.success(request, "Reporte generado correctamente.")
        return redirect('gerencia:exportaciones_gerencial')

    reportes = Reporte.objects.select_related('generado_por').all().order_by('-fecha_generacion')
    
    context = {
        'reportes': reportes,
        'tipos_reporte': tipos_reporte # <--- ¡Esto es lo nuevo! Enviamos la lista al template
    }
    return render(request, 'gerencia/exportaciones.html', context)
