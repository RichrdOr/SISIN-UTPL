from django.db import models
from polizas.models import Poliza, BienAsegurado
from usuarios.models import AsesorUTPL


class Broker(models.Model):
    nombre = models.CharField(max_length=100)
    correo = models.EmailField()
    telefono = models.CharField(max_length=20)

    def __str__(self):
        return self.nombre


class Siniestro(models.Model):
    cobertura_valida = models.IntegerField()
    estado = models.IntegerField()
    fecha_apertura = models.DateField()
    fecha_cierre = models.DateField(null=True, blank=True)
    tiempo = models.IntegerField()

    # 🔥 BIEN (AÑADIDO AQUÍ)
    tipo_bien = models.CharField(max_length=50)
    marca = models.CharField(max_length=100, blank=True)
    modelo = models.CharField(max_length=100, blank=True)
    numero_serie = models.CharField(max_length=100)

    poliza = models.ForeignKey(Poliza, on_delete=models.CASCADE)
    broker = models.ForeignKey(Broker, on_delete=models.SET_NULL, null=True, blank=True)
    asesor_asignado = models.ForeignKey(
        AsesorUTPL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )


class Evento(models.Model):
    descripcion = models.CharField(max_length=255)
    descripcion_evento = models.CharField(max_length=255)
    dias_transcurridos = models.IntegerField()
    estado = models.IntegerField()
    fecha_ocurrencia = models.DateField()
    fecha_reporte = models.DateField()

    # 🔥 EVENTO (AÑADIDO AQUÍ)
    ubicacion = models.CharField(max_length=255)
    tipo_evento = models.CharField(max_length=50)

    siniestro = models.ForeignKey(Siniestro, on_delete=models.CASCADE)
    bien = models.ForeignKey(BienAsegurado, on_delete=models.CASCADE)


class Danio(models.Model):
    evento = models.OneToOneField(Evento, on_delete=models.CASCADE, primary_key=True)
    area_asignada = models.CharField(max_length=100)
    tecnico_asignado = models.CharField(max_length=100)


class Robo(models.Model):
    evento = models.OneToOneField(Evento, on_delete=models.CASCADE, primary_key=True)
    valor_perdido = models.DecimalField(max_digits=12, decimal_places=2)


class Hurto(models.Model):
    evento = models.OneToOneField(Evento, on_delete=models.CASCADE, primary_key=True)
    ubicacion_ultima_vista = models.CharField(max_length=255)
