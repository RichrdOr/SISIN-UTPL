from django.contrib import admin
from .models import Siniestro, Evento, Danio, Robo, Hurto, Broker
# Register your models here.

admin.site.register(Siniestro)
admin.site.register(Evento)
admin.site.register(Danio)
admin.site.register(Robo)
admin.site.register(Hurto)
admin.site.register(Broker)