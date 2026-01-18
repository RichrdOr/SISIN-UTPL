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
            "fecha_ocurrencia": forms.DateInput(attrs={"type": "date", "class": "form-input"}),
            "descripcion": forms.Textarea(attrs={"class": "form-input", "rows": 3, "placeholder": "Describa lo ocurrido..."}),
            "tipo_bien": forms.Select(attrs={"class": "form-input"}),
            "marca": forms.TextInput(attrs={"class": "form-input"}),
            "modelo": forms.TextInput(attrs={"class": "form-input"}),
            "numero_serie": forms.TextInput(attrs={"class": "form-input"}),
            "reclamante": forms.Select(attrs={"class": "form-input"}),
            "reclamante_nombre": forms.TextInput(attrs={"class": "form-input"}),
            "reclamante_email": forms.EmailInput(attrs={"class": "form-input"}),
            "reclamante_telefono": forms.TextInput(attrs={"class": "form-input"}),
            "monto_reclamado": forms.NumberInput(attrs={"class": "form-input"}),
            "broker": forms.Select(attrs={"class": "form-input"}),
            "asesor_asignado": forms.Select(attrs={"class": "form-input"}),
            "poliza": forms.Select(attrs={"class": "form-input"}),
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
            "fecha_ocurrencia": forms.DateInput(attrs={"type": "date", "class": "form-input w-full rounded border px-3 py-2"}),
            "descripcion": forms.Textarea(attrs={"rows": 2, "class": "form-input w-full rounded border px-3 py-2"}),
            "ubicacion": forms.TextInput(attrs={"class": "form-input w-full rounded border px-3 py-2"}),
            "tipo_evento": forms.Select(attrs={"class": "form-input w-full rounded border px-3 py-2"}),
        }

class DanioForm(forms.ModelForm):
    class Meta:
        model = Danio
        fields = ["area_asignada", "tecnico_asignado"]
        widgets = {
            "area_asignada": forms.TextInput(attrs={"class": "form-input"}),
            "tecnico_asignado": forms.TextInput(attrs={"class": "form-input"}),
        }

class RoboForm(forms.ModelForm):
    class Meta:
        model = Robo
        fields = ["valor_perdido"]
        widgets = {
            "valor_perdido": forms.NumberInput(attrs={"class": "form-input"}),
        }

class HurtoForm(forms.ModelForm):
    class Meta:
        model = Hurto
        fields = ["ubicacion_ultima_vista"]
        widgets = {
            "ubicacion_ultima_vista": forms.TextInput(attrs={"class": "form-input"}),
        }
