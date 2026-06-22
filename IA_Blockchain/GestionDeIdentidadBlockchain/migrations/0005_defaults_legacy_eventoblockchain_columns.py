from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("GestionDeIdentidadBlockchain", "0004_ensure_eventoblockchain_columns"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE "GestionDeIdentidadBlockchain_eventoblockchain"
                ADD COLUMN IF NOT EXISTS "payload"    jsonb        NOT NULL DEFAULT '{}',
                ADD COLUMN IF NOT EXISTS "hash_previo" varchar(64)  NOT NULL DEFAULT '',
                ADD COLUMN IF NOT EXISTS "hash_actual" varchar(64)  NOT NULL DEFAULT '',
                ADD COLUMN IF NOT EXISTS "creado_en"  timestamptz  NOT NULL DEFAULT NOW();

            ALTER TABLE "GestionDeIdentidadBlockchain_eventoblockchain"
                ALTER COLUMN "payload"    SET DEFAULT '{}',
                ALTER COLUMN "hash_previo" SET DEFAULT '',
                ALTER COLUMN "hash_actual" SET DEFAULT '',
                ALTER COLUMN "creado_en"  SET DEFAULT NOW();
            """,
            reverse_sql=migrations.RunSQL.noop,
        )
    ]
