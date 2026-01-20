# Generated migration for model updates

from django.db import migrations, models
import django_fsm


class Migration(migrations.Migration):

    dependencies = [
        ('siniestros', '0003_historialestado'),
    ]

    operations = [
        # 1. Eliminar modelos que ya no se usan
        migrations.DeleteModel(
            name='DanioSiniestro',
        ),
        migrations.DeleteModel(
            name='PagareSiniestro',
        ),
        
        # 2. Actualizar opciones de DocumentoSiniestro
        migrations.AlterModelOptions(
            name='documentosiniestro',
            options={'ordering': ['-fecha_subida'], 'verbose_name': 'Documento de Siniestro', 'verbose_name_plural': 'Documentos de Siniestro'},
        ),
        
        # 3. Eliminar unique_together de DocumentoSiniestro
        migrations.AlterUniqueTogether(
            name='documentosiniestro',
            unique_together=set(),
        ),
        
        # 4. Eliminar campo subido_por de DocumentoSiniestro
        migrations.RemoveField(
            model_name='documentosiniestro',
            name='subido_por',
        ),
        
        # 5. Actualizar opciones de RoboSiniestro
        migrations.AlterModelOptions(
            name='robosiniestro',
            options={'verbose_name': 'Datos de Robo', 'verbose_name_plural': 'Datos de Robo'},
        ),
        
        # 6. Actualizar campos de RoboSiniestro (sin cambiar la PK)
        migrations.AlterField(
            model_name='robosiniestro',
            name='denuncia_policial',
            field=models.TextField(blank=True, verbose_name='Número/Detalle Denuncia Policial'),
        ),
        migrations.AlterField(
            model_name='robosiniestro',
            name='fecha_denuncia',
            field=models.DateField(blank=True, null=True, verbose_name='Fecha de Denuncia'),
        ),
        migrations.AlterField(
            model_name='robosiniestro',
            name='fiscalia',
            field=models.CharField(blank=True, max_length=200, verbose_name='Fiscalía'),
        ),
        
        # 7. Actualizar campos de Siniestro
        migrations.AlterField(
            model_name='siniestro',
            name='estado',
            field=django_fsm.FSMField(choices=[('reportado', 'Reportado'), ('docs_incompletos', 'Documentos Incompletos'), ('docs_completos', 'Documentos Completos'), ('enviado', 'Enviado a Aseguradora'), ('en_revision', 'En Revisión'), ('aprobado', 'Aprobado'), ('rechazado', 'Rechazado'), ('liquidado', 'Liquidado'), ('pagado', 'Pagado'), ('cerrado', 'Cerrado'), ('fuera_plazo', 'Fuera de Plazo')], default='reportado', max_length=50, verbose_name='Estado Actual'),
        ),
        migrations.AlterField(
            model_name='siniestro',
            name='fecha_limite_respuesta_aseguradora',
            field=models.DateField(blank=True, editable=False, null=True, verbose_name='Fecha Límite Respuesta (8 días)'),
        ),
        migrations.AlterField(
            model_name='siniestro',
            name='fuera_de_plazo',
            field=models.BooleanField(default=False, verbose_name='¿Reportado fuera del plazo de 15 días?'),
        ),
    ]
