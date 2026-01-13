from django import forms
from .models import Siniestro, Evento, Danio, Robo, Hurto

class SiniestroForm(forms.ModelForm):
    class Meta:
        model = Siniestro
        fields = [
            "poliza",
            "reclamante",
            "reclamante_nombre",
            "reclamante_email",
            "reclamante_telefono",
            "fecha_ocurrencia",
            "descripcion",
            "monto_reclamado",
            "tipo_bien",
            "marca",
            "modelo",
            "numero_serie",
            "broker",
            "asesor_asignado",
        ]
        widgets = {
            "fecha_ocurrencia": forms.DateInput(attrs={"type": "date"}),
            "descripcion": forms.Textarea(attrs={"rows":3}),
        }

class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = [
            "descripcion",
            "fecha_ocurrencia",
            "ubicacion",
            "tipo_evento",
        ]
        widgets = {
            "fecha_ocurrencia": forms.DateInput(attrs={"type": "date"}),
            "descripcion": forms.Textarea(attrs={"rows":2}),
        }

class DanioForm(forms.ModelForm):
    class Meta:
        model = Danio
        fields = ["area_asignada", "tecnico_asignado"]

class RoboForm(forms.ModelForm):
    class Meta:
        model = Robo
        fields = ["valor_perdido"]

class HurtoForm(forms.ModelForm):
    class Meta:
        model = Hurto
        fields = ["ubicacion_ultima_vista"]
