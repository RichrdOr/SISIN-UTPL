from django import forms
from .models import Siniestro, Danio, Robo, Hurto

class SiniestroForm(forms.ModelForm):
    class Meta:
        model = Siniestro
        exclude = ['estado', 'fecha_apertura', 'fecha_cierre']