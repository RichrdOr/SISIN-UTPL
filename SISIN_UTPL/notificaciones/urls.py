from django.urls import path
from . import views
from .views import notificaciones

urlpatterns = [
    #path('notificaciones/', notificaciones, name='notificaciones'),
    path('', views.notificaciones, name='notificaciones'),
    path('detalle/<int:notificacion_id>/', views.detalle_notificacion, name='detalle_notificacion'),
    path('marcar-todas-leidas/', views.marcar_todas_leidas, name='marcar_todas_leidas'),
    path('marcar-leida/<int:notificacion_id>/', views.marcar_leida, name='marcar_leida'),
]