from django.contrib import admin
from .models import (
    Siniestro,
    Broker,
    DocumentoSiniestro,
    # PagareSiniestro se eliminó porque no existe en models.py
)

admin.site.register(Siniestro)
admin.site.register(DocumentoSiniestro)
admin.site.register(Broker)