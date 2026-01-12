from django.shortcuts import render, redirect
from polizas.models import Poliza
from datetime import date
from .forms import EventoForm, SiniestroForm

# Create your views here.
def crear_siniestro(request):
    if request.method == "POST":
        siniestro_form = SiniestroForm(request.POST)
        evento_form = EventoForm(request.POST)

        if siniestro_form.is_valid() and evento_form.is_valid():
            # 1️⃣ Guardar siniestro
            siniestro = siniestro_form.save(commit=False)
            siniestro.estado = 1  # Abierto
            siniestro.cobertura_valida = 0
            siniestro.save()

            # 2️⃣ Guardar evento
            evento = evento_form.save(commit=False)
            evento.siniestro = siniestro
            evento.estado = 1
            evento.save()

            # 3️⃣ Notificar asesora (después)
            # crear_notificacion(siniestro)

            return redirect("detalle_siniestro", siniestro.id)
    else:
        siniestro_form = SiniestroForm()
        evento_form = EventoForm()

    return render(request, "asegurado/generarSiniestro.html", {
    "siniestro_form": siniestro_form,
    "evento_form": evento_form,
    "polizas": Poliza.objects.all(),
    "today": date.today(),
    })
