import os

import django

# 1. CONFIGURAR DJANGO (Para que funcione fuera del shell)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SISIN_UTPL.settings")
django.setup()

from django.db.models import Avg, Count, ExpressionWrapper, F, Sum, fields
from django.utils import timezone
from polizas.models import Poliza
from siniestros.models import Broker, Siniestro

print("\n" + "=" * 50)
print("📊 RESULTADOS DEL DIAGNÓSTICO DE DATOS")
print("=" * 50)

# 1. CONTEO DE DATOS
n_siniestros = Siniestro.objects.count()
n_polizas = Poliza.objects.count()
print(f"1. VOLUMEN DE DATOS:")
print(f"   - Siniestros encontrados: {n_siniestros}")
print(f"   - Pólizas encontradas:    {n_polizas}")

if n_siniestros == 0:
    print("   ❌ ERROR CRÍTICO: No hay siniestros. Ejecuta 'cargar_datos.py' de nuevo.")
    exit()

# 2. VERIFICACIÓN DE FECHAS (Para Gráficas de Tiempos)
sin_fechas_ok = (
    Siniestro.objects.exclude(fecha_reporte__isnull=True)
    .exclude(fecha_ocurrencia__isnull=True)
    .count()
)
print(f"\n2. CALIDAD DE FECHAS:")
print(f"   - Siniestros con fechas básicas: {sin_fechas_ok} de {n_siniestros}")

# 3. VERIFICACIÓN DE MONTOS (Para Gráfica Financiera)
monto_total = (
    Siniestro.objects.aggregate(Sum("monto_aprobado"))["monto_aprobado__sum"] or 0
)
print(f"\n3. DATOS FINANCIEROS:")
print(f"   - Suma total aprobado: ${monto_total:,.2f}")
if monto_total == 0:
    print(
        "   ⚠️ ALERTA: Los siniestros tienen monto $0. La gráfica financiera saldrá plana."
    )

# 4. VERIFICACIÓN DE BROKERS (Para Matriz de Brokers)
sin_broker = Siniestro.objects.filter(broker__isnull=False).count()
print(f"\n4. ASIGNACIÓN DE BROKERS:")
print(f"   - Siniestros con Broker asignado: {sin_broker}")
if sin_broker == 0:
    print(
        "   ❌ ERROR: Ningún siniestro tiene broker. La gráfica de puntos saldrá vacía."
    )

# 5. PRUEBA DE CÁLCULO DE TIEMPOS (El error común)
print(f"\n5. PRUEBA DE CÁLCULO (Ciclo de Vida):")
try:
    # Intenta calcular la diferencia entre Ocurrencia y Reporte
    promedio = Siniestro.objects.exclude(
        fecha_reporte__isnull=True, fecha_ocurrencia__isnull=True
    ).aggregate(
        r=Avg(
            ExpressionWrapper(
                F("fecha_reporte") - F("fecha_ocurrencia"),
                output_field=fields.DurationField(),
            )
        )
    )["r"]

    if promedio:
        print(f"   ✅ Cálculo exitoso: Promedio de reacción = {promedio.days} días")
    else:
        print(f"   ⚠️ El cálculo devolvió 'None' (Vacío).")
except Exception as e:
    print(f"   ❌ ERROR TÉCNICO AL CALCULAR: {e}")

print("=" * 50 + "\n")
