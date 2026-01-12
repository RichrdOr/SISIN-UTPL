from django import forms
from .models import Siniestro, Evento


class SiniestroForm(forms.ModelForm):
    class Meta:
        model = Siniestro
        fields = [
            "fecha_apertura",
            "tiempo",
            "poliza",
            "tipo_bien",
            "marca",
            "modelo",
            "numero_serie",
        ]


class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = [
            "descripcion",
            "fecha_ocurrencia",
            "fecha_reporte",
            "ubicacion",
            "tipo_evento",
        ]
