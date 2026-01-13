from django import forms
from .models import BienAsegurado

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
