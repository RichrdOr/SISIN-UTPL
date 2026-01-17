from django.shortcuts import render, redirect, get_object_or_404
from polizas.models import Poliza
from datetime import date
from .models import Siniestro, Evento
from django.contrib import messages
from datetime import date

# Create your views here.
from django.shortcuts import render, redirect
from polizas.models import Poliza
from datetime import date, datetime
from .models import Siniestro, Evento
from django.contrib import messages

from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import SiniestroForm, EventoForm
from datetime import date

from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import SiniestroForm, EventoForm
from .models import Siniestro, Evento
from datetime import date

def crear_siniestro(request):
    if request.method == "POST":
        evento_form = EventoForm(request.POST)
        if evento_form.is_valid():
            evento_form.save()
            return redirect('aseguradora:dashboard_aseguradora')
    else:
        evento_form = EventoForm()

    return render(request, 'aseguradora/generarSiniestro.html', {  # puedes renombrar la plantilla si quieres
        'evento_form': evento_form,
        'today': date.today().isoformat(),
    })



def dashboard_siniestros(request):
    siniestros = Siniestro.objects.all().order_by('-fecha_apertura')

    siniestros_data = []
    for s in siniestros:
        evento = s.evento_set.first()  # si hay evento, lo toma
        siniestros_data.append({
            "id": s.id,
            "tipo_bien": s.tipo_bien,
            "fecha": evento.fecha_ocurrencia if evento else s.fecha_apertura,
            "estado": "Creados" if s.estado == 1 else "En Proceso" if s.estado == 2 else "Finalizado",
        })

    stats = {
        "total": len(siniestros_data),
        "creados": sum(1 for x in siniestros_data if x["estado"] == "Creados"),
        "en_proceso": sum(1 for x in siniestros_data if x["estado"] == "En Proceso"),
        "finalizados": sum(1 for x in siniestros_data if x["estado"] == "Finalizado"),
    }

    return render(request, "asegurado/pantallaInicioAsegurado.html", {
        "siniestros": siniestros_data,
        "stats": stats,
    })



def detalle_siniestro(request, siniestro_id):
    siniestro = get_object_or_404(Siniestro, id=siniestro_id)
    evento = Evento.objects.filter(siniestro=siniestro).first()
    return render(request, "asegurado/detalle_siniestro.html", {
        "siniestro": siniestro,
        "evento": evento,
    })

