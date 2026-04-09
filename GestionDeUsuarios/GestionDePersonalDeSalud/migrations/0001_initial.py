from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Especialidad",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=100, unique=True)),
            ],
            options={
                "ordering": ["nombre"],
            },
        ),
        migrations.CreateModel(
            name="PersonalSalud",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("item_min_salud", models.CharField(max_length=20, unique=True)),
                ("rol", models.CharField(choices=[("medico", "Medico"), ("enfermera", "Enfermera"), ("admin", "Admin")], max_length=20)),
                ("telefono", models.CharField(blank=True, max_length=30, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("especialidad", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="personal_salud", to="GestionDePersonalDeSalud.especialidad")),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="perfil_personal_salud", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
