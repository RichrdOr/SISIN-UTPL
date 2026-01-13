from django.urls import path
from .views import crear_siniestro, detalle_siniestro, dashboard_siniestros

urlpatterns = [
    path("crear/", crear_siniestro, name="crear_siniestro"),
    path('siniestro/<int:siniestro_id>/', detalle_siniestro, name='detalle_siniestro'),
    path('dashboard/', dashboard_siniestros, name='dashboard_siniestros'),

]