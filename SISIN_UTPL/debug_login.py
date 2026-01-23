#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SISIN_UTPL.settings')
django.setup()

from django.test import Client

def debug_login():
    client = Client()
    
    # 1. Obtener la página de login
    response = client.get('/')
    print(f'Login page status: {response.status_code}')
    
    # 2. Probar login con credenciales de asesor
    response = client.post('/', {
        'username': 'MartaSeguro@gmail.com',
        'password': 'Carl3$@5',
        'rol': 'asesor'
    })
    
    print(f'Login POST status: {response.status_code}')
    
    if response.status_code == 302:
        print(f'Redirect location: {response.get("Location")}')
        print('✅ Login exitoso, redirigiendo...')
    elif response.status_code == 200:
        print('❌ Login fallido, quedando en la misma página')
        # Buscar mensajes de error
        content = response.content.decode()
        if 'error' in content.lower() or 'incorrecto' in content.lower():
            print('Hay mensajes de error en la respuesta')
        # Verificar si hay mensajes de Django
        if 'messages' in str(response.context):
            messages = list(response.context['messages'])
            for msg in messages:
                print(f'Mensaje: {msg}')
    else:
        print(f'Error inesperado: {response.status_code}')

if __name__ == '__main__':
    debug_login()
