import os
import random
from datetime import date, timedelta

import django

# --- CONFIGURACIÓN ---
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SISIN_UTPL.settings")
django.setup()

from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from notificaciones.models import Notificacion
from polizas.models import BienAsegurado, Poliza, RamoPoliza, Zona
from siniestros.models import (
    Broker,
    DocumentoSiniestro,
    HistorialEstado,
    RoboSiniestro,
    Siniestro,
)
from usuarios.models import AsesorUTPL, Usuario

print("🚀 INICIANDO CARGA INTELIGENTE PARA DASHBOARD AVANZADO...")

# ==========================================
# 1. LIMPIEZA TOTAL (Para evitar errores)
# ==========================================
print("🧹 Borrando datos antiguos...")
Notificacion.objects.all().delete()
HistorialEstado.objects.all().delete()
DocumentoSiniestro.objects.all().delete()
RoboSiniestro.objects.all().delete()
Siniestro.objects.all().delete()
RamoPoliza.objects.all().delete()
Poliza.objects.all().delete()
BienAsegurado.objects.all().delete()
Usuario.objects.all().delete()
AsesorUTPL.objects.all().delete()
Broker.objects.all().delete()
Zona.objects.all().delete()

# ==========================================
# 2. CREACIÓN DE ACTORES (Brokers y Asesores)
# ==========================================
print("🏗️ Creando Brokers y Asesores...")

# Brokers (Necesarios para la gráfica de puntos)
# Los creamos con nombres reales para que se vea bien
lista_brokers = [
    {"nombre": "Aon Risk Services", "email": "contacto@aon.com"},
    {"nombre": "Tecniseguros", "email": "siniestros@tecniseguros.com"},
    {"nombre": "Ecuaprimas", "email": "reclamos@ecuaprimas.com"},
    {"nombre": "Nova", "email": "info@nova.com"},
    {"nombre": "Seguros Unidos", "email": "atencion@unidos.com"},
]

brokers_objs = []
for b in lista_brokers:
    obj = Broker.objects.create(
        nombre=b["nombre"],
        correo=b["email"],
        telefono=f"022{random.randint(100000, 999999)}",
        activo=True,
    )
    brokers_objs.append(obj)

# Asesores UTPL
asesores_objs = []
for i in range(5):
    obj = AsesorUTPL.objects.create(
        nombre=f"Asesor {i + 1}",
        apellido="UTPL",
        email=f"asesor{i + 1}@utpl.edu.ec",
        telefono="0999999999",
    )
    asesores_objs.append(obj)

# Zonas (Para geografía)
zonas_nombres = ["Norte", "Sur", "Centro", "Valles", "Costa"]
zonas_objs = [Zona.objects.create(nombre=z) for z in zonas_nombres]

# ==========================================
# 3. CLIENTES Y PÓLIZAS (Base Financiera)
# ==========================================
print("👥 Creando Clientes y Pólizas...")

clientes_objs = []
for i in range(30):
    u = Usuario.objects.create(
        nombre=f"Cliente{i}",
        apellido=f"Apellido{i}",
        email=f"cliente{i}@mail.com",
        telefono=f"09{random.randint(10000000, 99999999)}",
    )
    clientes_objs.append(u)

# Pólizas (Necesarias para gráfica de Rentabilidad por Ramo)
# Generamos ~80 pólizas distribuidas en el tiempo
tipos_poliza = ["Vehicular", "Vida", "Incendio", "Asistencia Médica", "R. Civil"]
polizas_objs = []

for i in range(80):
    cliente = random.choice(clientes_objs)
    tipo = random.choice(tipos_poliza)

    # Fechas: Emitidas en los últimos 12 meses
    fecha_emision = date.today() - timedelta(days=random.randint(30, 360))

    # Bien asegurado
    bien = BienAsegurado.objects.create(
        descripcion=f"Bien {tipo} - {cliente.apellido}",
        estado=1,
        tipo_bien=1,
        valor=random.randint(10000, 50000),
        zona=random.choice(zonas_objs),
    )

    # Prima (Ingreso para la aseguradora)
    prima_valor = random.randint(300, 3500)

    pol = Poliza.objects.create(
        numero_poliza=f"POL-{2025}-{i + 1000}",
        titular=cliente,
        tipo_poliza=tipo,
        fecha_emision=fecha_emision,
        fecha_vencimiento=fecha_emision + timedelta(days=365),
        prima=prima_valor,  # IMPORTANTE PARA RENTABILIDAD
        cobertura="Cobertura Total",
        fecha_inicio=fecha_emision,
        fecha_fin=fecha_emision + timedelta(days=365),
        bien=bien,
        estado="activa",
        aseguradora="Aseguradora del Sur",
    )
    polizas_objs.append(pol)

    # Ramo asociado
    RamoPoliza.objects.create(
        poliza=pol,
        grupo="General",
        subgrupo=tipo,
        ramo=tipo,
        suma_asegurada=bien.valor,
        prima=prima_valor,
        base_imponible=prima_valor * 0.88,
        iva=prima_valor * 0.12,
        total_facturado=prima_valor,
        deducible_minimo=100,
        deducible_porcentaje=10,
    )

