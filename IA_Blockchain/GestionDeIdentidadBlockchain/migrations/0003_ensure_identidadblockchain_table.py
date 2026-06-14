from django.db import migrations


def ensure_identidad_table(apps, schema_editor):
    IdentidadBlockchain = apps.get_model("GestionDeIdentidadBlockchain", "IdentidadBlockchain")
    existing_tables = schema_editor.connection.introspection.table_names()
    if IdentidadBlockchain._meta.db_table not in existing_tables:
        schema_editor.create_model(IdentidadBlockchain)


class Migration(migrations.Migration):
    dependencies = [
        ("GestionDeIdentidadBlockchain", "0002_eventoblockchain_timestamp_bloque"),
    ]

    operations = [
        migrations.RunPython(ensure_identidad_table, migrations.RunPython.noop),
    ]
