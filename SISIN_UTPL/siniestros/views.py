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

def crear_siniestro(request):
    if request.method == "POST":
        # Tomar valores crudos del POST
        fecha_ocurrencia_raw = request.POST.get('fecha_ocurrencia', '')
        fecha_reporte_raw = request.POST.get('fecha_reporte', '')
        fecha_apertura_raw = request.POST.get('fecha_apertura', '')

        ubicacion = request.POST.get('ubicacion', '')
        tipo_evento = request.POST.get('tipo_evento', '')
        causa_probable = request.POST.get('causa_probable', '')
        tipo_bien = request.POST.get('tipo_bien', '')
        numero_serie = request.POST.get('numero_serie', '')
        marca = request.POST.get('marca', '')
        modelo = request.POST.get('modelo', '')
        descripcion = request.POST.get('descripcion', '')
        tiempo = request.POST.get('tiempo', '0')

        try:
            # Convertir fechas, usar hoy si vienen vacías
            fecha_ocurrencia = datetime.strptime(fecha_ocurrencia_raw, '%Y-%m-%d').date() \
                if fecha_ocurrencia_raw else date.today()
            fecha_reporte = datetime.strptime(fecha_reporte_raw, '%Y-%m-%d').date() \
                if fecha_reporte_raw else date.today()
            fecha_apertura = datetime.strptime(fecha_apertura_raw, '%Y-%m-%d').date() \
                if fecha_apertura_raw else date.today()

            siniestro = Siniestro.objects.create(
                cobertura_valida=0,
                estado=1,
                fecha_apertura=fecha_apertura,
                tiempo=int(tiempo),
                tipo_bien=tipo_bien,
                marca=marca,
                modelo=modelo,
                numero_serie=numero_serie,
                poliza=None
            )

            evento = Evento.objects.create(
                descripcion=descripcion,
                descripcion_evento=descripcion,
                dias_transcurridos=0,
                estado=1,
                fecha_ocurrencia=fecha_ocurrencia,
                fecha_reporte=fecha_reporte,
                ubicacion=ubicacion,
                tipo_evento=tipo_evento,
                siniestro=siniestro,
                bien=None
            )

            messages.success(request, 'Reporte enviado exitosamente.')
            return redirect("inicio_asegurado")

        except Exception as e:
            messages.error(request, f'Error al guardar el reporte: {str(e)}')
            return redirect("inicio_asegurado")

    return render(request, "asegurado/generarSiniestro.html", {
        "polizas": Poliza.objects.all(),
        "today": date.today().isoformat(),
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

