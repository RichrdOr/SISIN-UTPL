# Solo los modelos de personitas :3

from django.db import models
from django.contrib.auth.models import User

class PerfilUsuario(models.Model):
    ROLES = (
        ('gerente', 'Gerente'),
        ('asesor', 'Asesor'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Usuario")
    rol = models.CharField(max_length=10, choices=ROLES, default='asesor', verbose_name="Rol")
    telefono = models.CharField(max_length=15, blank=True, verbose_name="Teléfono")
    
    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuarios"
    
    def __str__(self):
        return f"{self.user.username} ({self.get_rol_display()})"

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
