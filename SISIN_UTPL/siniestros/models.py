from django.db import models
from django_fsm import FSMField, transition
from polizas.models import Poliza
from usuarios.models import Usuario

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
