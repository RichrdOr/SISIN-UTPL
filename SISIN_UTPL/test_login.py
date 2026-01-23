#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SISIN_UTPL.settings')
django.setup()

from django.test import Client

def test_login():
    client = Client()
    
    # Probar login POST con credenciales de asesor
    response = client.post('/', {
        'username': 'MartaSeguro@gmail.com',
        'password': 'Carl3$@5',
        'rol': 'asesor'
    })
    
    print(f'Login POST status: {response.status_code}')
    if response.status_code == 302:
        print(f'Redirect location: {response.get("Location")}')
    else:
        print(f'Response content: {response.content.decode()}')

if __name__ == '__main__':
    test_login()
