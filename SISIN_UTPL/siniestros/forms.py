from django import forms
from .models import Siniestro, DocumentoSiniestro, RoboSiniestro, DanioSiniestro
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
            'tipo': forms.Select(attrs={'class': 'input'}),
            'archivo': forms.FileInput(attrs={
                'class': 'input',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'descripcion': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'Descripción opcional'
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