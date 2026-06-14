from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("GestionDeIdentidadBlockchain", "0003_ensure_identidadblockchain_table"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE "GestionDeIdentidadBlockchain_eventoblockchain"
                ADD COLUMN IF NOT EXISTS "numero_bloque" integer NOT NULL DEFAULT 0,
                ADD COLUMN IF NOT EXISTS "anterior_hash" varchar(64) NOT NULL DEFAULT '',
                ADD COLUMN IF NOT EXISTS "documento_tipo" varchar(50) NOT NULL DEFAULT '',
                ADD COLUMN IF NOT EXISTS "documento_id" integer NOT NULL DEFAULT 0,
                ADD COLUMN IF NOT EXISTS "hash_documento" varchar(64) NOT NULL DEFAULT '',
                ADD COLUMN IF NOT EXISTS "firma_rsa" text NOT NULL DEFAULT '',
                ADD COLUMN IF NOT EXISTS "firmado_por_id" integer NULL,
                ADD COLUMN IF NOT EXISTS "timestamp" timestamp with time zone NOT NULL DEFAULT NOW(),
                ADD COLUMN IF NOT EXISTS "bloque_hash" varchar(64) NOT NULL DEFAULT '';
            """,
            reverse_sql=migrations.RunSQL.noop,
        )
    ]
