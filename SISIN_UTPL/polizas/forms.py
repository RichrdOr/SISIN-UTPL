from django import forms
from .models import Poliza, BienAsegurado, RamoPoliza

class PolizaForm(forms.ModelForm):
    class Meta:
        model = Poliza
        fields = [
            'numero_poliza', 'titular', 'tipo_poliza', 'aseguradora', 
            'fecha_emision', 'fecha_vencimiento', 'fecha_inicio', 'fecha_fin', 
            'prima', 'cobertura', 'bien'
        ]
        widgets = {
            'fecha_emision': forms.DateInput(attrs={'type': 'date', 'class': 'input'}),
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date', 'class': 'input'}),
            'fecha_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'input'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date', 'class': 'input'}),
            'cobertura': forms.Textarea(attrs={'rows': 2, 'class': 'input'}),
        }

class RamoPolizaForm(forms.ModelForm):
    class Meta:
        model = RamoPoliza
        # EXCLUIMOS 'poliza' porque el formset lo llena solo
        exclude = ['poliza']
        widgets = {
            'grupo': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Grupo'}),
            'subgrupo': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Subgrupo'}),
            'ramo': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Ramo'}),
            'suma_asegurada': forms.NumberInput(attrs={'class': 'input', 'step': '0.01'}),
            'deducible_porcentaje': forms.NumberInput(attrs={'class': 'input', 'step': '0.01'}),
            # Añade widgets para los demás campos decimales si los vas a mostrar
        }