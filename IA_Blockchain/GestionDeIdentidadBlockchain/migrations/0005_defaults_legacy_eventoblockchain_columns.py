from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("GestionDeIdentidadBlockchain", "0004_ensure_eventoblockchain_columns"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE "GestionDeIdentidadBlockchain_eventoblockchain"
                ALTER COLUMN "payload" SET DEFAULT '{}',
                ALTER COLUMN "hash_previo" SET DEFAULT '',
                ALTER COLUMN "hash_actual" SET DEFAULT '',
                ALTER COLUMN "creado_en" SET DEFAULT NOW();
            """,
            reverse_sql=migrations.RunSQL.noop,
        )
    ]
