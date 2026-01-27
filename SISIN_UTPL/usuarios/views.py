from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .decorators import asesora_required, gerente_required
from siniestros.models import Siniestro
# Create your views here.

@login_required
def redireccion_inicial(request):
    """
    Esta vista actúa como un semáforo. 
    Django envía aquí al usuario justo después de loguearse exitosamente.
    """
    user = request.user
    
    # 1. Si es Asesora -> Dashboard Asesora
    if user.groups.filter(name='Asesora').exists():
        return redirect('dashboard_asesora')
    
    # 2. Si es Gerente -> Dashboard Gerente
    elif user.groups.filter(name='Gerente').exists():
        return redirect('dashboard_gerente')
        
    # 3. Si es Superusuario (Admin) -> Panel de Admin
    elif user.is_superuser:
        return redirect('/admin/')
        
    else:
        # Si el usuario existe pero no tiene grupo asignado
        return render(request, 'usuarios/sin_permisos.html')
    
@asesora_required
def dashboard_asesora(request):
    """
    Solo entra aquí si el usuario pertenece al grupo 'Asesora'.
    """
    # Aquí puedes agregar lógica real más tarde (contar siniestros, etc.)
    return render(request, 'asesora/dashboard.html')

@gerente_required
def dashboard_gerente(request):
    """
    Solo entra aquí si el usuario pertenece al grupo 'Gerente'.
    """
    return render(request, 'gerencia/dashboard.html')



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


