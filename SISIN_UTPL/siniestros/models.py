from django.db import models
from django.utils import timezone
from datetime import timedelta
from django_fsm import FSMField, transition
from polizas.models import *
from usuarios.models import *
from datetime import date 

class Broker(models.Model):
    nombre = models.CharField(max_length=100)
    correo = models.EmailField()
    telefono = models.CharField(max_length=20)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Broker"
        verbose_name_plural = "Brokers"

    def __str__(self):
        return self.nombre


class Siniestro(models.Model):
    ESTADO_CHOICES = [
        ('reportado', 'Reportado'),
        ('documentos_incompletos', 'Documentos Incompletos'),
        ('documentos_completos', 'Documentos Completos'),
        ('enviado_aseguradora', 'Enviado a Aseguradora'),
        ('en_revision', 'En Revisión por Aseguradora'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('liquidado', 'Liquidado'),
        ('pagado', 'Pagado'),
        ('cerrado', 'Cerrado'),
        ('fuera_plazo', 'Fuera de Plazo'),
    ]

    TIPO_EVENTO_CHOICES = [
        ('danio', 'Daño'),
        ('robo', 'Robo'),
        ('hurto', 'Hurto'),
        ('incendio', 'Incendio'),
        ('inundacion', 'Inundación'),
        ('terremoto', 'Terremoto'),
        ('otro', 'Otro'),
    ]

    # 🔹 IDENTIFICACIÓN
    numero_siniestro = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Número de Siniestro",
        editable=False
    )

    # 🔹 RELACIÓN CON PÓLIZA Y RAMO (EL RAMO GOBIERNA EL SINIESTRO)
    poliza = models.ForeignKey(
        Poliza,
        on_delete=models.PROTECT,
        related_name='siniestros',
        verbose_name="Póliza"
    )

    ramo = models.ForeignKey(
        RamoPoliza,
        on_delete=models.PROTECT,
        related_name='siniestros',
        verbose_name="Ramo Específico",
        help_text="El ramo que gobierna este siniestro"
    )

    # 🔹 RECLAMANTE (capturado por asesora)
    reclamante = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='siniestros_reportados',
        verbose_name="Reclamante (Usuario Sistema)",
        null=True,
        blank=True
    )
    reclamante_nombre = models.CharField(max_length=150, verbose_name="Nombre Completo")
    reclamante_email = models.EmailField(verbose_name="Email del Reclamante")
    reclamante_telefono = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")

    # 🔹 DATOS DEL EVENTO
    tipo_evento = models.CharField(
        max_length=50,
        choices=TIPO_EVENTO_CHOICES,
        verbose_name="Tipo de Evento"
    )

    ubicacion = models.CharField(
        max_length=255,
        verbose_name="Ubicación del Evento"
    )

    causa_probable = models.TextField(
        blank=True,
        verbose_name="Causa Probable"
    )

    # 🔹 FECHAS CRÍTICAS DEL EVENTO
    fecha_ocurrencia = models.DateField(
        verbose_name="Fecha de Ocurrencia del Evento"
    )
    
    fecha_reporte = models.DateField(
        auto_now_add=True,
        verbose_name="Fecha de Reporte en Sistema"
    )

    fecha_apertura = models.DateField(
        default=timezone.now,
        verbose_name="Fecha de Apertura Oficial"
    )

    descripcion = models.TextField(
        verbose_name="Descripción Detallada del Siniestro"
    )

    # 🔹 CONTROL DE PLAZO DE 15 DÍAS
    dias_transcurridos_reporte = models.IntegerField(
        editable=False,
        null=True,
        blank=True,
        verbose_name="Días entre Ocurrencia y Reporte"
    )

    fuera_de_plazo = models.BooleanField(
        default=False,
        editable=False,
        verbose_name="¿Reportado fuera del plazo de 15 días?"
    )

    # 🔹 MONTOS
    monto_reclamado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Monto Reclamado"
    )

    monto_aprobado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Monto Aprobado por Aseguradora"
    )

    deducible_aplicado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Deducible Aplicado"
    )

    monto_a_pagar = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Monto Final a Pagar",
        help_text="Monto aprobado - deducible"
    )

    # 🔹 CONTROL DE ESTADO
    estado = FSMField(
        default='reportado',
        choices=ESTADO_CHOICES,
        verbose_name="Estado Actual"
    )

    cobertura_valida = models.BooleanField(
        default=False,
        verbose_name="¿Cobertura Válida?"
    )

    # 🔹 CONTROL DE PLAZOS CON ASEGURADORA
    fecha_envio_aseguradora = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de Envío a Aseguradora"
    )

    fecha_limite_respuesta_aseguradora = models.DateField(
        null=True,
        blank=True,
        editable=False,
        verbose_name="Fecha Límite Respuesta (8 días)",
        help_text="Se calcula automáticamente: fecha_envio + 8 días"
    )

    fecha_respuesta_aseguradora = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha Real de Respuesta Aseguradora"
    )

    aseguradora_fuera_de_plazo = models.BooleanField(
        default=False,
        verbose_name="¿Aseguradora respondió fuera de plazo?"
    )

    # 🔹 CONTROL DE PAGO (72 HORAS)
    fecha_limite_pago = models.DateField(
        null=True,
        blank=True,
        editable=False,
        verbose_name="Fecha Límite de Pago (72 horas)"
    )

    fecha_pago_real = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha Real de Pago"
    )

    pago_fuera_de_plazo = models.BooleanField(
        default=False,
        verbose_name="¿Pago fuera de plazo?"
    )

    # 🔹 FECHAS DE CIERRE
    fecha_cierre = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de Cierre Final"
    )

    tiempo_resolucion_dias = models.IntegerField(
        null=True,
        blank=True,
        editable=False,
        verbose_name="Tiempo Total de Resolución (días)"
    )

    # 🔹 BIEN AFECTADO
    tipo_bien = models.CharField(
        max_length=100,
        verbose_name="Tipo de Bien Afectado"
    )
    marca = models.CharField(max_length=100, blank=True, verbose_name="Marca")
    modelo = models.CharField(max_length=100, blank=True, verbose_name="Modelo")
    numero_serie = models.CharField(
        max_length=100,
        verbose_name="Número de Serie/Placa"
    )

    # 🔹 RESPONSABLES
    broker = models.ForeignKey(
        Broker,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Broker Asignado"
    )

    asesor_asignado = models.ForeignKey(
        AsesorUTPL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Asesor UTPL Asignado"
    )

    # 🔹 OBSERVACIONES
    observaciones_internas = models.TextField(
        blank=True,
        verbose_name="Observaciones Internas"
    )

    razon_rechazo = models.TextField(
        blank=True,
        verbose_name="Razón de Rechazo"
    )

    # 🔹 CAMPOS ADICIONALES PARA FLUJO COMPLETO
    documentos_faltantes = models.TextField(
        blank=True,
        verbose_name="Documentos Faltantes",
        help_text="Lista de documentos que faltan por entregar"
    )

    aseguradora_destino = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Aseguradora Destino"
    )

    correo_aseguradora = models.EmailField(
        blank=True,
        verbose_name="Correo de la Aseguradora"
    )

    mensaje_aseguradora = models.TextField(
        blank=True,
        verbose_name="Mensaje enviado a Aseguradora"
    )

    monto_liquidado_aseguradora = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Monto Liquidado por Aseguradora"
    )

    notas_liquidacion = models.TextField(
        blank=True,
        verbose_name="Notas de Liquidación"
    )

    notas_cierre = models.TextField(
        blank=True,
        verbose_name="Notas de Cierre"
    )

    class Meta:
        verbose_name = "Siniestro"
        verbose_name_plural = "Siniestros"
        ordering = ['-fecha_reporte']

    def __str__(self):
        return f"{self.numero_siniestro} - {self.tipo_evento} - {self.estado}"

    def save(self, *args, **kwargs):
        # Generar número de siniestro automático
        if not self.numero_siniestro:
            year = timezone.now().year
            count = Siniestro.objects.filter(
                fecha_reporte__year=year
            ).count() + 1
            self.numero_siniestro = f"SIN-{year}-{count:05d}"

        # Calcular días transcurridos entre ocurrencia y reporte
        if self.fecha_ocurrencia and self.fecha_reporte:
            delta = self.fecha_reporte - self.fecha_ocurrencia
            self.dias_transcurridos_reporte = delta.days
            
            # Validar si está fuera del plazo de 15 días
            if self.dias_transcurridos_reporte > 15:
                self.fuera_de_plazo = True
                self.cobertura_valida = False
                self.estado = 'fuera_plazo'

        # Calcular fecha límite de respuesta aseguradora (8 días)
        if self.fecha_envio_aseguradora and not self.fecha_limite_respuesta_aseguradora:
            self.fecha_limite_respuesta_aseguradora = (
                self.fecha_envio_aseguradora + timedelta(days=8)
            )

        # Calcular fecha límite de pago (72 horas = 3 días)
        if self.estado == 'aprobado' and self.monto_aprobado and not self.fecha_limite_pago:
            self.fecha_limite_pago = timezone.now().date() + timedelta(days=3)

        # Calcular monto a pagar
        if self.monto_aprobado and self.deducible_aplicado:
            self.monto_a_pagar = self.monto_aprobado - self.deducible_aplicado

        # Calcular tiempo de resolución
        if self.fecha_cierre and self.fecha_apertura:
            delta = self.fecha_cierre - self.fecha_apertura
            self.tiempo_resolucion_dias = delta.days

        super().save(*args, **kwargs)

    @property
    def documentos_obligatorios_completos(self):
        """Verifica si tiene todos los documentos obligatorios"""
        tipos_obligatorios = ['carta', 'informe', 'proforma', 'preexistencia']
        documentos_actuales = self.documentos.values_list('tipo', flat=True)
        return all(tipo in documentos_actuales for tipo in tipos_obligatorios)

    @property
    def puede_enviarse_a_aseguradora(self):
        """Verifica si cumple condiciones para envío"""
        return (
            self.documentos_obligatorios_completos and
            not self.fuera_de_plazo and
            self.estado in ['reportado', 'documentos_completos']
        )

    @property
    def alerta_respuesta_aseguradora(self):
        """Verifica si la aseguradora está tardando"""
        if self.fecha_limite_respuesta_aseguradora and not self.fecha_respuesta_aseguradora:
            hoy = timezone.now().date()
            return hoy > self.fecha_limite_respuesta_aseguradora
        return False

    # 🔹 TRANSICIONES FSM
    @transition(field=estado, source='reportado', target='documentos_incompletos')
    def marcar_documentos_incompletos(self):
        """Cuando faltan documentos"""
        pass

    @transition(field=estado, source=['reportado', 'documentos_incompletos'], target='documentos_completos')
    def marcar_documentos_completos(self):
        """Cuando se completan todos los documentos obligatorios"""
        if not self.documentos_obligatorios_completos:
            raise ValueError("Aún faltan documentos obligatorios")

    @transition(field=estado, source='documentos_completos', target='enviado_aseguradora')
    def enviar_a_aseguradora(self):
        """Marca envío a aseguradora"""
        self.fecha_envio_aseguradora = timezone.now().date()
        self.fecha_limite_respuesta_aseguradora = (
            self.fecha_envio_aseguradora + timedelta(days=8)
        )

    @transition(field=estado, source='enviado_aseguradora', target='en_revision')
    def marcar_en_revision(self):
        """La aseguradora ha comenzado a revisar"""
        pass

    @transition(field=estado, source='en_revision', target='aprobado')
    def aprobar(self):
        """Aprueba el siniestro"""
        self.fecha_respuesta_aseguradora = timezone.now().date()
        self.cobertura_valida = True
        # Verificar si respondió fuera de plazo
        if self.fecha_limite_respuesta_aseguradora:
            if self.fecha_respuesta_aseguradora > self.fecha_limite_respuesta_aseguradora:
                self.aseguradora_fuera_de_plazo = True

    @transition(field=estado, source='en_revision', target='rechazado')
    def rechazar(self, razon=''):
        """Rechaza el siniestro"""
        self.fecha_respuesta_aseguradora = timezone.now().date()
        self.cobertura_valida = False
        self.razon_rechazo = razon

    @transition(field=estado, source='aprobado', target='liquidado')
    def liquidar(self, monto_aprobado, deducible):
        """Registra liquidación"""
        self.monto_aprobado = monto_aprobado
        self.deducible_aplicado = deducible
        self.monto_a_pagar = monto_aprobado - deducible

    def validar_cobertura(self):
        """
        Retorna True si la póliza estaba activa y vigente al momento del siniestro.
        """
        # Seguridad: Si no tiene póliza asignada, no hay cobertura
        if not self.poliza:
            return False

        # 1. Verificar estado de la póliza
        if self.poliza.estado != 'activa':
            return False

        # 2. Verificar vigencia (Fecha Ocurrencia vs Fechas Póliza)
        # Asumimos que fecha_ocurrencia es obligatorio
        if self.poliza.fecha_inicio <= self.fecha_ocurrencia <= self.poliza.fecha_fin:
            return True
        
        return False

    # --- 2. CALCULAR TIEMPO DE RESOLUCIÓN (Métricas) ---
    def calcular_tiempo_resolucion(self):
        """
        Calcula los días transcurridos desde la apertura hasta el cierre (o hasta hoy).
        """
        fecha_fin_calculo = self.fecha_cierre if self.fecha_cierre else date.today()
        delta = fecha_fin_calculo - self.fecha_apertura
        return delta.days


    @transition(field=estado, source=['pagado', 'rechazado'], target='cerrado')
    def cerrar(self):
        """Cierra el siniestro"""
        self.fecha_cierre = timezone.now().date()


