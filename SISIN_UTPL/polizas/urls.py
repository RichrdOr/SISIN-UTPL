from django.urls import path
from .views import *

urlpatterns = [
    path('polizas/', ver_polizas, name='ver_polizas'),
    path('polizas/crear/', crear_poliza, name='crear_poliza'),
]