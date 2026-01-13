from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from siniestros.models import Siniestro, Evento
# Create your views here.


def inicio_asegurado(request):
    # Obtener siniestros (por ahora de poliza 1)
    siniestros = Siniestro.objects.filter(poliza_id=1).select_related('poliza')
    eventos = Evento.objects.filter(siniestro__in=siniestros)

    # Crear lista de siniestros con datos para el template
    siniestros_data = []
    for siniestro in siniestros:
        evento = eventos.filter(siniestro=siniestro).first()
        siniestros_data.append({
            'codigo': siniestro.id,
            'bien_afectado': siniestro.tipo_bien,
            'fecha_evento': evento.fecha_ocurrencia if evento else siniestro.fecha_apertura,
            'estado': 'Abierto' if siniestro.estado == 1 else 'Cerrado',
        })

    # Calcular stats
    total = len(siniestros_data)
    creados = sum(1 for s in siniestros_data if s['estado'] == 'Abierto')
    en_proceso = 0  # Por ahora 0
    finalizados = sum(1 for s in siniestros_data if s['estado'] == 'Cerrado')

    stats = {
        'total': total,
        'creados': creados,
        'en_proceso': en_proceso,
        'finalizados': finalizados,
    }

    return render(request, 'asegurado/pantallaInicioAsegurado.html', {
        'siniestros': siniestros_data,
        'stats': stats,
    })


def generarSiniestro(request):
    if request.method == "POST":
        return redirect("detalle_siniestro")

    return render(request, 'asegurado/generarSiniestro.html')

def detalleSiniestro(request):
    return render(request, 'asegurado/detalle_siniestro.html')

@login_required
def dashboard_gerente(request):
    return render(request, 'gerente/dashboard.html')