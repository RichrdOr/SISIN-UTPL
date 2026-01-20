from django import forms
from .models import Siniestro, DocumentoSiniestro, RoboSiniestro
from polizas.models import Poliza, RamoPoliza


class SiniestroForm(forms.ModelForm):
    """Formulario principal para crear siniestro"""
    
    class Meta:
        model = Siniestro
        fields = [
            'poliza',
            'ramo',
            'reclamante_nombre',
            'reclamante_email',
            'reclamante_telefono',
            'tipo_evento',
            'fecha_ocurrencia',
            'ubicacion',
            'causa_probable',
            'descripcion',
            'monto_reclamado',
            'tipo_bien',
            'marca',
            'modelo',
            'numero_serie',
        ]
        
        widgets = {
            'poliza': forms.Select(attrs={
                'class': 'input',
                'required': True
            }),
            'ramo': forms.Select(attrs={
                'class': 'input',
                'required': True
            }),
            'reclamante_nombre': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'Nombre completo del reclamante'
            }),
            'reclamante_email': forms.EmailInput(attrs={
                'class': 'input',
                'placeholder': 'correo@ejemplo.com'
            }),
            'reclamante_telefono': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': '0987654321'
            }),
            'tipo_evento': forms.Select(attrs={
                'class': 'input'
            }),
            'fecha_ocurrencia': forms.DateInput(attrs={
                'type': 'date',
                'class': 'input'
            }),
            'ubicacion': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'Ubicación exacta del evento'
            }),
            'causa_probable': forms.Textarea(attrs={
                'class': 'input',
                'rows': 2,
                'placeholder': 'Breve descripción de la causa'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'input',
                'rows': 4,
                'placeholder': 'Descripción detallada del siniestro...'
            }),
            'monto_reclamado': forms.NumberInput(attrs={
                'class': 'input',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'tipo_bien': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'Ej: Computadora, Vehículo'
            }),
            'marca': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'Marca del bien'
            }),
            'modelo': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'Modelo'
            }),
            'numero_serie': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'Serie o placa'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Hacer que el campo ramo dependa de la póliza seleccionada
        if 'poliza' in self.data:
            try:
                poliza_id = int(self.data.get('poliza'))
                self.fields['ramo'].queryset = RamoPoliza.objects.filter(poliza_id=poliza_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.poliza:
            self.fields['ramo'].queryset = self.instance.poliza.ramos.all()
        else:
            self.fields['ramo'].queryset = RamoPoliza.objects.none()


class DocumentoSiniestroForm(forms.ModelForm):
    """Formulario para subir documentos"""
    
    class Meta:
        model = DocumentoSiniestro
        fields = ['tipo', 'archivo', 'descripcion']
        
        widgets = {
            'tipo': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary'
            }),
            'archivo': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-border rounded-md bg-background text-foreground file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-primary file:text-primary-foreground file:cursor-pointer',
                'accept': '.pdf'
            }),
            'descripcion': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary',
                'placeholder': 'Descripción opcional del documento'
            }),
        }


class RoboSiniestroForm(forms.ModelForm):
    """Formulario adicional para casos de robo"""
    
    class Meta:
        model = RoboSiniestro
        fields = ['denuncia_policial', 'fiscalia', 'fecha_denuncia']
        
        widgets = {
            'denuncia_policial': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'Número de denuncia'
            }),
            'fiscalia': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'Nombre de la fiscalía'
            }),
            'fecha_denuncia': forms.DateInput(attrs={
                'type': 'date',
                'class': 'input'
            }),
        }


# =============================================
# FORMULARIOS PARA TRANSICIONES DE ESTADO
# =============================================

class DocsIncompletosForm(forms.Form):
    """Formulario para marcar documentos como incompletos"""
    
    DOCUMENTOS_CHOICES = [
        ('cedula', 'Cédula de identidad'),
        ('poliza', 'Copia de la póliza'),
        ('denuncia', 'Denuncia policial'),
        ('facturas', 'Facturas o comprobantes'),
        ('fotos', 'Fotografías del siniestro'),
        ('certificado_medico', 'Certificado médico'),
        ('informe_tecnico', 'Informe técnico'),
        ('proforma', 'Proforma de reparación'),
        ('otros', 'Otros documentos'),
    ]
    
    documentos_faltantes = forms.MultipleChoiceField(
        choices=DOCUMENTOS_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-checkbox h-4 w-4 text-primary rounded border-border'
        }),
        label="Documentos faltantes"
    )
    
    observaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary',
            'rows': 3,
            'placeholder': 'Observaciones adicionales...'
        }),
        label="Observaciones"
    )


