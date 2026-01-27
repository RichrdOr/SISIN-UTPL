import csv
import io
import json
from datetime import date, timedelta

# --- LIBRERÍAS DE TERCEROS (Excel y PDF) ---
import openpyxl

# --- DJANGO CORE Y UTILIDADES ---
from django.contrib import messages
from django.contrib.auth.models import Group  # Usuario del Admin/Sistema
from django.contrib.auth.models import User as SystemUser
from django.core.files.base import ContentFile

# --- BASE DE DATOS (Agregaciones y Cálculos Matemáticos) ---
from django.db.models import Avg, Count, ExpressionWrapper, F, Q, Sum, fields
from django.db.models.functions import Coalesce, TruncMonth
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

# --- MODELOS DEL PROYECTO ---
from polizas.models import Poliza
from reportes.models import Reporte
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from siniestros.models import Broker, Siniestro

# Manejo de usuarios: 'Usuario' (para el dashboard) y el alias 'ClienteUsuario'
# (por si usas reportes antiguos que lo requieran así)
from usuarios.models import Usuario
from usuarios.models import Usuario as ClienteUsuario

# Modelos locales de la app Gerencia
from .models import ParametroSistema, ReglaDeducible


# 1. DASHBOARD
def dashboard_gerencial(request):
    # ==========================================
    # 1. INDICADORES (KPIs)
    # ==========================================
    total_abiertos = Siniestro.objects.filter(
        estado__in=[
            "reportado",
            "docs_incompletos",
            "docs_completos",
            "enviado",
            "en_revision",
            "aprobado",
            "liquidado",
        ]
    ).count()

    total_cerrados = Siniestro.objects.filter(
        estado__in=["pagado", "rechazado", "cerrado"]
    ).count()
    total_vencidos = Siniestro.objects.filter(estado="fuera_plazo").count()
    total_gestion = total_abiertos + total_cerrados + total_vencidos

    # ==========================================
    # 2. DATOS FINANCIEROS (Histórico)
    # ==========================================
    hoy = timezone.now().date()
    meses_labels = []
    data_primas = []
    data_pagos = []

    for i in range(5, -1, -1):
        fecha_ref = hoy.replace(day=1) - timedelta(days=30 * i)
        meses_labels.append(fecha_ref.strftime("%b %Y"))

        # Ingresos
        ingresos = (
            Poliza.objects.filter(
                fecha_emision__year=fecha_ref.year, fecha_emision__month=fecha_ref.month
            ).aggregate(Sum("prima"))["prima__sum"]
            or 0
        )

        # Egresos
        egresos = (
            Siniestro.objects.filter(
                fecha_apertura__year=fecha_ref.year,
                fecha_apertura__month=fecha_ref.month,
            ).aggregate(Sum("monto_aprobado"))["monto_aprobado__sum"]
            or 0
        )

        data_primas.append(float(ingresos))
        data_pagos.append(float(egresos))

    # KPI Siniestralidad
    monto_total_pagado = sum(data_pagos)
    total_primas = sum(data_primas)
    siniestralidad_pct = (
        (monto_total_pagado / total_primas * 100) if total_primas > 0 else 0
    )

    # ==========================================
    # 3. DATOS AVANZADOS
    # ==========================================

    # A. Rentabilidad por Ramo
    ramos = Poliza.objects.values("tipo_poliza").distinct()
    labels_ramos = []
    data_primas_ramo = []
    data_ratio_ramo = []

    for r in ramos:
        tipo = r["tipo_poliza"]
        if not tipo:
            continue
        labels_ramos.append(tipo)

        p = (
            Poliza.objects.filter(tipo_poliza=tipo).aggregate(Sum("prima"))[
                "prima__sum"
            ]
            or 0
        )
        s = (
            Siniestro.objects.filter(poliza__tipo_poliza=tipo).aggregate(
                Sum("monto_aprobado")
            )["monto_aprobado__sum"]
            or 0
        )

        data_primas_ramo.append(float(p))
        ratio = (float(s) / float(p) * 100) if p > 0 else 0
        data_ratio_ramo.append(round(ratio, 1))

    # B. Matriz Brokers
    brokers_qs = (
        Siniestro.objects.values("broker__nombre")
        .annotate(cant=Count("id"), prom=Avg("monto_aprobado"))
        .exclude(broker__nombre__isnull=True)
    )

    scatter_data = []
    for b in brokers_qs:
        scatter_data.append(
            {"x": b["cant"], "y": float(b["prom"] or 0), "broker": b["broker__nombre"]}
        )

    # C. Ciclo de Vida
    def avg_dias(campo_fin, campo_ini):
        prom = Siniestro.objects.exclude(
            **{f"{campo_fin}__isnull": True, f"{campo_ini}__isnull": True}
        ).aggregate(
            r=Avg(
                ExpressionWrapper(
                    F(campo_fin) - F(campo_ini), output_field=fields.DurationField()
                )
            )
        )["r"]
        return prom.days if prom else 0

    ciclo_data = [
        avg_dias("fecha_reporte", "fecha_ocurrencia"),
        avg_dias("fecha_respuesta_aseguradora", "fecha_envio_aseguradora"),
        avg_dias("fecha_pago_real", "fecha_respuesta_aseguradora"),
    ]

    # ==========================================
    # 4. CONTEXTO CON JSON (¡LA SOLUCIÓN!)
    # ==========================================
    # Usamos json.dumps para convertir las listas de Python a Texto JSON seguro
    context = {
        "kpis": {
            "total_gestion": total_gestion,
            "total_abiertos": total_abiertos,
            "total_cerrados": total_cerrados,
            "total_vencidos": total_vencidos,
            "monto_pagado_semestre": "{:,.2f}".format(monto_total_pagado),
            "siniestralidad_pct": "{:.1f}%".format(siniestralidad_pct),
        },
        # Convertimos a JSON string para que JavaScript no falle
        "fin_labels_json": json.dumps(meses_labels),
        "fin_primas_json": json.dumps(data_primas),
        "fin_pagos_json": json.dumps(data_pagos),
        "res_data_json": json.dumps([total_cerrados, total_abiertos, total_vencidos]),
        "ramos_labels_json": json.dumps(labels_ramos),
        "ramos_primas_json": json.dumps(data_primas_ramo),
        "ramos_ratio_json": json.dumps(data_ratio_ramo),
        "scatter_brokers_json": json.dumps(scatter_data),
        "ciclo_data_json": json.dumps(ciclo_data),
    }

    return render(request, "gerencia/dashboard.html", context)


