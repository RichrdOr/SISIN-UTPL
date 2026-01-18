from django import forms
from .models import BienAsegurado, RamoPoliza

class BienAseguradoForm(forms.ModelForm):
    class Meta:
        model = BienAsegurado
        fields = [
            "descripcion",
            "tipo_bien",
            "estado",
            "valor",
            "zona",
        ]

class RamoPolizaForm(forms.ModelForm):
    class Meta:
        model = RamoPoliza
        fields = "__all__"