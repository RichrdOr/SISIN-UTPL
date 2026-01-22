import os

import django
from django.db import connection

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SISIN_UTPL.settings")
django.setup()

print("☢️  INICIANDO REINICIO DE POSTGRESQL...")

try:
    with connection.cursor() as cursor:
        # Esto borra TODO el esquema público (tablas, vistas, etc.)
        print("   -> Borrando esquema 'public'...")
        cursor.execute("DROP SCHEMA public CASCADE;")

        # Esto lo vuelve a crear limpio
        print("   -> Creando esquema 'public' limpio...")
        cursor.execute("CREATE SCHEMA public;")

    print("✅ ¡ÉXITO! Base de datos PostgreSQL limpia y lista para migraciones.")

except Exception as e:
    print(f"❌ ERROR: {e}")
    print(
        "Revisa que tu usuario y contraseña en settings.py sean correctos y SIN TILDES."
    )
