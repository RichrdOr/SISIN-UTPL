from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
# Create your views here.


def inicio_asegurado(request):
    return render(request, 'asegurado/pantallaInicioAsegurado.html')


def generarSiniestro(request):
    if request.method == "POST":
        return redirect("detalle_siniestro")

    return render(request, 'asegurado/generarSiniestro.html')

def detalleSiniestro(request):
    return render(request, 'asegurado/detalle_siniestro.html')

@login_required
def dashboard_gerente(request):
    return render(request, 'gerente/dashboard.html')