# ==========================================
# 4. SINIESTROS (La parte crítica para las gráficas)
# ==========================================
print("🔥 Creando Siniestros con lógica de tiempos...")

# Estados posibles
estados = [
    "reportado",
    "docs_completos",
    "enviado",
    "en_revision",
    "aprobado",
    "pagado",
    "pagado",
    "pagado",
    "rechazado",
]

for i in range(120):  # Creamos bastantes para que se vea lleno
    poliza = random.choice(polizas_objs)
    estado_final = random.choice(estados)
    broker_asignado = random.choice(brokers_objs)  # IMPORTANTE PARA MATRIZ BROKERS

    # 1. Definir fechas en cadena lógica (Para gráfica Eficiencia)
    # Ocurrencia -> Reporte -> Envío -> Respuesta -> Pago

    # Fecha base: Ocurrencia (hace entre 1 y 180 días)
    f_ocurrencia = date.today() - timedelta(days=random.randint(10, 180))

    # Fecha Reporte (+0 a 5 días después)
    f_reporte = f_ocurrencia + timedelta(days=random.randint(0, 5))

    # Variables opcionales según estado
    f_envio = None
    f_respuesta = None
    f_pago = None
    f_cierre = None

    # Lógica de cascada: Si está pagado, debe tener TODAS las fechas anteriores
    if estado_final in [
        "enviado",
        "en_revision",
        "aprobado",
        "pagado",
        "rechazado",
        "cerrado",
    ]:
        f_envio = f_reporte + timedelta(days=random.randint(1, 3))

    if estado_final in ["aprobado", "pagado", "rechazado", "cerrado"]:
        # Aseguradora tarda entre 2 y 10 días en responder
        f_respuesta = f_envio + timedelta(days=random.randint(2, 10))

    if estado_final in ["pagado", "cerrado"]:
        # Tesorería tarda entre 1 y 5 días en pagar
        f_pago = f_respuesta + timedelta(days=random.randint(1, 5))
        f_cierre = f_pago

    # Montos
    monto_recl = random.randint(200, 5000)
    monto_aprob = 0
    if estado_final in ["aprobado", "pagado", "cerrado"]:
        monto_aprob = monto_recl * random.uniform(0.8, 1.0)  # Aprueban casi todo

    # Crear Siniestro
    s = Siniestro.objects.create(
        numero_siniestro=f"SIN-{2026}-{i + 5000}",
        poliza=poliza,
        ramo=poliza.ramos.first(),
        reclamante=poliza.titular,
        reclamante_nombre=f"{poliza.titular.nombre}",
        reclamante_email=poliza.titular.email,
        tipo_evento=random.choice(["choque", "robo", "incendio", "inundacion"]),
        ubicacion="Ciudad de Loja",
        # FECHAS CLAVE
        fecha_ocurrencia=f_ocurrencia,
        fecha_reporte=f_reporte,
        fecha_apertura=f_reporte,
        fecha_envio_aseguradora=f_envio,
        fecha_respuesta_aseguradora=f_respuesta,
        fecha_pago_real=f_pago,
        fecha_cierre=f_cierre,
        descripcion="Siniestro generado automáticamente para pruebas de dashboard.",
        # MONTOS
        monto_reclamado=monto_recl,
        monto_aprobado=monto_aprob,
        deducible_aplicado=monto_aprob * 0.10,
        monto_a_pagar=monto_aprob * 0.90,
        estado=estado_final,
        # RELACIONES
        broker=broker_asignado,  # VITAL PARA SCATTER PLOT
        asesor_asignado=random.choice(asesores_objs),
        tipo_bien="Vehículo",
        numero_serie="XYZ-123",
    )

    # Forzar fecha_reporte (auto_now_add a veces bloquea la edición inicial)
    Siniestro.objects.filter(id=s.id).update(fecha_reporte=f_reporte)

    # Si es robo, añadir detalle
    if s.tipo_evento == "robo":
        RoboSiniestro.objects.create(
            siniestro=s,
            denuncia_policial=f"DEN-{random.randint(1000, 9999)}",
            fiscalia="Fiscalía Loja",
            fecha_denuncia=f_reporte,
        )

    # Crear Historial básico para que no salga vacío
    HistorialEstado.objects.create(
        siniestro=s,
        estado_anterior="creado",
        estado_nuevo="reportado",
        usuario="sistema",
        fecha_cambio=timezone.make_aware(
            timezone.datetime.combine(f_reporte, timezone.datetime.min.time())
        ),
    )

print("✅ ¡CARGA FINALIZADA CON ÉXITO!")
print("   Ahora tus gráficas de 'Eficiencia' y 'Brokers' tendrán datos reales.")

