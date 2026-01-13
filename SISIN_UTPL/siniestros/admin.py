from django.contrib import admin
from .models import Siniestro, Evento, Danio, Robo, Hurto, Broker

admin.site.register(Siniestro)
admin.site.register(Evento)
admin.site.register(Danio)
admin.site.register(Robo)
admin.site.register(Hurto)
admin.site.register(Broker)
