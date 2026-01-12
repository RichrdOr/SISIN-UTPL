from django.contrib import admin
from .models import Usuario, AsesorUTPL, Gerente, PersonaResponsable

admin.site.register(Usuario)
admin.site.register(AsesorUTPL)
admin.site.register(Gerente)
admin.site.register(PersonaResponsable)
