import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','SISIN_UTPL.settings')
django.setup()
from django.db import connection

def cols(table):
    c = connection.cursor()
    c.execute("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name=%s ORDER BY ordinal_position", [table])
    return c.fetchall()

print('=== Tables to inspect ===')
for t in ('polizas_ramopoliza','siniestros_siniestro'):
    try:
        rows = cols(t)
        print(f"Table {t}: {len(rows)} columns")
        for r in rows:
            print('  ', r)
    except Exception as e:
        print(f"Table {t}: ERROR -> {e}")

print('\n=== siniestros migrations applied (django_migrations) ===')
with connection.cursor() as c:
    c.execute("SELECT name, applied FROM django_migrations WHERE app='siniestros' ORDER BY applied")
    for row in c.fetchall():
        print('  ', row)

print('\n=== polizas migrations applied (django_migrations) ===')
with connection.cursor() as c:
    c.execute("SELECT name, applied FROM django_migrations WHERE app='polizas' ORDER BY applied")
    for row in c.fetchall():
        print('  ', row)