class DocumentoSiniestro(models.Model):
    TIPO_CHOICES = [
        ('carta', 'Carta Formal'),
        ('informe', 'Informe Técnico'),
        ('denuncia', 'Denuncia Fiscalía'),
        ('proforma', 'Proforma de Reparación'),
        ('preexistencia', 'Certificado de Preexistencia'),
        ('salvamento', 'Salvamento'),
        ('finiquito', 'Finiquito'),
        ('comprobante_pago', 'Comprobante de Pago'),
        ('liquidacion', 'Liquidación Aseguradora'),
        ('otro', 'Otro'),
    ]

    siniestro = models.ForeignKey(
        Siniestro,
        on_delete=models.CASCADE,
        related_name="documentos"
    )
    
    tipo = models.CharField(
        max_length=30,
        choices=TIPO_CHOICES,
        verbose_name="Tipo de Documento"
    )
    
    archivo = models.FileField(
        upload_to="siniestros/documentos/%Y/%m/",
        verbose_name="Archivo"
    )
    
    descripcion = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Descripción"
    )
    
    fecha_subida = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Carga"
    )

    subido_por = models.ForeignKey(
        AsesorUTPL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Subido Por"
    )

    class Meta:
        verbose_name = "Documento de Siniestro"
        verbose_name_plural = "Documentos de Siniestro"
        unique_together = ['siniestro', 'tipo']  # Un solo documento de cada tipo

    def __str__(self):
        return f"{self.siniestro.numero_siniestro} - {self.get_tipo_display()}"


