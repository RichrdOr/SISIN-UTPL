

# Bienes, zonas, pólizas y responsables

from django.db import models
from django_fsm import FSMField, transition
from usuarios.models import Usuario, PersonaResponsable

class Zona(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class BienAsegurado(models.Model):
    descripcion = models.CharField(max_length=255)
    estado = models.IntegerField()
    tipo_bien = models.IntegerField()
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    zona = models.ForeignKey(Zona, on_delete=models.PROTECT)

    def __str__(self):
        return self.descripcion


class Poliza(models.Model):
    ESTADO_CHOICES = [
        ('activa', 'Activa'),
        ('suspendida', 'Suspendida'),
        ('cancelada', 'Cancelada'),
        ('expirada', 'Expirada'),
    ]

    numero_poliza = models.CharField(max_length=20, unique=True, verbose_name="Número de Póliza")
    titular = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='polizas', verbose_name="Titular")
    tipo_poliza = models.CharField(max_length=50, verbose_name="Tipo de Póliza")
    fecha_emision = models.DateField(verbose_name="Fecha de Emisión")
    fecha_vencimiento = models.DateField(verbose_name="Fecha de Vencimiento")
    prima = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prima")
    cobertura = models.TextField(verbose_name="Cobertura")
    estado = FSMField(default='activa', choices=ESTADO_CHOICES, verbose_name="Estado")
    aseguradora = models.CharField(max_length=100)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    bien = models.ForeignKey(BienAsegurado, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Póliza"
        verbose_name_plural = "Pólizas"

    def __str__(self):
        return f"Póliza {self.numero_poliza} - {self.titular}"

    @transition(field=estado, source='activa', target='suspendida')
    def suspender(self):
        pass

    @transition(field=estado, source=['activa', 'suspendida'], target='cancelada')
    def cancelar(self):
        pass

    @transition(field=estado, source='activa', target='expirada')
    def expirar(self):
        pass


class ResponsableBien(models.Model):
    responsable = models.ForeignKey(PersonaResponsable, on_delete=models.CASCADE)
    bien = models.ForeignKey(BienAsegurado, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('responsable', 'bien')
