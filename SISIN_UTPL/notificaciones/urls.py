
from django.urls import path
from . import views

urlpatterns = [
    path('', views.notificaciones, name='notificaciones'),
    path('detalle/<int:notificacion_id>/', views.detalle_notificacion, name='detalle_notificacion'),
    path('marcar-todas-leidas/', views.marcar_todas_leidas, name='marcar_todas_leidas'),
    path('marcar-leida/<int:notificacion_id>/', views.marcar_leida, name='marcar_leida'),
    path('reenviar-correo/<int:notificacion_id>/', views.reenviar_correo_notificacion, name='reenviar_correo'),
    path('eliminar/<int:notificacion_id>/', views.eliminar_notificacion, name='eliminar_notificacion'),
    path('eliminar-todas-leidas/', views.eliminar_todas_leidas, name='eliminar_todas_leidas'),
    # URLs para alertas
    path('alerta/eliminar/<int:alerta_id>/', views.eliminar_alerta, name='eliminar_alerta'),
    path('alertas/eliminar-todas/', views.eliminar_todas_alertas, name='eliminar_todas_alertas'),
]
