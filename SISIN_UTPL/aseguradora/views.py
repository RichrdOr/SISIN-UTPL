from django.shortcuts import render # <--- Esta es la línea que faltaba

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
