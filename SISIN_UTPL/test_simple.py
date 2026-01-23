#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SISIN_UTPL.settings')
django.setup()

from django.contrib.auth import authenticate
from usuarios.models import PerfilUsuario

def test_login():
    print("=== Prueba de Login ===")
    
    # 1. Verificar que el usuario existe
    try:
        from django.contrib.auth.models import User
        user = User.objects.get(email='MartaSeguro@gmail.com')
        print(f"✅ Usuario encontrado: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Activo: {user.is_active}")
    except User.DoesNotExist:
        print("❌ Usuario no encontrado")
        return
    
    # 2. Verificar el perfil
    try:
        perfil = PerfilUsuario.objects.get(user=user)
        print(f"✅ Perfil encontrado: {perfil.rol}")
    except PerfilUsuario.DoesNotExist:
        print("❌ Perfil no encontrado")
        return
    
    # 3. Probar autenticación
    auth_user = authenticate(username='MartaSeguro@gmail.com', password='Carl3$@5')
    if auth_user:
        print("✅ Autenticación exitosa")
    else:
        print("❌ Autenticación fallida")
        # Probar con username en lugar de email
        auth_user = authenticate(username=user.username, password='Carl3$@5')
        if auth_user:
            print("✅ Autenticación exitosa con username")
        else:
            print("❌ Autenticación fallida con username también")

if __name__ == '__main__':
    test_login()
