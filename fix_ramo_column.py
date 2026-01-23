import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','SISIN_UTPL.settings')
django.setup()
from django.db import connection

def column_exists(table, column):
    with connection.cursor() as c:
        c.execute("SELECT 1 FROM information_schema.columns WHERE table_name=%s AND column_name=%s", [table, column])
        return bool(c.fetchone())

def fk_exists(table, constraint_name):
    with connection.cursor() as c:
        c.execute("SELECT 1 FROM information_schema.table_constraints WHERE table_name=%s AND constraint_name=%s", [table, constraint_name])
        return bool(c.fetchone())

TABLE='siniestros_siniestro'
COL='ramo_id'
CONSTRAINT='fk_siniestros_siniestro_ramo'

with connection.cursor() as c:
    if column_exists(TABLE, COL):
        print(f"Column {COL} already exists on {TABLE}")
    else:
        try:
            c.execute(f"ALTER TABLE {TABLE} ADD COLUMN {COL} bigint")
            print(f"Added column {COL} on {TABLE}")
        except Exception as e:
            print('Error adding column:', e)

    if fk_exists(TABLE, CONSTRAINT):
        print(f"Constraint {CONSTRAINT} already exists on {TABLE}")
    else:
        try:
            c.execute(f"ALTER TABLE {TABLE} ADD CONSTRAINT {CONSTRAINT} FOREIGN KEY ({COL}) REFERENCES polizas_ramopoliza(id) ON DELETE NO ACTION")
            print(f"Added FK constraint {CONSTRAINT}")
        except Exception as e:
            print('Error adding FK constraint:', e)

print('Done')
