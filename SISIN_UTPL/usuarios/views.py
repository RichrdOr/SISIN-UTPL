from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from siniestros.models import Siniestro
# Create your views here.


def inicio_asegurado(request):
    # 🔹 Obtener siniestros (ejemplo: póliza 1)
    siniestros = (
        Siniestro.objects
        .filter(poliza_id=1)
        .select_related('poliza')
    )

    siniestros_data = []
    for siniestro in siniestros:
        siniestros_data.append({
            'codigo': siniestro.numero_siniestro,
            'bien_afectado': siniestro.tipo_bien,
            'fecha_evento': siniestro.fecha_ocurrencia,
            'estado': siniestro.get_estado_display(),
        })

    # 🔹 Estadísticas
    total = siniestros.count()
    creados = siniestros.filter(estado='reportado').count()
    en_proceso = siniestros.filter(estado='en_revision').count()
    finalizados = siniestros.filter(estado__in=['pagado', 'rechazado']).count()

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


