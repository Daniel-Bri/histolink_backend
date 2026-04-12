from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("GestionDePersonalDeSalud", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="especialidad",
            name="nombre",
            field=models.CharField(max_length=120, unique=True),
        ),
    ]
