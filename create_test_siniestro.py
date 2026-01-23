import os
import django
from datetime import date
os.environ.setdefault('DJANGO_SETTINGS_MODULE','SISIN_UTPL.settings')
django.setup()
from siniestros.models import Siniestro
from polizas.models import Poliza, Zona, BienAsegurado, RamoPoliza
from usuarios.models import Usuario, AsesorUTPL
from notificaciones.models import Notificacion
from django.contrib.contenttypes.models import ContentType

z, _ = Zona.objects.get_or_create(nombre='ZonaTest')
usuario, _ = Usuario.objects.get_or_create(email='cliente3@example.com', defaults={'nombre':'Cli3','apellido':'T3','telefono':''})
pol, created = Poliza.objects.get_or_create(numero_poliza='POL-TEST-3', defaults={'titular':usuario, 'tipo_poliza':'Automóvil', 'fecha_emision':date.today(), 'fecha_vencimiento':date.today(), 'prima':200.0, 'cobertura':'Cobertura X', 'estado':'activa', 'aseguradora':'UTPL', 'fecha_inicio':date.today(), 'fecha_fin':date.today()})
if created:
    print('Created Poliza', pol.id)
# ensure BienAsegurado exists
b, _ = BienAsegurado.objects.get_or_create(descripcion='Bien sin test', estado=1, tipo_bien=1, valor=500, zona=z)
# ensure ramo exists for poliza
ramo, _ = RamoPoliza.objects.get_or_create(poliza=pol, grupo='G', subgrupo='S', ramo='R', defaults={'suma_asegurada':0,'prima':0,'base_imponible':0,'iva':0,'total_facturado':0,'deducible_minimo':0,'deducible_porcentaje':0})
# create siniestro
sin = Siniestro.objects.create(poliza=pol, ramo=ramo, reclamante_nombre='Juan', reclamante_email='juan3@example.com', tipo_evento='danio', ubicacion='Quito', fecha_ocurrencia=date.today(), descripcion='desc', monto_reclamado=1000, tipo_bien='Auto', numero_serie='XYZ123')
asesor, _ = AsesorUTPL.objects.get_or_create(email='asesor3@example.com', defaults={'nombre':'As3','apellido':'P3','telefono':''})
ct = ContentType.objects.get_for_model(Siniestro)
noti = Notificacion.objects.create(titulo='Siniestro TEST', mensaje='Siniestro creado', tipo='info', content_type=ct, object_id=sin.id, destinatario=asesor)
print('CREADO SINIESTRO', sin.id, 'NOTIF', noti.id)
