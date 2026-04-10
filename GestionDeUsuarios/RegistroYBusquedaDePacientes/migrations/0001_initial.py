import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Paciente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ci', models.CharField(db_index=True, max_length=15, verbose_name='Carnet de Identidad')),
                ('ci_complemento', models.CharField(blank=True, default='', max_length=5, verbose_name='Complemento del CI')),
                ('nombres', models.CharField(max_length=150, verbose_name='Nombres')),
                ('apellido_paterno', models.CharField(max_length=100, verbose_name='Apellido paterno')),
                ('apellido_materno', models.CharField(blank=True, default='', max_length=100, verbose_name='Apellido materno')),
                ('fecha_nacimiento', models.DateField(verbose_name='Fecha de nacimiento')),
                ('sexo', models.CharField(choices=[('M', 'Masculino'), ('F', 'Femenino')], max_length=1, verbose_name='Sexo')),
                ('autoidentificacion', models.CharField(choices=[('QUECHUA', 'Quechua'), ('AYMARA', 'Aymara'), ('GUARANI', 'Guaraní'), ('CHIQUITANO', 'Chiquitano'), ('MOJENO', 'Mojeno'), ('MESTIZO', 'Mestizo'), ('BLANCO', 'Blanco'), ('AFRO', 'Afroboliviano'), ('OTRO', 'Otro'), ('NE', 'No Especificado')], default='NE', max_length=20, verbose_name='Autoidentificación étnica')),
                ('telefono', models.CharField(blank=True, default='', max_length=20, verbose_name='Teléfono')),
                ('direccion', models.TextField(blank=True, default='', verbose_name='Dirección')),
                ('nombre_responsable', models.CharField(blank=True, default='', max_length=200, verbose_name='Nombre del responsable')),
                ('telefono_responsable', models.CharField(blank=True, default='', max_length=20, verbose_name='Teléfono del responsable')),
                ('parentesco_responsable', models.CharField(blank=True, default='', max_length=50, verbose_name='Parentesco del responsable')),
                ('tipo_seguro', models.CharField(choices=[('SUS', 'SUS'), ('CNS', 'CNS'), ('COSSMIL', 'COSSMIL'), ('BANCARIA', 'Bancaria'), ('PETROLERA', 'Petrolera'), ('PRIVADO', 'Privado'), ('PARTICULAR', 'Particular')], default='PARTICULAR', max_length=20, verbose_name='Tipo de seguro')),
                ('numero_asegurado', models.CharField(blank=True, default='', max_length=50, verbose_name='Número de asegurado')),
                ('activo', models.BooleanField(default=True, verbose_name='Activo')),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='pacientes_registrados', to=settings.AUTH_USER_MODEL, verbose_name='Registrado por')),
                ('creado_en', models.DateTimeField(auto_now_add=True, verbose_name='Creado en')),
                ('actualizado_en', models.DateTimeField(auto_now=True, verbose_name='Actualizado en')),
            ],
            options={
                'verbose_name': 'Paciente',
                'verbose_name_plural': 'Pacientes',
                'ordering': ['apellido_paterno', 'apellido_materno', 'nombres'],
                'unique_together': {('ci', 'ci_complemento')},
                'constraints': [models.CheckConstraint(check=~models.Q(ci=''), name='paciente_ci_no_vacio')],
                'indexes': [models.Index(fields=['ci'], name='idx_paciente_ci'), models.Index(fields=['apellido_paterno', 'apellido_materno'], name='idx_paciente_apellidos')],
            },
        ),
    ]