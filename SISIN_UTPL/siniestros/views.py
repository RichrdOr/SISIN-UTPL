from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from datetime import date

from .models import Siniestro
from .forms import SiniestroForm


def crear_siniestro(request):
    if request.method == "POST":
        form = SiniestroForm(request.POST, request.FILES)
        if form.is_valid():
            siniestro = form.save(commit=False)
            siniestro.fecha_apertura = date.today()
            siniestro.save()

            messages.success(request, "Siniestro creado correctamente.")
            return redirect('dashboard_siniestros')
    else:
        form = SiniestroForm()

    return render(request, 'asesora/crear_siniestro.html', {
        'form': form,
        'today': date.today().isoformat(),
    })




def dashboard_siniestros(request):
    siniestros = Siniestro.objects.all().order_by('-fecha_apertura')

    siniestros_data = []
    for s in siniestros:
        siniestros_data.append({
            "id": s.id,
            "tipo_bien": s.tipo_bien,
            "fecha": s.fecha_ocurrencia,
            "estado": s.get_estado_display(),
        })

    stats = {
        "total": siniestros.count(),
        "creados": siniestros.filter(estado='reportado').count(),
        "en_proceso": siniestros.filter(estado='en_revision').count(),
        "finalizados": siniestros.filter(estado__in=['aprobado', 'pagado']).count(),
    }

    return render(request, "siniestros/dashboard.html", {
        "siniestros": siniestros_data,
        "stats": stats,
    })



def detalle_siniestro(request, siniestro_id):
    siniestro = get_object_or_404(Siniestro, id=siniestro_id)

    return render(request, 'siniestros/detalle_siniestro.html', {
        'siniestro': siniestro,
        'documentos': siniestro.documentos.all(),
        'pagare': getattr(siniestro, 'pagare', None)
    })


from django.contrib import messages

def enviar_a_revision(request, siniestro_id):
    siniestro = get_object_or_404(Siniestro, id=siniestro_id)

    try:
        siniestro.revisar()
        siniestro.save()
        messages.info(request, "Siniestro enviado a revisión.")
    except:
        messages.error(request, "No se pudo cambiar el estado.")

    return redirect('detalle_siniestro', siniestro_id=siniestro.id)


def aprobar_siniestro(request, siniestro_id):
    siniestro = get_object_or_404(Siniestro, id=siniestro_id)

    try:
        siniestro.aprobar()
        siniestro.cobertura_valida = True
        siniestro.fecha_respuesta_aseguradora = date.today()
        siniestro.save()
        messages.success(request, "Siniestro aprobado.")
    except:
        messages.error(request, "No se pudo aprobar el siniestro.")

    return redirect('detalle_siniestro', siniestro_id=siniestro.id)


def dashboard_asesora(request):
    return render(request, "asesora/dashboard.html")

def siniestros_asesora(request):
    return render(request, "asesora/siniestros.html")
    