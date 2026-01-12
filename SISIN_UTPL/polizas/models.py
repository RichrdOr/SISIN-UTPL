

# Bienes, zonas, pólizas y responsables

from django.db import models
from usuarios.models import PersonaResponsable


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
    aseguradora = models.CharField(max_length=100)
    cobertura = models.CharField(max_length=255)
    estado = models.IntegerField()
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    prima = models.DecimalField(max_digits=10, decimal_places=2)
    bien = models.ForeignKey(BienAsegurado, on_delete=models.CASCADE)


class ResponsableBien(models.Model):
    responsable = models.ForeignKey(PersonaResponsable, on_delete=models.CASCADE)
    bien = models.ForeignKey(BienAsegurado, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('responsable', 'bien')