# Vistas Dummy para evitar errores de URL
def reportes_gerencial(request):
    return render(request, "gerencia/base_gerencia.html")


def parametros_gerencial(request):
    return render(request, "gerencia/base_gerencia.html")


def usuarios_gerencial(request):
    return render(request, "gerencia/base_gerencia.html")


def exportaciones_gerencial(request):
    return render(request, "gerencia/base_gerencia.html")


# 2. REPORTES
def reportes_gerencial(request):
    # Relación: Siniestro -> Poliza
    # Siniestro -> Reclamante (ClienteUsuario)
    siniestros_list = (
        Siniestro.objects.select_related("poliza", "reclamante")
        .all()
        .order_by("-fecha_reporte")
    )

    # Filtros
    lista_tipos = (
        Siniestro.objects.values_list("tipo_bien", flat=True)
        .distinct()
        .order_by("tipo_bien")
    )
    lista_estados = Siniestro.ESTADO_CHOICES

    f_estado = request.GET.get("estado")
    f_tipo = request.GET.get("tipo")
    f_fecha = request.GET.get("fecha_inicio")

    if f_estado and f_estado != "Todos":
        siniestros_list = siniestros_list.filter(estado=f_estado)
    if f_tipo and f_tipo != "Todos":
        siniestros_list = siniestros_list.filter(tipo_bien=f_tipo)
    if f_fecha:
        siniestros_list = siniestros_list.filter(fecha_reporte__gte=f_fecha)

    # Exportación Directa (Botones rápidos en la tabla)
    export_format = request.GET.get("export")

    if export_format == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="reporte_siniestros_{timezone.now().date()}.csv"'
        )
        writer = csv.writer(response)
        writer.writerow(
            ["N Caso", "Estado", "Bien", "Poliza", "Fecha", "Reclamado", "Aprobado"]
        )
        for s in siniestros_list:
            writer.writerow(
                [
                    s.numero_siniestro,
                    s.estado,
                    s.tipo_bien,
                    s.poliza.numero_poliza,
                    s.fecha_reporte,
                    s.monto_reclamado,
                    s.monto_aprobado or 0,
                ]
            )
        return response

    elif export_format == "pdf":
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="reporte_siniestros_{timezone.now().date()}.pdf"'
        )
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
        p.line(30, y - 5, 500, y - 5)
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
        "siniestros": siniestros_list,
        "filtros": request.GET,
        "lista_tipos": lista_tipos,
        "lista_estados": lista_estados,
    }
    return render(request, "gerencia/reportes.html", context)


