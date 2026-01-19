from django.contrib import admin
from .models import (
    Siniestro,
    Danio,
    Robo,
    Hurto,
    Broker,
    DocumentoSiniestro,
    PagareSiniestro
)

admin.site.register(Siniestro)
admin.site.register(DocumentoSiniestro)
admin.site.register(PagareSiniestro)
admin.site.register(Danio)
admin.site.register(Robo)
admin.site.register(Hurto)
admin.site.register(Broker)
