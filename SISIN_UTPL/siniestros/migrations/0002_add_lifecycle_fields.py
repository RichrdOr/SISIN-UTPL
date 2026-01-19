# Generated manually for lifecycle fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('siniestros', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='siniestro',
            name='documentos_faltantes',
            field=models.TextField(blank=True, help_text='Lista de documentos que faltan por entregar', verbose_name='Documentos Faltantes'),
        ),
        migrations.AddField(
            model_name='siniestro',
            name='aseguradora_destino',
            field=models.CharField(blank=True, max_length=100, verbose_name='Aseguradora Destino'),
        ),
        migrations.AddField(
            model_name='siniestro',
            name='correo_aseguradora',
            field=models.EmailField(blank=True, max_length=254, verbose_name='Correo de la Aseguradora'),
        ),
        migrations.AddField(
            model_name='siniestro',
            name='mensaje_aseguradora',
            field=models.TextField(blank=True, verbose_name='Mensaje enviado a Aseguradora'),
        ),
        migrations.AddField(
            model_name='siniestro',
            name='monto_liquidado_aseguradora',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Monto Liquidado por Aseguradora'),
        ),
        migrations.AddField(
            model_name='siniestro',
            name='notas_liquidacion',
            field=models.TextField(blank=True, verbose_name='Notas de Liquidación'),
        ),
        migrations.AddField(
            model_name='siniestro',
            name='notas_cierre',
            field=models.TextField(blank=True, verbose_name='Notas de Cierre'),
        ),
    ]
