from django.urls import path
from .views import notificaciones

urlpatterns = [
    path('notificaciones/', notificaciones, name='notificaciones'),
]