# 3. PARÁMETROS
def parametros_gerencial(request):
    config, created = ParametroSistema.objects.get_or_create(id=1)
    reglas = ReglaDeducible.objects.all()
    lista_tipos_poliza = (
        Poliza.objects.values_list("tipo_poliza", flat=True)
        .distinct()
        .order_by("tipo_poliza")
    )

    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "guardar_general":
            config.dias_reporte_siniestro = request.POST.get("dias_reporte")
            config.dias_respuesta_seguro = request.POST.get("dias_respuesta")
            config.dias_pago = request.POST.get("dias_pago")
            config.descuento_pronto_pago = request.POST.get("descuento_valor")
            config.plazo_max_descuento = request.POST.get("descuento_plazo")
            config.alerta_fuera_plazo = "alerta_plazo" in request.POST
            config.alerta_pagos_vencidos = "alerta_pagos" in request.POST
            config.save()
            messages.success(request, "Configuración guardada.")

        elif accion == "nueva_regla":
            ReglaDeducible.objects.create(
                tipo_poliza=request.POST.get("tipo_poliza"),
                descripcion=request.POST.get("descripcion"),
                minimo=request.POST.get("minimo") or 0,
                maximo=request.POST.get("maximo") or 0,
            )
            messages.success(request, "Regla agregada.")

        elif accion == "editar_regla":
            id_regla = request.POST.get("regla_id")
            regla = get_object_or_404(ReglaDeducible, id=id_regla)
            regla.tipo_poliza = request.POST.get("tipo_poliza")
            regla.descripcion = request.POST.get("descripcion")
            regla.minimo = request.POST.get("minimo") or 0
            regla.maximo = request.POST.get("maximo") or 0
            regla.save()
            messages.success(request, "Regla actualizada.")

        elif accion == "eliminar_regla":
            id_regla = request.POST.get("regla_id")
            ReglaDeducible.objects.filter(id=id_regla).delete()
            messages.warning(request, "Regla eliminada.")

        return redirect("gerencia:parametros_gerencial")

    context = {"config": config, "reglas": reglas, "tipos_poliza": lista_tipos_poliza}
    return render(request, "gerencia/parametros.html", context)


# 4. USUARIOS (GESTIÓN DE ACCESO AL SISTEMA)
def usuarios_gerencial(request):
    # Aquí gestionamos SystemUsers (los que se loguean)
    if not Group.objects.exists():
        roles_iniciales = ["Administrador", "Gerente", "Analista", "Auditor"]
        for role in roles_iniciales:
            Group.objects.create(name=role)
    roles_db = Group.objects.all().order_by("name")

    if request.method == "POST":
        nombre = request.POST.get("userName")
        email = request.POST.get("userEmail")
        rol_id = request.POST.get("userRole")

        # Usamos SystemUser porque necesitamos password y login
        if not SystemUser.objects.filter(username=email).exists():
            nuevo_usuario = SystemUser.objects.create_user(
                username=email, email=email, password="password123"
            )
            nuevo_usuario.first_name = nombre
            if rol_id:
                grupo = Group.objects.get(id=rol_id)
                nuevo_usuario.groups.add(grupo)
                nuevo_usuario.is_staff = True  # Permiso para entrar al admin
            nuevo_usuario.save()
            messages.success(request, f"Usuario de sistema creado exitosamente.")
        else:
            messages.error(request, "El usuario ya existe en el sistema.")
        return redirect("gerencia:usuarios_gerencial")

    usuarios = (
        SystemUser.objects.prefetch_related("groups").all().order_by("-date_joined")
    )
    context = {"usuarios": usuarios, "roles": roles_db}
    return render(request, "gerencia/usuarios.html", context)


