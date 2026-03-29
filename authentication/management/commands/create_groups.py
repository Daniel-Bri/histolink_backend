"""
authentication/management/commands/create_groups.py

Management command para crear los roles (grupos) del sistema clínico Histolink.
Crea las entradas en auth_group si no existen.

Uso:
    python manage.py create_groups
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


# Roles del sistema clínico Histolink
ROLES = [
    "Médico",
    "Enfermera",
    "Administrativo",
    "Laboratorio",
    "Farmacia",
    "Auditor",
    "Director",
]


class Command(BaseCommand):
    help = "Crea los grupos/roles del sistema clínico Histolink en auth_group."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Creando roles del sistema Histolink..."))

        creados = 0
        existentes = 0

        for rol in ROLES:
            group, created = Group.objects.get_or_create(name=rol)
            if created:
                creados += 1
                self.stdout.write(self.style.SUCCESS(f"  ✓ Creado: {rol}"))
            else:
                existentes += 1
                self.stdout.write(f"  · Ya existe: {rol}")

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Listo — {creados} roles creados, {existentes} ya existían."
            )
        )
