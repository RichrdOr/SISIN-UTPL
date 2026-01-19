from django.db import models

class ParametroSistema(models.Model):
    # Configuración Global (Solo 1 registro)
    dias_reporte_siniestro = models.IntegerField(default=15, verbose_name="Días máx para reportar")
    dias_respuesta_seguro = models.IntegerField(default=3, verbose_name="Días meta respuesta")
    dias_pago = models.IntegerField(default=30, verbose_name="Días máx para pago")
    
    # Descuentos
    descuento_pronto_pago = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    plazo_max_descuento = models.IntegerField(default=10)

    # Alertas
    alerta_fuera_plazo = models.BooleanField(default=True)
    alerta_pagos_vencidos = models.BooleanField(default=True)
    alerta_doc_incompleta = models.BooleanField(default=False)

    def __str__(self):
        return "Configuración General"

class ReglaDeducible(models.Model):
    # Reglas dinámicas que se pueden agregar/editar en la tabla
    tipo_poliza = models.CharField(max_length=50) # Ej: Automóvil, Vida
    descripcion = models.CharField(max_length=150) # Ej: 5% del valor comercial
    minimo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    maximo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.tipo_poliza} - {self.descripcion}"