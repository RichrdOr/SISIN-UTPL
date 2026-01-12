# Solo los modelos de personitas :3

from django.db import models


class Usuario(models.Model):
    id_cedula = models.IntegerField(primary_key=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    correo = models.EmailField()
    userName = models.CharField(max_length=50)
    password = models.CharField(max_length=128)
    estado = models.IntegerField()

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"


class AsesorUTPL(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, primary_key=True)


class Gerente(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, primary_key=True)


class PersonaResponsable(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, primary_key=True)

