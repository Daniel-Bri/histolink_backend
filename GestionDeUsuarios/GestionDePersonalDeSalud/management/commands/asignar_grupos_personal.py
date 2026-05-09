"""
Comando de corrección única: asigna el grupo Django correcto a cada PersonalSalud
que fue creado sin grupo (bug previo en el serializer).

Uso:
    python manage.py asignar_grupos_personal
    python manage.py asignar_grupos_personal --dry-run   # solo muestra, no guarda
"""

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from GestionDeUsuarios.GestionDePersonalDeSalud.models import PersonalSalud

ROL_A_GRUPO = {
    'medico':    'Médico',
    'enfermera': 'Enfermera',
    'admin':     'Administrativo',
}


class Command(BaseCommand):
    help = 'Asigna el grupo Django correcto a cada PersonalSalud sin grupo asignado.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Solo muestra los cambios, no los aplica.')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        corregidos = 0
        ya_ok = 0

        for personal in PersonalSalud.objects.select_related('user').all():
            user = personal.user
            group_name = ROL_A_GRUPO.get(personal.rol)
            if not group_name:
                continue

            try:
                group = Group.objects.get(name=group_name)
            except Group.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  Grupo "{group_name}" no existe. Ejecuta create_groups primero.'))
                continue

            if user.groups.filter(pk=group.pk).exists():
                ya_ok += 1
                continue

            self.stdout.write(f'  {user.username} ({personal.rol}) → grupo "{group_name}"')
            if not dry_run:
                user.groups.add(group)
            corregidos += 1

        if dry_run:
            self.stdout.write(self.style.WARNING(f'\n[DRY RUN] Se corregirían {corregidos} usuario(s). {ya_ok} ya estaban correctos.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\n✓ {corregidos} usuario(s) corregidos. {ya_ok} ya estaban correctos.'))