class EnviarAseguradoraForm(forms.Form):
    """Formulario para enviar siniestro a la aseguradora"""
    
    correo_aseguradora = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary',
            'placeholder': 'correo@aseguradora.com'
        }),
        label="Correo de la Aseguradora"
    )
    
    mensaje = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary',
            'rows': 4,
            'placeholder': 'Mensaje adicional para la aseguradora...'
        }),
        label="Mensaje Adicional"
    )


class AprobarSiniestroForm(forms.Form):
    """Formulario para aprobar siniestro (solo confirma cobertura)"""
    
    observaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary',
            'rows': 3,
            'placeholder': 'Observaciones de la aprobación...'
        }),
        label="Observaciones"
    )


class RechazarSiniestroForm(forms.Form):
    """Formulario para rechazar siniestro"""
    
    RAZONES_CHOICES = [
        ('', 'Seleccione una razón...'),
        ('no_cubierto', 'Evento no cubierto por la póliza'),
        ('fuera_plazo', 'Reportado fuera del plazo establecido'),
        ('bien_no_coincide', 'El bien no coincide con la póliza'),
        ('exclusion', 'Aplica exclusión de la póliza'),
        ('documentacion_invalida', 'Documentación inválida o insuficiente'),
        ('fraude', 'Sospecha de fraude'),
        ('otro', 'Otra razón'),
    ]
    
    razon_principal = forms.ChoiceField(
        choices=RAZONES_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary'
        }),
        label="Razón Principal"
    )
    
    detalle_rechazo = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary',
            'rows': 4,
            'placeholder': 'Detalle completo de la razón del rechazo...'
        }),
        label="Detalle del Rechazo"
    )


class LiquidarSiniestroForm(forms.Form):
    """Formulario para liquidar siniestro (ingresar montos)"""
    
    monto_aprobado = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary',
            'step': '0.01',
            'placeholder': '0.00'
        }),
        label="Monto Aprobado ($)"
    )
    
    deducible = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary',
            'step': '0.01',
            'placeholder': '0.00'
        }),
        label="Deducible ($)"
    )
    
    documento_liquidacion = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'w-full px-3 py-2 border border-border rounded-md bg-background text-foreground file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-primary file:text-primary-foreground file:cursor-pointer',
            'accept': '.pdf'
        }),
        label="Documento de Liquidación (PDF)"
    )
    
    notas = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary',
            'rows': 3,
            'placeholder': 'Notas de liquidación...'
        }),
        label="Notas"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        monto = cleaned_data.get('monto_aprobado')
        deducible = cleaned_data.get('deducible')
        
        if monto and deducible and deducible > monto:
            raise forms.ValidationError("El deducible no puede ser mayor al monto aprobado")
        
        return cleaned_data


class RegistrarPagoForm(forms.Form):
    """Formulario para registrar pago"""
    
    comprobante_pago = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'w-full px-3 py-2 border border-border rounded-md bg-background text-foreground file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-primary file:text-primary-foreground file:cursor-pointer',
            'accept': '.pdf,.jpg,.jpeg,.png'
        }),
        label="Comprobante de Pago"
    )
    
    observaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary',
            'rows': 2,
            'placeholder': 'Observaciones del pago...'
        }),
        label="Observaciones"
    )


class CerrarSiniestroForm(forms.Form):
    """Formulario para cerrar siniestro"""
    
    notas_cierre = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary',
            'rows': 3,
            'placeholder': 'Notas de cierre del siniestro...'
        }),
        label="Notas de Cierre"
    )
    
    confirmar = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox h-4 w-4 text-primary rounded border-border'
        }),
        label="Confirmo que deseo cerrar este siniestro de forma permanente"
    )
