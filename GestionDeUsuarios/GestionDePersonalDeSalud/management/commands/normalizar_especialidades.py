from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction

from GestionDeUsuarios.GestionDePersonalDeSalud.models import (
    Especialidad,
    PersonalSalud,
    normalizar_nombre_especialidad,
)


class Command(BaseCommand):
    help = "Detecta y unifica especialidades duplicadas por acentos/espacios/case."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Aplica cambios (sin este flag, solo muestra diagnóstico).",
        )

    def handle(self, *args, **options):
        apply_changes = options["apply"]
        grupos = {}
        for esp in Especialidad.objects.all().order_by("id"):
            key = normalizar_nombre_especialidad(esp.nombre)
            grupos.setdefault(key, []).append(esp)

        duplicados = {k: v for k, v in grupos.items() if len(v) > 1}
        if not duplicados:
            self.stdout.write(self.style.SUCCESS("No se encontraron duplicados lógicos de especialidades."))
            return

        self.stdout.write("Duplicados detectados:")
        for key, rows in duplicados.items():
            nombres = ", ".join(f"{r.id}:{r.nombre}" for r in rows)
            self.stdout.write(f"  - {key}: {nombres}")

        if not apply_changes:
            self.stdout.write("Ejecuta con --apply para unificar y reasignar FKs.")
            return

        try:
            with transaction.atomic():
                for key, rows in duplicados.items():
                    canonical = rows[0]

                    for dup in rows[1:]:
                        PersonalSalud.objects.filter(especialidad_id=dup.id).update(especialidad_id=canonical.id)
                        dup.delete()
        except IntegrityError as exc:
            raise CommandError(
                f"IntegrityError: {exc}\n"
                "No se pudo unificar por conflicto de unicidad o FK. Revisa registros duplicados y dependencias."
            ) from exc

        self.stdout.write(self.style.SUCCESS("Unificación completada y FKs de PersonalSalud reasignadas."))
