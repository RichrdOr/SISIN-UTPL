import os
import django
import random
from datetime import date, timedelta

# --- 1. CONFIGURACIÓN DE DJANGO ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SISIN_UTPL.settings')
django.setup()

# --- 2. IMPORTACIONES ---
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from usuarios.models import Usuario, AsesorUTPL
from polizas.models import Zona, BienAsegurado, Poliza, RamoPoliza
from siniestros.models import Siniestro, Broker
from notificaciones.models import Notificacion

print("🚀 INICIANDO SCRIPT DE SEMILLA...")

# --- 3. LIMPIEZA DE DATOS PREVIOS (Para evitar error de duplicados) ---
print("🧹 Limpiando datos antiguos de prueba...")
# Borramos en orden para respetar las claves foráneas
Notificacion.objects.all().delete()
Siniestro.objects.all().delete()
RamoPoliza.objects.all().delete()
Poliza.objects.all().delete()
BienAsegurado.objects.all().delete()
print("   -> Base de datos limpia de transacciones.")


# --- 4. CREACIÓN DE DATOS ---

# Crear Zonas
zonas = []
for z in ['Norte', 'Sur', 'Centro', 'Valles']:
    obj, _ = Zona.objects.get_or_create(nombre=z)
    zonas.append(obj)

# Crear Asesor y Broker
asesor, _ = AsesorUTPL.objects.get_or_create(
    email="asesor1@utpl.edu.ec",
    defaults={'nombre': "Juan", 'apellido': "Asesor", 'telefono': "0999999999"}
)
broker, _ = Broker.objects.get_or_create(
    nombre="Broker Principal S.A.",
    defaults={'correo': "contacto@broker.com", 'telefono': "022222222"}
)

# Crear Clientes (Usuario)
clientes = []
nombres = [("Carlos", "Perez"), ("Maria", "Gomez"), ("Luis", "Torres")]
for n, a in nombres:
    # Usamos un email random para asegurar unicidad
    email_random = f"{n.lower()}.{a.lower()}.{random.randint(1,999)}@test.com"
    user, _ = Usuario.objects.get_or_create(
        nombre=n, 
        apellido=a,
        defaults={'email': email_random, 'telefono': "099123456"}
    )
    clientes.append(user)
    
# Si la lista de clientes quedó vacía (porque ya existían), los traemos todos
if not clientes:
    clientes = list(Usuario.objects.all())

print("--- Creando Pólizas y Siniestros... ---")
tipos = ['Vehicular', 'Vida', 'Incendio']
estados = ['reportado', 'pagado', 'rechazado', 'aprobado']

for i in range(25):
    cliente = random.choice(clientes)
    
    # Bien
    bien = BienAsegurado.objects.create(
        descripcion=f"Bien {i}", estado=1, tipo_bien=1, valor=20000, zona=zonas[0]
    )
    
    # Fechas
    inicio = date.today() - timedelta(days=random.randint(0, 200))
    
    # Póliza
    poliza = Poliza.objects.create(
        numero_poliza=f"POL-{random.randint(100000,999999)}", # Número largo para evitar choque
        titular=cliente,
        tipo_poliza=random.choice(tipos),
        fecha_emision=inicio,
        fecha_vencimiento=inicio + timedelta(days=365),
        prima=random.randint(500, 2000),
        cobertura="Full",
        fecha_inicio=inicio,
        fecha_fin=inicio + timedelta(days=365),
        bien=bien,
        aseguradora="Seguros Test"
    )

    # Ramo
    ramo = RamoPoliza.objects.create(
        poliza=poliza, grupo="G", subgrupo="S", ramo="R",
        suma_asegurada=20000, prima=poliza.prima, base_imponible=0, 
        iva=0, total_facturado=0, deducible_minimo=0, deducible_porcentaje=0
    )

    # Siniestro (Solo algunos tienen siniestro)
    if i % 2 == 0: 
        estado = random.choice(estados)
        
        monto_recl = random.randint(500, 5000)
        monto_aprob = monto_recl * 0.8 if estado in ['pagado', 'aprobado'] else 0
        
        # Generamos un ID manual temporal para evitar conflicto con la lógica del modelo
        # solo durante la carga masiva
        id_manual = f"SIN-AUTO-{random.randint(100000, 999999)}"

        s = Siniestro.objects.create(
            numero_siniestro=id_manual, # Forzamos ID único
            poliza=poliza,
            ramo=ramo,
            reclamante=cliente,
            reclamante_nombre=f"{cliente.nombre} {cliente.apellido}",
            reclamante_email=cliente.email,
            tipo_evento='danio',
            ubicacion="Loja",
            fecha_ocurrencia=inicio,
            fecha_apertura=inicio,
            descripcion="Siniestro de prueba generado por script",
            monto_reclamado=monto_recl,
            monto_aprobado=monto_aprob,
            estado=estado,
            tipo_bien="Auto",
            numero_serie="123",
            broker=broker,
            asesor_asignado=asesor
        )
        
        # Actualizar fecha reporte para historial
        Siniestro.objects.filter(id=s.id).update(fecha_reporte=inicio)

        # Crear Notificación
        Notificacion.objects.create(
            titulo=f"Siniestro {s.numero_siniestro}",
            mensaje="Generado automáticamente",
            tipo='info',
            content_type=ContentType.objects.get_for_model(s),
            object_id=s.id,
            destinatario=asesor
        )

print("✅ ¡TODO LISTO! Base de datos reiniciada y poblada.")