from django.shortcuts import render, get_object_or_404, redirect
from .models import Notificacion
from django.contrib.contenttypes.models import ContentType
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden, JsonResponse
from django.urls import reverse
from django.db import models

<<<<<<< Updated upstream
# Create your views here.
=======

def notificaciones(request):
    # Intentamos filtrar por usuario si está autenticado y su email coincide
    if request.user.is_authenticated and hasattr(request.user, 'email'):
        base_qs = Notificacion.objects.filter(destinatario__email=request.user.email)
    else:
        base_qs = Notificacion.objects.all()

    base_qs = base_qs.order_by('-fecha_creacion')

    # Aplicar filtro por pestaña (todas, no-leidas, polizas, siniestros, sistema)
    filtro = request.GET.get('filtro', 'todas')
    if filtro == 'no-leidas':
        notis = base_qs.filter(leida=False)
    elif filtro == 'polizas':
        notis = base_qs.filter(content_type__model__icontains='poliza')
    elif filtro == 'siniestros':
        notis = base_qs.filter(content_type__model__icontains='siniestro')
    elif filtro == 'sistema':
        # interpretar "sistema" por tipo o por modelo que contenga 'sistema'
        notis = base_qs.filter(models.Q(tipo__iexact='sistema') | models.Q(content_type__model__icontains='sistema'))
    else:
        notis = base_qs

    # Preparar contexto simple para la plantilla existente
    items = []
    for n in notis:
        fecha = n.fecha_creacion.date().strftime('%d/%m/%Y')
        hora = n.fecha_creacion.time().strftime('%H:%M')
        # intentar extraer id de siniestro o poliza desde contenido
        contenido = None
        cont_id = None
        try:
            contenido = n.contenido
            cont_id = getattr(contenido, 'id', None)
        except Exception:
            contenido = None

        # tipo de relación (poliza, siniestro, etc.)
        related_type = n.content_type.model if n.content_type else None

        # si el tipo relacionado indica siniestro, exponer siniestro_id para la plantilla
        siniestro_id = cont_id if related_type and 'siniestro' in related_type else None

        items.append({
            'id': n.id,
            'titulo': n.titulo,
            'mensaje': n.mensaje,
            'tipo': n.tipo,
            'leida': n.leida,
            'fecha': fecha,
            'hora': hora,
            'contenido_obj': contenido,
            'contenido_id': cont_id,
            'related_type': related_type,
            'related_id': cont_id,
            'siniestro_id': siniestro_id,
        })

    context = {
        'notificaciones': items,
        'no_leidas_count': base_qs.filter(leida=False).count(),
        'leidas_count': base_qs.filter(leida=True).count(),
        'criticas_count': base_qs.filter(tipo='critica').count(),
        'filtro': filtro
    }
    return render(request, 'asesora/notificaciones.html', context)


def detalle_notificacion(request, pk):
    n = get_object_or_404(Notificacion, pk=pk)
    # marcar como leída
    if not n.leida:
        n.leida = True
        n.save()

    # redirigir al objeto relacionado si existe
    try:
        obj = n.contenido
        if obj is not None:
            # Si el objeto tiene get_absolute_url, usarlo
            if hasattr(obj, 'get_absolute_url'):
                return redirect(obj.get_absolute_url())
            # Si es una póliza sin get_absolute_url, intentar construir URL
            ct = n.content_type
            # Redirecciones por tipo de modelo
            model_name = ct.model.lower() if ct else ''
            if 'poliza' in model_name:
                try:
                    return redirect(reverse('polizas:detalle_poliza', args=[obj.id]))
                except Exception:
                    return redirect('polizas:ver_polizas')
            if 'siniestro' in model_name:
                try:
                    return redirect(reverse('siniestros:detalle_siniestro', args=[obj.id]))
                except Exception:
                    return redirect('siniestros:siniestros_asesora')
            # Si es una notificación de sistema o sin objeto, ir al dashboard
            if 'sistema' in model_name or obj is None:
                return redirect('dashboard_redirect')
    except Exception:
        pass

    # fallback
    return redirect('notificaciones:notificaciones')


@require_POST
def marcar_todas_leidas(request):
    # marcar todas las notificaciones del destinatario como leídas
    if request.user.is_authenticated and hasattr(request.user, 'email'):
        Notificacion.objects.filter(destinatario__email=request.user.email, leida=False).update(leida=True)
        unread = Notificacion.objects.filter(destinatario__email=request.user.email, leida=False).count()
    else:
        Notificacion.objects.filter(leida=False).update(leida=True)
        unread = Notificacion.objects.filter(leida=False).count()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'unread_count': unread})
    return redirect(request.META.get('HTTP_REFERER', reverse('notificaciones:notificaciones')))


@require_POST
def limpiar_todo(request):
    # eliminar todas las notificaciones del destinatario
    if request.user.is_authenticated and hasattr(request.user, 'email'):
        Notificacion.objects.filter(destinatario__email=request.user.email).delete()
    else:
        Notificacion.objects.all().delete()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'unread_count': 0})
    return redirect(request.META.get('HTTP_REFERER', reverse('notificaciones:notificaciones')))


@require_POST
def eliminar_notificacion(request, pk):
    n = get_object_or_404(Notificacion, pk=pk)
    # permitir solo si pertenece al usuario (si hay mapping por email)
    if request.user.is_authenticated and hasattr(request.user, 'email'):
        if n.destinatario.email != request.user.email:
            return HttpResponseForbidden()
    n.delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # nuevo conteo
        unread = 0
        if request.user.is_authenticated and hasattr(request.user, 'email'):
            unread = Notificacion.objects.filter(destinatario__email=request.user.email, leida=False).count()
        else:
            unread = Notificacion.objects.filter(leida=False).count()
        return JsonResponse({'success': True, 'unread_count': unread})
    return redirect(request.META.get('HTTP_REFERER', reverse('notificaciones:notificaciones')))


@require_POST
def marcar_notificacion(request, pk):
    n = get_object_or_404(Notificacion, pk=pk)
    if request.user.is_authenticated and hasattr(request.user, 'email'):
        if n.destinatario.email != request.user.email:
            return HttpResponseForbidden()
    n.leida = not n.leida
    n.save()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        unread = 0
        if request.user.is_authenticated and hasattr(request.user, 'email'):
            unread = Notificacion.objects.filter(destinatario__email=request.user.email, leida=False).count()
        else:
            unread = Notificacion.objects.filter(leida=False).count()
        return JsonResponse({'success': True, 'leida': n.leida, 'unread_count': unread})
    return redirect(request.META.get('HTTP_REFERER', reverse('notificaciones:notificaciones')))
>>>>>>> Stashed changes
