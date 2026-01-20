from django.db import models
from django.utils import timezone
from datetime import timedelta
from django_fsm import FSMField, transition
from polizas.models import Poliza, RamoPoliza
from usuarios.models import Usuario, AsesorUTPL


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
    """
    Modelo principal de Siniestro con FSM (Finite State Machine).
    
    FLUJO DE ESTADOS:
    ================
    1. REPORTADO 📝 → Estado inicial al crear siniestro
       ├── Si faltan documentos → DOCS_INCOMPLETOS
       └── Si documentos OK → DOCS_COMPLETOS
    
    2. DOCS_INCOMPLETOS ⚠️ → Esperando documentación
       └── Cuando se completan → DOCS_COMPLETOS
    
    3. DOCS_COMPLETOS 📋 → Listo para enviar
       └── Enviar a aseguradora → ENVIADO
    
    4. ENVIADO 📤 → Correo enviado a aseguradora
       └── Marcar en revisión → EN_REVISION
    
    5. EN_REVISION 🔍 → Aseguradora analizando
       ├── Si rechaza → RECHAZADO (FIN)
       └── Si aprueba → APROBADO
    
    6. APROBADO ✅ → Cobertura confirmada
       └── Liquidar (ingresar montos) → LIQUIDADO
    
    7. LIQUIDADO 💰 → Montos calculados
       └── Registrar pago → PAGADO
    
    8. PAGADO 💳 → Dinero entregado
       └── Cerrar → CERRADO (INMUTABLE)
    
    9. RECHAZADO ❌ → Siniestro no cubierto
       └── Cerrar → CERRADO (INMUTABLE)
    
    10. FUERA_PLAZO ⏰ → Reportado después de 15 días (automático)
    """
    
    ESTADO_CHOICES = [
        ('reportado', 'Reportado'),
        ('docs_incompletos', 'Documentos Incompletos'),
        ('docs_completos', 'Documentos Completos'),
        ('enviado', 'Enviado a Aseguradora'),
        ('en_revision', 'En Revisión'),
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

    # 🔹 RELACIÓN CON PÓLIZA Y RAMO
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

    # 🔹 RECLAMANTE
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

    # 🔹 FECHAS CRÍTICAS
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

    # 🔹 CONTROL DE PLAZO DE 15 DÍAS (RN-05)
    dias_transcurridos_reporte = models.IntegerField(
        editable=False,
        null=True,
        blank=True,
        verbose_name="Días entre Ocurrencia y Reporte"
    )

    fuera_de_plazo = models.BooleanField(
        default=False,
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

    # 🔹 CONTROL DE ESTADO (FSM)
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
        verbose_name="Fecha Límite Respuesta (8 días)"
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

    # 🔹 FECHAS DE CIERRE (RN-15)
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

    # 🔹 OBSERVACIONES Y NOTAS
    observaciones_internas = models.TextField(
        blank=True,
        verbose_name="Observaciones Internas"
    )

    razon_rechazo = models.TextField(
        blank=True,
        verbose_name="Razón de Rechazo"
    )

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
        return f"{self.numero_siniestro} - {self.get_tipo_evento_display()} - {self.get_estado_display()}"

    def save(self, *args, **kwargs):
        # Generar número de siniestro automático
        if not self.numero_siniestro:
            year = timezone.now().year
            count = Siniestro.objects.filter(
                fecha_reporte__year=year
            ).count() + 1
            self.numero_siniestro = f"SIN-{year}-{count:05d}"

        # RN-05: Calcular días transcurridos y validar plazo de 15 días
        if self.fecha_ocurrencia:
            fecha_ref = self.fecha_reporte if self.fecha_reporte else timezone.now().date()
            delta = fecha_ref - self.fecha_ocurrencia
            self.dias_transcurridos_reporte = delta.days
            
            if self.dias_transcurridos_reporte > 15 and self.estado == 'reportado':
                self.fuera_de_plazo = True

        # Calcular fecha límite de respuesta aseguradora (8 días)
        if self.fecha_envio_aseguradora and not self.fecha_limite_respuesta_aseguradora:
            self.fecha_limite_respuesta_aseguradora = (
                self.fecha_envio_aseguradora + timedelta(days=8)
            )

        # Calcular fecha límite de pago (72 horas = 3 días)
        if self.estado == 'liquidado' and not self.fecha_limite_pago:
            self.fecha_limite_pago = timezone.now().date() + timedelta(days=3)

        # RN-11: Calcular monto a pagar
        if self.monto_aprobado and self.deducible_aplicado:
            self.monto_a_pagar = self.monto_aprobado - self.deducible_aplicado

        # RN-15: Calcular tiempo de resolución al cerrar
        if self.fecha_cierre and self.fecha_apertura:
            delta = self.fecha_cierre - self.fecha_apertura
            self.tiempo_resolucion_dias = delta.days

        super().save(*args, **kwargs)

    # =============================================
    # PROPIEDADES ÚTILES
    # =============================================
    
    @property
    def dias_transcurridos(self):
        """Días desde el reporte hasta hoy"""
        if self.fecha_reporte:
            return (timezone.now().date() - self.fecha_reporte).days
        return 0

    @property
    def tiene_documentos(self):
        """Verifica si tiene al menos un documento"""
        return self.documentos.exists()

    @property
    def alerta_respuesta_aseguradora(self):
        """Verifica si la aseguradora está tardando"""
        if self.fecha_limite_respuesta_aseguradora and not self.fecha_respuesta_aseguradora:
            return timezone.now().date() > self.fecha_limite_respuesta_aseguradora
        return False

    @property
    def estado_color(self):
        """Retorna el color asociado al estado para UI"""
        colores = {
            'reportado': '#f59e0b',
            'docs_incompletos': '#ef4444',
            'docs_completos': '#3b82f6',
            'enviado': '#8b5cf6',
            'en_revision': '#06b6d4',
            'aprobado': '#10b981',
            'rechazado': '#dc2626',
            'liquidado': '#0ea5e9',
            'pagado': '#22c55e',
            'cerrado': '#6b7280',
            'fuera_plazo': '#991b1b',
        }
        return colores.get(self.estado, '#9ca3af')

    @property
    def estado_bg(self):
        """Retorna el color de fondo para badges"""
        return f"{self.estado_color}20"

    @property
    def estado_label(self):
        """Retorna la etiqueta del estado"""
        return self.get_estado_display()

    # =============================================
    # TRANSICIONES FSM
    # =============================================

    # 1. REPORTADO → DOCS_INCOMPLETOS
    @transition(field=estado, source='reportado', target='docs_incompletos')
    def marcar_documentos_incompletos(self):
        """
        Marca el siniestro como documentos incompletos.
        Se debe especificar qué documentos faltan.
        """
        pass

    # 2. REPORTADO → DOCS_COMPLETOS (validación visual OK)
    @transition(field=estado, source=['reportado', 'docs_incompletos'], target='docs_completos')
    def marcar_documentos_completos(self):
        """
        Confirma que los documentos están completos (validación visual).
        No requiere que todos los archivos estén subidos físicamente.
        """
        self.documentos_faltantes = ''

    # 3. DOCS_COMPLETOS → ENVIADO
    @transition(field=estado, source='docs_completos', target='enviado')
    def enviar_a_aseguradora(self):
        """
        Envía el siniestro a la aseguradora.
        Registra fecha de envío y calcula fecha límite de respuesta.
        """
        self.fecha_envio_aseguradora = timezone.now().date()
        self.fecha_limite_respuesta_aseguradora = (
            self.fecha_envio_aseguradora + timedelta(days=8)
        )

    # 4. ENVIADO → EN_REVISION
    @transition(field=estado, source='enviado', target='en_revision')
    def marcar_en_revision(self):
        """
        La aseguradora ha recibido y está analizando el caso.
        """
        pass

    # 5A. EN_REVISION → APROBADO
    @transition(field=estado, source='en_revision', target='aprobado')
    def aprobar(self):
        """
        La aseguradora aprueba la cobertura.
        Solo confirma cobertura, NO se ingresan montos aquí.
        """
        self.fecha_respuesta_aseguradora = timezone.now().date()
        self.cobertura_valida = True
        
        # Verificar si respondió fuera de plazo
        if self.fecha_limite_respuesta_aseguradora:
            if self.fecha_respuesta_aseguradora > self.fecha_limite_respuesta_aseguradora:
                self.aseguradora_fuera_de_plazo = True

    # 5B. EN_REVISION → RECHAZADO
    @transition(field=estado, source='en_revision', target='rechazado')
    def rechazar(self):
        """
        La aseguradora rechaza el siniestro.
        Se debe guardar la razón del rechazo.
        """
        self.fecha_respuesta_aseguradora = timezone.now().date()
        self.cobertura_valida = False

    # 6. APROBADO → LIQUIDADO
    @transition(field=estado, source='aprobado', target='liquidado')
    def liquidar(self):
        """
        Se ingresan los montos (aprobado, deducible) y se calcula monto a pagar.
        Se debe subir el PDF de liquidación.
        """
        # RN-11: Validar montos positivos
        if self.monto_aprobado and self.monto_aprobado <= 0:
            raise ValueError("El monto aprobado debe ser positivo")
        if self.deducible_aplicado and self.deducible_aplicado < 0:
            raise ValueError("El deducible no puede ser negativo")
        
        # Calcular monto a pagar
        if self.monto_aprobado and self.deducible_aplicado is not None:
            self.monto_a_pagar = self.monto_aprobado - self.deducible_aplicado
        
        # Establecer fecha límite de pago (72 horas)
        self.fecha_limite_pago = timezone.now().date() + timedelta(days=3)

    # 7. LIQUIDADO → PAGADO
    @transition(field=estado, source='liquidado', target='pagado')
    def registrar_pago(self):
        """
        Se registra el pago efectivo.
        Se debe subir el comprobante de pago.
        """
        self.fecha_pago_real = timezone.now().date()
        
        # Verificar si el pago fue fuera de plazo
        if self.fecha_limite_pago and self.fecha_pago_real > self.fecha_limite_pago:
            self.pago_fuera_de_plazo = True

    # 8. PAGADO/RECHAZADO → CERRADO
    @transition(field=estado, source=['pagado', 'rechazado'], target='cerrado')
    def cerrar(self):
        """
        Cierre final del siniestro (RN-15).
        El siniestro queda inmutable para consulta.
        """
        self.fecha_cierre = timezone.now().date()


class DocumentoSiniestro(models.Model):
    """Documentos asociados a un siniestro"""
    
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
        verbose_name="Fecha de Subida"
    )

    class Meta:
        verbose_name = "Documento de Siniestro"
        verbose_name_plural = "Documentos de Siniestro"
        ordering = ['-fecha_subida']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.siniestro.numero_siniestro}"

    @property
    def nombre_archivo(self):
        """Retorna solo el nombre del archivo sin la ruta"""
        return self.archivo.name.split('/')[-1] if self.archivo else ''

    @property
    def extension(self):
        """Retorna la extensión del archivo"""
        if self.archivo:
            return self.archivo.name.split('.')[-1].upper()
        return ''


