from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.views import LogoutView
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from siniestros.models import Siniestro
from .models import PerfilUsuario
from .forms import LoginFormularioPersonalizado
# Create your views here.


def logout_then_home(request):
    """Log out the current user (if any) and redirect to site root."""
    try:
        logout(request)
    except Exception:
        pass
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('/')


def login_view(request):
    if request.method == 'POST':
        form = LoginFormularioPersonalizado(request, data=request.POST)
        
        # Debug: imprimir datos del formulario
        print(f"Datos recibidos: {request.POST}")
        print(f"Formulario es válido: {form.is_valid()}")
        
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            rol = form.cleaned_data.get('rol')
            
            print(f"Datos limpios - Username: {username}, Rol: {rol}")
            
            user = authenticate(request, username=username, password=password)
            if user is not None:
                print(f"Usuario autenticado: {user.username}")
                # Verificar el rol del perfil
                try:
                    perfil = PerfilUsuario.objects.get(user=user)
                    print(f"Perfil encontrado - Rol: {perfil.rol}")
                    if perfil.rol == rol:
                        login(request, user)
                        messages.success(request, f'¡Bienvenido/a {user.get_full_name() or user.username}!')
                        
                        if rol == 'gerente':
                            return redirect('gerencia:dashboard_gerencial')
                        else:
                            return redirect('siniestros:dashboard_asesora')
                    else:
                        messages.error(request, 'El rol seleccionado no coincide con el rol del usuario.')
                        print(f"Rol no coincide: perfil.rol={perfil.rol}, rol_seleccionado={rol}")
                except PerfilUsuario.DoesNotExist:
                    messages.error(request, 'El usuario no tiene un perfil asignado.')
                    print("El usuario no tiene perfil")
            else:
                messages.error(request, 'Credenciales incorrectas.')
                print("Autenticación fallida")
        else:
            print(f"Errores del formulario: {form.errors}")
    else:
        form = LoginFormularioPersonalizado()
    
    return render(request, 'login/login.html', {'form': form})


class CustomLogoutView(LogoutView):
    # Redirect to site root (login page) after logout
    next_page = reverse_lazy('login')
    
    def dispatch(self, request, *args, **kwargs):
        messages.info(request, 'Has cerrado sesión correctamente.')
        return super().dispatch(request, *args, **kwargs)


@login_required
def dashboard_gerente(request):
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        if perfil.rol != 'gerente':
            messages.error(request, 'No tienes permisos para acceder a esta página.')
            return redirect('aseguradora:dashboard_aseguradora')
    except PerfilUsuario.DoesNotExist:
        messages.error(request, 'No tienes un perfil asignado.')
        return redirect('login')
    
    # Estadísticas generales
    context = {
        'usuario': request.user,
        'total_polizas': 150,  # Ejemplo - puedes conectar con modelos reales
        'polizas_activas': 120,
        'siniestros_pendientes': 25,
        'prima_total': 450000.00,
    }
    
    return render(request, 'gerente/dashboard_gerente.html', context)


@login_required
def dashboard_asesor(request):
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        if perfil.rol != 'asesor':
            messages.error(request, 'No tienes permisos para acceder a esta página.')
            return redirect('gerencia:dashboard_gerencial')
    except PerfilUsuario.DoesNotExist:
        messages.error(request, 'No tienes un perfil asignado.')
        return redirect('login')
    
    # Obtener siniestros (ejemplo: póliza 1)
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

    # Estadísticas
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

    return render(request, 'asesora/dashboard_asesora.html', {
        'siniestros': siniestros_data,
        'stats': stats,
        'usuario': request.user,
    })


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


