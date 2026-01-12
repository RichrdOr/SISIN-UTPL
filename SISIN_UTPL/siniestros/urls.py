from django.urls import path
from .views import crear_siniestro

urlpatterns = [
    path("crear/", crear_siniestro, name="crear_siniestro"),
]