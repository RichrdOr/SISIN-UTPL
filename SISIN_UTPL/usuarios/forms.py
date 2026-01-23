from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import PerfilUsuario

class LoginFormularioPersonalizado(AuthenticationForm):
    rol = forms.ChoiceField(
        choices=[('gerente', 'Gerente'), ('asesor', 'Asesor')],
        required=True,
        widget=forms.RadioSelect(attrs={
            'class': 'hidden'  # Ocultamos el select original porque usamos tarjetas
        })
    )
    
    username = forms.CharField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200',
            'placeholder': 'Correo electrónico',
            'autocomplete': 'email'
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200',
            'placeholder': 'Contraseña',
            'autocomplete': 'current-password'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Correo Electrónico'
        self.fields['password'].label = 'Contraseña'
        self.fields['rol'].label = 'Tipo de Acceso'
