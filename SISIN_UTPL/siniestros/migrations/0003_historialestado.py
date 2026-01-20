# Generated migration for HistorialEstado model

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('siniestros', '0002_add_lifecycle_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistorialEstado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado_anterior', models.CharField(blank=True, max_length=30, verbose_name='Estado Anterior')),
                ('estado_nuevo', models.CharField(max_length=30, verbose_name='Estado Nuevo')),
                ('fecha_cambio', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Fecha de Cambio')),
                ('usuario', models.CharField(default='Sistema', max_length=100, verbose_name='Usuario')),
                ('observaciones', models.TextField(blank=True, verbose_name='Observaciones')),
                ('siniestro', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='historial_estados', to='siniestros.siniestro')),
            ],
            options={
                'verbose_name': 'Historial de Estado',
                'verbose_name_plural': 'Historial de Estados',
                'ordering': ['-fecha_cambio'],
            },
        ),
    ]
