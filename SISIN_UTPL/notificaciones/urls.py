from django.urls import path
from .views import (
    notificaciones,
    detalle_notificacion,
    marcar_todas_leidas,
    limpiar_todo,
    eliminar_notificacion,
    marcar_notificacion,
)

# Namespace for reverse URLs
app_name = 'notificaciones'

urlpatterns = [
    path('notificaciones/', notificaciones, name='notificaciones'),
    path('notificaciones/<int:pk>/', detalle_notificacion, name='detalle_notificacion'),
    path('notificaciones/marcar-todas-leidas/', marcar_todas_leidas, name='marcar_todas_leidas'),
    path('notificaciones/limpiar-todo/', limpiar_todo, name='limpiar_todo'),
    path('notificaciones/<int:pk>/eliminar/', eliminar_notificacion, name='eliminar_notificacion'),
    path('notificaciones/<int:pk>/marcar/', marcar_notificacion, name='marcar_notificacion'),
]