# Neutral migration kept for compatibility across environments.
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("GestionDePersonalDeSalud", "0003_especialidad_tenant_personalsalud_tenant_and_more"),
    ]

    operations = []
