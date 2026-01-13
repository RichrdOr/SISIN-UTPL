from django.db import models
from django_fsm import FSMField, transition
from polizas.models import Poliza, BienAsegurado
from usuarios.models import Usuario, AsesorUTPL

class Broker(models.Model):
    nombre = models.CharField(max_length=100)
    correo = models.EmailField()
    telefono = models.CharField(max_length=20)

    def __str__(self):
        return self.nombre


class Siniestro(models.Model):
    ESTADO_CHOICES = [
        ('reportado', 'Reportado'),
        ('en_revision', 'En Revisión'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('pagado', 'Pagado'),
    ]

    numero_siniestro = models.CharField(max_length=20, unique=True, verbose_name="Número de Siniestro")
    poliza = models.ForeignKey(Poliza, on_delete=models.CASCADE, related_name='siniestros', verbose_name="Póliza")
    reclamante = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='siniestros', verbose_name="Reclamante")
    fecha_ocurrencia = models.DateField(verbose_name="Fecha de Ocurrencia")
    fecha_reporte = models.DateField(auto_now_add=True, verbose_name="Fecha de Reporte")
    descripcion = models.TextField(verbose_name="Descripción")
    monto_reclamado = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto Reclamado")
    monto_aprobado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Monto Aprobado")
    estado = FSMField(default='reportado', choices=ESTADO_CHOICES, verbose_name="Estado")
    cobertura_valida = models.IntegerField()
    fecha_apertura = models.DateField()
    fecha_cierre = models.DateField(null=True, blank=True)
    tiempo = models.IntegerField()

    broker = models.ForeignKey(Broker, on_delete=models.SET_NULL, null=True, blank=True)
    asesor_asignado = models.ForeignKey(
        AsesorUTPL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Siniestro"
        verbose_name_plural = "Siniestros"

    def __str__(self):
        return f"Siniestro {self.numero_siniestro} - {self.poliza}"

    @transition(field=estado, source='reportado', target='en_revision')
    def revisar(self):
        pass

    @transition(field=estado, source='en_revision', target='aprobado')
    def aprobar(self):
        pass

    @transition(field=estado, source='en_revision', target='rechazado')
    def rechazar(self):
        pass

    @transition(field=estado, source='aprobado', target='pagado')
    def pagar(self):
        pass


class Evento(models.Model):
    descripcion = models.CharField(max_length=255)
    descripcion_evento = models.CharField(max_length=255)
    dias_transcurridos = models.IntegerField()
    estado = models.IntegerField()
    fecha_ocurrencia = models.DateField()
    fecha_reporte = models.DateField()
    ubicacion = models.CharField(max_length=255)
    tipo_evento = models.CharField(max_length=50)
    siniestro = models.ForeignKey(Siniestro, on_delete=models.CASCADE)
    bien = models.ForeignKey(BienAsegurado, on_delete=models.CASCADE, null=True, blank=True)


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
