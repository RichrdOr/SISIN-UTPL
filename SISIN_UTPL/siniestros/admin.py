from django.contrib import admin
from .models import (
    Siniestro,
    Broker,
    DocumentoSiniestro,
    PagareSiniestro
)

admin.site.register(Siniestro)
admin.site.register(DocumentoSiniestro)
admin.site.register(PagareSiniestro)
admin.site.register(Broker)
