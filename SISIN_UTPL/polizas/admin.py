from django.contrib import admin
from .models import Zona, BienAsegurado, Poliza, ResponsableBien
# Register your models here.

admin.site.register(Zona)
admin.site.register(BienAsegurado)
admin.site.register(Poliza)
admin.site.register(ResponsableBien)