class RoboSiniestro(models.Model):
    """Datos adicionales para siniestros de tipo robo"""
    
    # Mantener siniestro como primary_key para compatibilidad con migración inicial
    siniestro = models.OneToOneField(
        Siniestro,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='info_robo'
    )
    
    denuncia_policial = models.TextField(
        blank=True,
        verbose_name="Número/Detalle Denuncia Policial"
    )
    
    fiscalia = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Fiscalía"
    )
    
    fecha_denuncia = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de Denuncia"
    )

    class Meta:
        verbose_name = "Datos de Robo"
        verbose_name_plural = "Datos de Robo"

    def __str__(self):
        return f"Robo - {self.siniestro.numero_siniestro}"


class HistorialEstado(models.Model):
    """Registro histórico de cambios de estado"""
    
    siniestro = models.ForeignKey(
        Siniestro,
        on_delete=models.CASCADE,
        related_name='historial_estados'
    )
    
    estado_anterior = models.CharField(max_length=30)
    estado_nuevo = models.CharField(max_length=30)
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    usuario = models.CharField(max_length=150, blank=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = "Historial de Estado"
        verbose_name_plural = "Historial de Estados"
        ordering = ['-fecha_cambio']

    def __str__(self):
        return f"{self.siniestro.numero_siniestro}: {self.estado_anterior} → {self.estado_nuevo}"