# 5. EXPORTACIONES (REPORTES DE NEGOCIO)
def exportaciones_gerencial(request):
    tipos_reporte = Reporte.TIPO_CHOICES

    if request.method == "POST":
        tipo_reporte = request.POST.get("report_type")
        formato = request.POST.get("format")

        # El responsable es el SystemUser (Logueado)
        usuario_responsable = (
            request.user
            if request.user.is_authenticated
            else SystemUser.objects.first()
        )
        if not usuario_responsable:
            usuario_responsable = SystemUser.objects.create_user(
                "admin_sistema", "admin@sys.com", "admin"
            )

        archivo_final = None
        nombre_archivo = ""

        headers = []
        data_rows = []

        if tipo_reporte == "siniestros":
            headers = [
                "N°",
                "Estado",
                "Bien",
                "Póliza",
                "Fecha",
                "Monto Reclamado",
                "Monto Aprobado",
            ]
            objetos = (
                Siniestro.objects.select_related("poliza")
                .all()
                .order_by("-fecha_reporte")
            )
            for obj in objetos:
                data_rows.append(
                    [
                        str(obj.numero_siniestro),
                        obj.estado,
                        obj.tipo_bien[:20],
                        obj.poliza.numero_poliza,
                        str(obj.fecha_reporte),
                        f"${obj.monto_reclamado}",
                        f"${obj.monto_aprobado or 0}",
                    ]
                )

        elif tipo_reporte == "polizas":
            # Reportamos Pólizas y sus Titulares (ClienteUsuario)
            headers = [
                "N° Póliza",
                "Tipo",
                "Titular",
                "Inicio",
                "Fin",
                "Prima",
                "Estado",
            ]
            objetos = (
                Poliza.objects.select_related("titular").all().order_by("-fecha_inicio")
            )
            for obj in objetos:
                # obj.titular es ClienteUsuario (tiene nombre y apellido)
                nombre_titular = (
                    f"{obj.titular.nombre} {obj.titular.apellido}"
                    if obj.titular
                    else "N/A"
                )
                data_rows.append(
                    [
                        obj.numero_poliza,
                        obj.tipo_poliza,
                        nombre_titular[:25],
                        str(obj.fecha_inicio),
                        str(obj.fecha_fin),
                        f"${obj.prima}",
                        obj.estado,
                    ]
                )

        elif tipo_reporte == "usuarios":
            # ¡OJO! Aquí reportamos CLIENTES (ClienteUsuario), que es la cartera de negocio
            headers = ["Nombre", "Apellido", "Email", "Teléfono"]
            objetos = ClienteUsuario.objects.all().order_by("apellido")
            for obj in objetos:
                data_rows.append([obj.nombre, obj.apellido, obj.email, obj.telefono])

        # --- GENERAR EXCEL ---
        if formato == "excel":
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = tipo_reporte.capitalize()
            ws.append(["REPORTE", tipo_reporte.upper()])
            ws.append(["GENERADO POR", usuario_responsable.username])
            ws.append(["FECHA", str(timezone.now().date())])
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
        elif formato == "pdf":
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
            p.line(30, y - 5, 580, y - 5)
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
            writer.writerow(["REPORTE", tipo_reporte.upper()])
            writer.writerow(headers)
            writer.writerows(data_rows)
            archivo_final = ContentFile(buffer.getvalue().encode("utf-8"))
            nombre_archivo = f"{tipo_reporte}_{timezone.now().strftime('%H%M%S')}.csv"

        # Guardamos el registro en Reportes
        nuevo_reporte = Reporte(
            titulo=f"Reporte {tipo_reporte.capitalize()}",
            tipo=tipo_reporte,
            generado_por=usuario_responsable,  # SystemUser
            descripcion=f"Exportación de {len(data_rows)} registros.",
        )
        nuevo_reporte.archivo.save(nombre_archivo, archivo_final)
        nuevo_reporte.save()

        messages.success(request, f"Reporte generado exitosamente.")
        return redirect("gerencia:exportaciones_gerencial")

    reportes = (
        Reporte.objects.select_related("generado_por")
        .all()
        .order_by("-fecha_generacion")
    )

    context = {"reportes": reportes, "tipos_reporte": tipos_reporte}
    return render(request, "gerencia/exportaciones.html", context)