# 🔹 MODELOS ESPECIALIZADOS POR TIPO DE EVENTO (OPCIONAL, según necesidad)
class DanioSiniestro(models.Model):
    """Información adicional específica para siniestros de tipo Daño"""
    siniestro = models.OneToOneField(
        Siniestro,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='info_danio'
    )
    area_asignada = models.CharField(max_length=100, verbose_name="Área Asignada")
    tecnico_asignado = models.CharField(max_length=100, verbose_name="Técnico Asignado")
    requiere_reparacion = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Información de Daño"
        verbose_name_plural = "Información de Daños"


class RoboSiniestro(models.Model):
    """Información adicional específica para robos"""
    siniestro = models.OneToOneField(
        Siniestro,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='info_robo'
    )
    denuncia_policial = models.CharField(max_length=50, verbose_name="Nro. Denuncia")
    fiscalia = models.CharField(max_length=100, verbose_name="Fiscalía")
    fecha_denuncia = models.DateField(verbose_name="Fecha de Denuncia")
    
    class Meta:
        verbose_name = "Información de Robo"
        verbose_name_plural = "Información de Robos"

class Hurto(models.Model):
    # CORREGIDO: Ahora apunta a Siniestro en lugar de "Evento" para evitar errores
    siniestro = models.OneToOneField(Siniestro, on_delete=models.CASCADE, primary_key=True)
    ubicacion_ultima_vista = models.CharField(max_length=255)