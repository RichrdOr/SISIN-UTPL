"""
Servicio de lógica de negocio para Siniestros.
Centraliza todas las operaciones y validaciones.
"""

from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import logging

from .models import Siniestro, DocumentoSiniestro, HistorialEstado
from .utils import Notificador

logger = logging.getLogger(__name__)


class SiniestroServiceError(Exception):
    """Excepción personalizada para errores del servicio"""
    pass


class SiniestroService:
    """
    Servicio que encapsula toda la lógica de negocio de siniestros.
    Todas las transiciones de estado deben pasar por este servicio.
    """

    @staticmethod
    def _registrar_historial(siniestro, estado_anterior, estado_nuevo, usuario='', observaciones=''):
        """Registra el cambio de estado en el historial"""
        HistorialEstado.objects.create(
            siniestro=siniestro,
            estado_anterior=estado_anterior,
            estado_nuevo=estado_nuevo,
            usuario=usuario,
            observaciones=observaciones
        )

    @staticmethod
    def _validar_plazo_reporte(siniestro):
        """
        RN-05: Valida el plazo de 15 días entre ocurrencia y reporte.
        """
        if siniestro.dias_transcurridos_reporte and siniestro.dias_transcurridos_reporte > 15:
            siniestro.fuera_de_plazo = True
            return False
        return True

    # =========================================
    # TRANSICIÓN 1: REPORTADO → DOCS_INCOMPLETOS
    # =========================================
    @classmethod
    @transaction.atomic
    def marcar_documentos_incompletos(cls, siniestro, documentos_faltantes, usuario=''):
        """
        Marca el siniestro como documentos incompletos.
        
        Args:
            siniestro: Instancia del Siniestro
            documentos_faltantes: Lista o texto de documentos faltantes
            usuario: Usuario que realiza la acción
            
        Returns:
            Siniestro actualizado
        """
        if siniestro.estado != 'reportado':
            raise SiniestroServiceError(
                f"Solo se puede marcar como incompleto desde estado 'reportado'. Estado actual: {siniestro.estado}"
            )
        
        estado_anterior = siniestro.estado
        
        # Guardar documentos faltantes
        if isinstance(documentos_faltantes, list):
            siniestro.documentos_faltantes = ', '.join(documentos_faltantes)
        else:
            siniestro.documentos_faltantes = documentos_faltantes
        
        # Ejecutar transición FSM
        siniestro.marcar_documentos_incompletos()
        siniestro.save()
        
        # Registrar historial
        cls._registrar_historial(
            siniestro, estado_anterior, 'docs_incompletos', usuario,
            f"Documentos faltantes: {siniestro.documentos_faltantes}"
        )
        
        # Notificar al reclamante
        Notificador.notificar_cambio_estado(siniestro, 'docs_incompletos')
        
        logger.info(f"Siniestro {siniestro.numero_siniestro} marcado como docs_incompletos")
        return siniestro

    # =========================================
    # TRANSICIÓN 2: REPORTADO/DOCS_INCOMPLETOS → DOCS_COMPLETOS
    # =========================================
    @classmethod
    @transaction.atomic
    def marcar_documentos_completos(cls, siniestro, usuario=''):
        """
        Confirma que los documentos están completos (validación visual).
        
        Args:
            siniestro: Instancia del Siniestro
            usuario: Usuario que realiza la acción
            
        Returns:
            Siniestro actualizado
        """
        if siniestro.estado not in ['reportado', 'docs_incompletos']:
            raise SiniestroServiceError(
                f"Solo se puede completar documentos desde 'reportado' o 'docs_incompletos'. Estado actual: {siniestro.estado}"
            )
        
        estado_anterior = siniestro.estado
        
        # Ejecutar transición FSM
        siniestro.marcar_documentos_completos()
        siniestro.save()
        
        # Registrar historial
        cls._registrar_historial(
            siniestro, estado_anterior, 'docs_completos', usuario,
            "Documentos validados como completos"
        )
        
        # Notificar al reclamante
        Notificador.notificar_cambio_estado(siniestro, 'docs_completos')
        
        logger.info(f"Siniestro {siniestro.numero_siniestro} marcado como docs_completos")
        return siniestro

    # =========================================
    # TRANSICIÓN 3: DOCS_COMPLETOS → ENVIADO (VERSIÓN CORREGIDA)
    # =========================================
    # =========================================
    # TRANSICIÓN 3: DOCS_COMPLETOS → ENVIADO (VERSIÓN CORREGIDA Y ROBUSTA)
    # =========================================
    @classmethod
    @transaction.atomic
    def enviar_a_aseguradora(cls, siniestro, correo_aseguradora, mensaje='', usuario=''):
        """
        Envía el siniestro a la aseguradora CON adjuntos reales.
        """
        import os  # Necesario para manejar nombres de archivos
        from django.core.mail import EmailMessage
        from django.conf import settings

        # 1. Validación
        if siniestro.estado != 'docs_completos':
            # Permitimos reenvío si ya está en estado enviado (opcional)
            if siniestro.estado == 'enviado':
                pass 
            else:
                raise SiniestroServiceError(
                    f"Solo se puede enviar desde estado 'docs_completos'. Estado actual: {siniestro.estado}"
                )
        
        estado_anterior = siniestro.estado
        
        # 2. Guardar datos en el modelo
        siniestro.correo_aseguradora = correo_aseguradora
        siniestro.mensaje_aseguradora = mensaje
        if siniestro.poliza:
            siniestro.aseguradora_destino = siniestro.poliza.aseguradora
        
        # 3. CONSTRUIR Y ENVIAR EL CORREO REAL
        try:
            asunto = f"Nuevo Reclamo - Siniestro #{siniestro.numero_siniestro} - Póliza {siniestro.poliza.numero_poliza}"
            
            cuerpo = f"""
            Estimados {siniestro.poliza.aseguradora}:

            Por medio de la presente notificamos el siguiente siniestro para su gestión:

            RESUMEN DEL CASO:
            ------------------------------------------------
            Nº Siniestro:   {siniestro.numero_siniestro}
            Titular:        {siniestro.poliza.titular}
            Póliza:         {siniestro.poliza.numero_poliza}
            Fecha Evento:   {siniestro.fecha_ocurrencia}
            Ubicación:      {siniestro.ubicacion}
            
            DESCRIPCIÓN:
            {siniestro.descripcion}

            NOTAS ADICIONALES:
            {mensaje if mensaje else "Ninguna."}

            ------------------------------------------------
            Se adjunta la documentación de respaldo disponible.
            
            Atentamente,
            Departamento de Siniestros
            """

            email = EmailMessage(
                subject=asunto,
                body=cuerpo,
                from_email=settings.EMAIL_HOST_USER,
                to=[correo_aseguradora],
            )

            # --- ADJUNTAR ARCHIVOS (LA PARTE CLAVE) ---
            documentos = siniestro.documentos.all()
            count_adjuntos = 0
            
            for doc in documentos:
                if doc.archivo:
                    try:
                        # Abrimos el archivo en modo lectura binaria
                        with doc.archivo.open('rb') as f:
                            contenido = f.read()
                            # Obtenemos solo el nombre del archivo (sin rutas)
                            nombre_archivo = os.path.basename(doc.archivo.name)
                            # Adjuntamos al correo
                            email.attach(nombre_archivo, contenido, 'application/pdf')
                            count_adjuntos += 1
                    except Exception as e:
                        logger.error(f"Error adjuntando {doc.archivo.name}: {e}")

            # Enviar
            email.send(fail_silently=False)
            logger.info(f"Correo enviado a {correo_aseguradora} con {count_adjuntos} adjuntos.")

        except Exception as e:
            logger.error(f"Error crítico enviando correo: {e}")
            # Puedes decidir si lanzar error o solo loguearlo
            # raise SiniestroServiceError(f"Fallo al enviar correo: {e}")

        # 4. Transición de Estado
        if siniestro.estado != 'enviado':
            siniestro.enviar_a_aseguradora() # Método del modelo (FSM)
        
        siniestro.fecha_envio_aseguradora = timezone.now()
        # Fecha límite + 3 días hábiles aprox
        siniestro.fecha_limite_respuesta_aseguradora = timezone.now().date() + timezone.timedelta(days=3)
        siniestro.save()
        
        # 5. Historial
        cls._registrar_historial(
            siniestro, estado_anterior, 'enviado', usuario,
            f"Enviado a: {correo_aseguradora}. Adjuntos: {count_adjuntos}"
        )
        
        # 6. Notificar al cliente (Opcional - usa utils.py para esto)
        Notificador.notificar_cambio_estado(siniestro, 'enviado')
        
        return siniestro
    
    # =========================================
    # TRANSICIÓN 4: ENVIADO → EN_REVISION
    # =========================================
    @classmethod
    @transaction.atomic
    def marcar_en_revision(cls, siniestro, usuario=''):
        """
        Marca el siniestro como en revisión por la aseguradora.
        
        Args:
            siniestro: Instancia del Siniestro
            usuario: Usuario que realiza la acción
            
        Returns:
            Siniestro actualizado
        """
        if siniestro.estado != 'enviado':
            raise SiniestroServiceError(
                f"Solo se puede marcar en revisión desde estado 'enviado'. Estado actual: {siniestro.estado}"
            )
        
        estado_anterior = siniestro.estado
        
        # Ejecutar transición FSM
        siniestro.marcar_en_revision()
        siniestro.save()
        
        # Registrar historial
        cls._registrar_historial(
            siniestro, estado_anterior, 'en_revision', usuario,
            "Aseguradora ha iniciado revisión"
        )
        
        # Notificar al reclamante
        Notificador.notificar_cambio_estado(siniestro, 'en_revision')
        
        logger.info(f"Siniestro {siniestro.numero_siniestro} en revisión")
        return siniestro

    # =========================================
    # TRANSICIÓN 5A: EN_REVISION → APROBADO
    # =========================================
    @classmethod
    @transaction.atomic
    def aprobar(cls, siniestro, observaciones='', usuario=''):
        """
        Aprueba el siniestro (solo confirma cobertura, NO montos).
        
        Args:
            siniestro: Instancia del Siniestro
            observaciones: Observaciones de la aprobación
            usuario: Usuario que realiza la acción
            
        Returns:
            Siniestro actualizado
        """
        if siniestro.estado != 'en_revision':
            raise SiniestroServiceError(
                f"Solo se puede aprobar desde estado 'en_revision'. Estado actual: {siniestro.estado}"
            )
        
        estado_anterior = siniestro.estado
        
        # Ejecutar transición FSM
        siniestro.aprobar()
        
        if observaciones:
            siniestro.observaciones_internas += f"\n[{timezone.now().strftime('%d/%m/%Y %H:%M')}] Aprobación: {observaciones}"
        
        siniestro.save()
        
        # Registrar historial
        cls._registrar_historial(
            siniestro, estado_anterior, 'aprobado', usuario,
            observaciones or "Cobertura aprobada por aseguradora"
        )
        
        # Notificar al reclamante
        Notificador.notificar_cambio_estado(siniestro, 'aprobado')
        
        logger.info(f"Siniestro {siniestro.numero_siniestro} aprobado")
        return siniestro

    # =========================================
    # TRANSICIÓN 5B: EN_REVISION → RECHAZADO
    # =========================================
    @classmethod
    @transaction.atomic
    def rechazar(cls, siniestro, razon_rechazo, usuario=''):
        """
        Rechaza el siniestro.
        
        Args:
            siniestro: Instancia del Siniestro
            razon_rechazo: Razón del rechazo (obligatorio)
            usuario: Usuario que realiza la acción
            
        Returns:
            Siniestro actualizado
        """
        if siniestro.estado != 'en_revision':
            raise SiniestroServiceError(
                f"Solo se puede rechazar desde estado 'en_revision'. Estado actual: {siniestro.estado}"
            )
        
        if not razon_rechazo:
            raise SiniestroServiceError("Debe especificar la razón del rechazo")
        
        estado_anterior = siniestro.estado
        
        # Guardar razón de rechazo
        siniestro.razon_rechazo = razon_rechazo
        
        # Ejecutar transición FSM
        siniestro.rechazar()
        siniestro.save()
        
        # Registrar historial
        cls._registrar_historial(
            siniestro, estado_anterior, 'rechazado', usuario,
            f"Razón: {razon_rechazo}"
        )
        
        # Notificar al reclamante
        Notificador.notificar_cambio_estado(siniestro, 'rechazado')
        
        logger.info(f"Siniestro {siniestro.numero_siniestro} rechazado")
        return siniestro

    # =========================================
    # TRANSICIÓN 6: APROBADO → LIQUIDADO
    # =========================================
    @classmethod
    @transaction.atomic
    def liquidar(cls, siniestro, monto_aprobado, deducible, notas='', usuario=''):
        """
        Liquida el siniestro (ingresa montos y calcula pago).
        
        Args:
            siniestro: Instancia del Siniestro
            monto_aprobado: Monto aprobado por la aseguradora
            deducible: Deducible a aplicar
            notas: Notas de liquidación
            usuario: Usuario que realiza la acción
            
        Returns:
            Siniestro actualizado
        """
        if siniestro.estado != 'aprobado':
            raise SiniestroServiceError(
                f"Solo se puede liquidar desde estado 'aprobado'. Estado actual: {siniestro.estado}"
            )
        
        # RN-11: Validar montos positivos
        monto_aprobado = Decimal(str(monto_aprobado))
        deducible = Decimal(str(deducible))
        
        if monto_aprobado <= 0:
            raise SiniestroServiceError("El monto aprobado debe ser mayor a cero")
        
        if deducible < 0:
            raise SiniestroServiceError("El deducible no puede ser negativo")
        
        if deducible > monto_aprobado:
            raise SiniestroServiceError("El deducible no puede ser mayor al monto aprobado")
        
        estado_anterior = siniestro.estado
        
        # Guardar montos
        siniestro.monto_aprobado = monto_aprobado
        siniestro.deducible_aplicado = deducible
        siniestro.notas_liquidacion = notas
        
        # Ejecutar transición FSM (calcula monto_a_pagar)
        siniestro.liquidar()
        siniestro.save()
        
        # Registrar historial
        cls._registrar_historial(
            siniestro, estado_anterior, 'liquidado', usuario,
            f"Monto: ${monto_aprobado}, Deducible: ${deducible}, A pagar: ${siniestro.monto_a_pagar}"
        )
        
        # Notificar al reclamante
        Notificador.notificar_cambio_estado(siniestro, 'liquidado')
        
        logger.info(f"Siniestro {siniestro.numero_siniestro} liquidado")
        return siniestro

    # =========================================
    # TRANSICIÓN 7: LIQUIDADO → PAGADO
    # =========================================
    @classmethod
    @transaction.atomic
    def registrar_pago(cls, siniestro, usuario=''):
        """
        Registra el pago del siniestro.
        
        Args:
            siniestro: Instancia del Siniestro
            usuario: Usuario que realiza la acción
            
        Returns:
            Siniestro actualizado
        """
        if siniestro.estado != 'liquidado':
            raise SiniestroServiceError(
                f"Solo se puede registrar pago desde estado 'liquidado'. Estado actual: {siniestro.estado}"
            )
        
        estado_anterior = siniestro.estado
        
        # Ejecutar transición FSM
        siniestro.registrar_pago()
        siniestro.save()
        
        # Registrar historial
        fuera_plazo = " (FUERA DE PLAZO)" if siniestro.pago_fuera_de_plazo else ""
        cls._registrar_historial(
            siniestro, estado_anterior, 'pagado', usuario,
            f"Pago registrado: ${siniestro.monto_a_pagar}{fuera_plazo}"
        )
        
        # Notificar al reclamante
        Notificador.notificar_cambio_estado(siniestro, 'pagado')
        
        logger.info(f"Siniestro {siniestro.numero_siniestro} pagado")
        return siniestro

    # =========================================
    # TRANSICIÓN 8: PAGADO/RECHAZADO → CERRADO
    # =========================================
    @classmethod
    @transaction.atomic
    def cerrar(cls, siniestro, notas_cierre='', usuario=''):
        """
        Cierra el siniestro (RN-15: guarda fecha_cierre automáticamente).
        
        Args:
            siniestro: Instancia del Siniestro
            notas_cierre: Notas de cierre
            usuario: Usuario que realiza la acción
            
        Returns:
            Siniestro actualizado
        """
        if siniestro.estado not in ['pagado', 'rechazado']:
            raise SiniestroServiceError(
                f"Solo se puede cerrar desde estado 'pagado' o 'rechazado'. Estado actual: {siniestro.estado}"
            )
        
        estado_anterior = siniestro.estado
        
        # Guardar notas de cierre
        siniestro.notas_cierre = notas_cierre
        
        # Ejecutar transición FSM (guarda fecha_cierre automáticamente)
        siniestro.cerrar()
        siniestro.save()
        
        # Registrar historial
        cls._registrar_historial(
            siniestro, estado_anterior, 'cerrado', usuario,
            f"Cierre final. Tiempo de resolución: {siniestro.tiempo_resolucion_dias} días"
        )
        
        # Notificar al reclamante
        Notificador.notificar_cambio_estado(siniestro, 'cerrado')
        
        logger.info(f"Siniestro {siniestro.numero_siniestro} cerrado")
        return siniestro

    # =========================================
    # ACCIONES ADICIONALES
    # =========================================
    
    @classmethod
    def enviar_recordatorio_documentos(cls, siniestro):
        """
        Envía un recordatorio de documentos pendientes.
        Solo aplica para estado 'docs_incompletos'.
        """
        if siniestro.estado != 'docs_incompletos':
            raise SiniestroServiceError(
                "Solo se puede enviar recordatorio en estado 'docs_incompletos'"
            )
        
        Notificador.enviar_recordatorio_documentos(siniestro)
        
        # Agregar nota interna
        siniestro.observaciones_internas += f"\n[{timezone.now().strftime('%d/%m/%Y %H:%M')}] Recordatorio de documentos enviado"
        siniestro.save()
        
        logger.info(f"Recordatorio enviado para siniestro {siniestro.numero_siniestro}")
        return True

    @classmethod
    def subir_documento(cls, siniestro, archivo, tipo, descripcion=''):
        """
        Sube un documento al siniestro.
        
        Args:
            siniestro: Instancia del Siniestro
            archivo: Archivo a subir
            tipo: Tipo de documento
            descripcion: Descripción opcional
            
        Returns:
            DocumentoSiniestro creado
        """
        # Validar que el siniestro no esté cerrado
        if siniestro.estado == 'cerrado':
            raise SiniestroServiceError("No se pueden subir documentos a un siniestro cerrado")
        
        documento = DocumentoSiniestro.objects.create(
            siniestro=siniestro,
            archivo=archivo,
            tipo=tipo,
            descripcion=descripcion
        )
        
        logger.info(f"Documento {tipo} subido para siniestro {siniestro.numero_siniestro}")
        return documento

    @classmethod
    def obtener_acciones_disponibles(cls, siniestro):
        """
        Retorna las acciones disponibles según el estado actual.
        
        Returns:
            Lista de diccionarios con las acciones disponibles
        """
        acciones = {
            'reportado': [
                {'accion': 'marcar_docs_incompletos', 'label': 'Marcar Docs Incompletos', 'color': 'warning', 'icon': 'alert-triangle'},
                {'accion': 'marcar_docs_completos', 'label': 'Confirmar Documentos', 'color': 'success', 'icon': 'check-circle'},
            ],
            'docs_incompletos': [
                {'accion': 'enviar_recordatorio', 'label': 'Enviar Recordatorio', 'color': 'info', 'icon': 'mail'},
                {'accion': 'marcar_docs_completos', 'label': 'Confirmar Documentos', 'color': 'success', 'icon': 'check-circle'},
            ],
            'docs_completos': [
                {'accion': 'enviar_aseguradora', 'label': 'Enviar a Aseguradora', 'color': 'primary', 'icon': 'send'},
            ],
            'enviado': [
                {'accion': 'marcar_revision', 'label': 'Marcar en Revisión', 'color': 'info', 'icon': 'search'},
            ],
            'en_revision': [
                {'accion': 'aprobar', 'label': 'Aprobar', 'color': 'success', 'icon': 'check'},
                {'accion': 'rechazar', 'label': 'Rechazar', 'color': 'danger', 'icon': 'x'},
            ],
            'aprobado': [
                {'accion': 'liquidar', 'label': 'Liquidar', 'color': 'primary', 'icon': 'dollar-sign'},
            ],
            'liquidado': [
                {'accion': 'registrar_pago', 'label': 'Registrar Pago', 'color': 'success', 'icon': 'credit-card'},
            ],
            'pagado': [
                {'accion': 'cerrar', 'label': 'Cerrar Siniestro', 'color': 'secondary', 'icon': 'archive'},
            ],
            'rechazado': [
                {'accion': 'cerrar', 'label': 'Cerrar Siniestro', 'color': 'secondary', 'icon': 'archive'},
            ],
            'cerrado': [],
            'fuera_plazo': [],
        }
        
        return acciones.get(siniestro.estado, [])
