from django.db import models
from django_fsm import FSMField, transition
from polizas.models import *
from usuarios.models import *

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

    numero_siniestro = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Número de Siniestro"
    )

    poliza = models.ForeignKey(
        Poliza,
        on_delete=models.CASCADE,
        related_name='siniestros',
        verbose_name="Póliza"
    )

    # 🔹 RECLAMANTE (capturado por asesora)
    reclamante = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='siniestros',
        verbose_name="Reclamante"
    )
    reclamante_nombre = models.CharField(max_length=150)
    reclamante_email = models.EmailField()
    reclamante_telefono = models.CharField(max_length=20, blank=True)

    # 🔹 DATOS DEL EVENTO (ANTES ERA "Evento")
    tipo_evento = models.CharField(
    max_length=50,
    default='desconocido',
    verbose_name="Tipo de Evento"
    )
 # daño, robo, hurto, incendio

    ubicacion = models.CharField(
    max_length=255,
    default='No especificada',
    verbose_name="Ubicación del Evento"
    )

    causa_probable = models.TextField(
        blank=True,
        verbose_name="Causa Probable"
    )

    fecha_ocurrencia = models.DateField(
        verbose_name="Fecha de Ocurrencia"
    )
    fecha_reporte = models.DateField(
        auto_now_add=True,
        verbose_name="Fecha de Reporte"
    )

    descripcion = models.TextField(
        verbose_name="Descripción del Siniestro"
    )

    # 🔹 MONTOS
    monto_reclamado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Monto Reclamado"
    )

    monto_aprobado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Monto Aprobado"
    )

    deducible_aplicado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Deducible Aplicado"
    )

    # 🔹 CONTROL DE ESTADO
    estado = FSMField(
        default='reportado',
        choices=ESTADO_CHOICES,
        verbose_name="Estado"
    )

    cobertura_valida = models.BooleanField(
        default=False,
        verbose_name="Cobertura Válida"
    )

    tiempo_resolucion_dias = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Tiempo de Resolución (días)"
    )

    # 🔹 CONTROL DE PLAZOS CON ASEGURADORA
    fecha_envio_aseguradora = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha Envío a Aseguradora"
    )

    fecha_respuesta_aseguradora = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha Respuesta Aseguradora"
    )

    # 🔹 FECHAS INTERNAS
    fecha_apertura = models.DateField(
        verbose_name="Fecha de Apertura"
    )

    fecha_cierre = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de Cierre"
    )

    # 🔹 BIEN AFECTADO
    tipo_bien = models.CharField(max_length=50)
    marca = models.CharField(max_length=100, blank=True)
    modelo = models.CharField(max_length=100, blank=True)
    numero_serie = models.CharField(max_length=100)

    # 🔹 RESPONSABLES
    broker = models.ForeignKey(
        Broker,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

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

    # 🔹 FSM
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


class DocumentoSiniestro(models.Model):
    TIPO_CHOICES = [
        ('carta', 'Carta Formal'),
        ('informe', 'Informe Técnico'),
        ('denuncia', 'Denuncia Fiscalía'),
        ('proforma', 'Proforma'),
        ('preexistencia', 'Preexistencia'),
        ('finiquito', 'Finiquito'),
        ('comprobante_pago', 'Comprobante de Pago'),
    ]

    siniestro = models.ForeignKey(
        Siniestro,
        on_delete=models.CASCADE,
        related_name="documentos"
    )
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    archivo = models.FileField(upload_to="siniestros/documentos/")
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Documento de Siniestro"
        verbose_name_plural = "Documentos de Siniestro"

    def __str__(self):
        return f"{self.siniestro.numero_siniestro} - {self.tipo}"





class Danio(models.Model):
    evento = models.OneToOneField(Siniestro, on_delete=models.CASCADE, primary_key=True)
    area_asignada = models.CharField(max_length=100)
    tecnico_asignado = models.CharField(max_length=100)


class Robo(models.Model):
    evento = models.OneToOneField(Siniestro, on_delete=models.CASCADE, primary_key=True)
    valor_perdido = models.DecimalField(max_digits=12, decimal_places=2)


class Hurto(models.Model):
    evento = models.OneToOneField(Siniestro, on_delete=models.CASCADE, primary_key=True)
    ubicacion_ultima_vista = models.CharField(max_length=255)


class PagareSiniestro(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente de Firma'),
        ('firmado', 'Firmado'),
        ('cancelado', 'Cancelado'),
    ]

    siniestro = models.OneToOneField(
        Siniestro,
        on_delete=models.CASCADE,
        related_name="pagare"
    )

    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    archivo = models.FileField(
        upload_to="siniestros/pagares/",
        null=True,
        blank=True
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente'
    )

    fecha_emision = models.DateField(auto_now_add=True)
    fecha_firma = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Pagaré"
        verbose_name_plural = "Pagarés"

    def __str__(self):
        return f"Pagaré {self.siniestro.numero_siniestro}"
