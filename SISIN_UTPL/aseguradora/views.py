from django.shortcuts import render, get_object_or_404
from siniestros.models import Siniestro # Importante
# Pantalla 1: Dashboard Gerencial
def dashboard(request):
    # --- DATOS DINÁMICOS (LISTOS PARA BD) ---
    
    context = {
        'usuario_nombre': 'María Fernanda',
        'usuario_cargo': 'Asesora Senior',
    }
    return render(request, 'aseguradora/dashboard.html', context)

# Pantalla 2: Bandeja de Siniestros
def bandeja_siniestros(request):
    return render(request, 'aseguradora/bandeja_siniestros.html')

# Pantalla 3: Detalle de Siniestro
def detalle_siniestro(request):
    return render(request, 'aseguradora/detalle_siniestro.html')

# Pantalla 4: Enviar Correo
def enviar_correo(request):
    return render(request, 'aseguradora/enviar_correo.html')

# Pantalla 5: Liquidación
def liquidacion(request):
    return render(request, 'aseguradora/liquidacion.html')

# Pantalla 6: Registrar Pago
def registrar_pago(request):
    return render(request, 'aseguradora/registrar_pago.html')

# Pantalla 7: Cerrar Siniestro
def cerrar_siniestro(request):
    return render(request, 'aseguradora/cerrar_siniestro.html')

# Pantalla 8: Gestión de Pólizas
def gestion_polizas(request):
    return render(request, 'aseguradora/gestion_polizas.html')

# Pantalla 9: Alertas
def alertas(request):
    return render(request, 'aseguradora/alertas.html')

# Formulario Nuevo Siniestro
def generar_siniestro(request):
    return render(request, 'aseguradora/generarSiniestro.html')

def bandeja_siniestros(request):
    return render(request, 'aseguradora/bandeja_siniestros.html')

# En aseguradora/views.py



def detalle_siniestro(request, siniestro_id): # <--- Agregamos el ID como parámetro
    # 1. Recuperar el siniestro específico de la BD
    siniestro = get_object_or_404(Siniestro, id=siniestro_id)
    
    # 2. "CEREBRO": Ejecutar las validaciones en vivo
    es_cobertura_valida = siniestro.validar_cobertura()
    dias_transcurridos = siniestro.calcular_tiempo_resolucion()

    # 3. Preparar los datos para la "CARA" (Template)
    context = {
        'siniestro': siniestro,
        'cobertura_valida': es_cobertura_valida,
        'dias_transcurridos': dias_transcurridos,
        # Si tienes el evento asociado, también podrías pasarlo:
        'evento': siniestro.evento_set.first() 
    }
    
    return render(request, 'aseguradora/detalle_siniestro.html', context)
