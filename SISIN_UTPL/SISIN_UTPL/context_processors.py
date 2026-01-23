from notificaciones.models import Notificacion

def unread_notifications_count(request):
    try:
        if request.user.is_authenticated and hasattr(request.user, 'email'):
            count = Notificacion.objects.filter(destinatario__email=request.user.email, leida=False).count()
        else:
            count = 0
    except Exception:
        count = 0
    return {'unread_notifications_count': count}
