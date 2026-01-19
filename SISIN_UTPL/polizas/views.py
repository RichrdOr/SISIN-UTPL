from django.shortcuts import render, redirect
from django.forms import inlineformset_factory
from .models import Poliza, RamoPoliza
from .forms import RamoPolizaForm, PolizaForm

# Create your views here.

def ver_polizas(request):
    return render(request, 'asesora/polizas.html')

def crear_poliza(request):
    # 1. Definimos el formset
    RamoFormSet = inlineformset_factory(
        Poliza, 
        RamoPoliza, 
        form=RamoPolizaForm,
        extra=1, 
        can_delete=True
    )
    
    if request.method == 'POST':
        # Aquí recibimos los datos
        form = PolizaForm(request.POST)
        formset = RamoFormSet(request.POST)
        
        # Por ahora, como solo quieres que redirija sin guardar:
        return redirect('nombre_de_tu_url_de_exito') 
        
    else:
        # Carga inicial (GET)
        form = PolizaForm()
        formset = RamoFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'clientes': [], # O Cliente.objects.all()
    }
    
    return render(request, 'asesora/crear_poliza.html', context)