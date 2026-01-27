# Solo los modelos de personitas :3

from django.db import models

class Usuario(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    apellido = models.CharField(max_length=100, verbose_name="Apellido")
    email = models.EmailField(unique=True, verbose_name="Correo Electrónico")
    telefono = models.CharField(max_length=15, blank=True, verbose_name="Teléfono")

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class PersonaResponsable(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    apellido = models.CharField(max_length=100, verbose_name="Apellido")
    email = models.EmailField(unique=True, verbose_name="Correo Electrónico")
    telefono = models.CharField(max_length=15, blank=True, verbose_name="Teléfono")

    class Meta:
        verbose_name = "Persona Responsable"
        verbose_name_plural = "Personas Responsables"

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class AsesorUTPL(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    apellido = models.CharField(max_length=100, verbose_name="Apellido")
    email = models.EmailField(unique=True, verbose_name="Correo Electrónico")
    telefono = models.CharField(max_length=15, blank=True, verbose_name="Teléfono")

    class Meta:
        verbose_name = "Asesor UTPL"
        verbose_name_plural = "Asesores UTPL"

    def __str__(self):
        return f"{self.nombre} {self.apellido}"
