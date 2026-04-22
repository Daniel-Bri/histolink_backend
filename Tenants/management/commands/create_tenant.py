"""
Crea un establecimiento (tenant) nuevo junto con su usuario Director inicial.

Uso:
    python manage.py create_tenant --nombre "Hospital San Juan" --username director1 --password Seguro123
    python manage.py create_tenant --nombre "Clinica Norte" --username dir_norte --password Pass456 --nit 12345678
"""

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from GestionDeUsuarios.GestionDePersonalDeSalud.models import PersonalSalud
from Tenants.models import Tenant


class Command(BaseCommand):
    help = "Crea un nuevo establecimiento (tenant) con su usuario Director inicial."

    def add_arguments(self, parser):
        parser.add_argument('--nombre',   required=True,  help="Nombre del establecimiento")
        parser.add_argument('--username', required=True,  help="Username del Director")
        parser.add_argument('--password', required=True,  help="Contraseña del Director")
        parser.add_argument('--email',    default='',     help="Email del Director (opcional)")
        parser.add_argument('--slug',     default='',     help="Slug del tenant (se genera automáticamente si se omite)")
        parser.add_argument('--nit',      default='',     help="NIT del establecimiento (opcional)")

    def handle(self, *args, **options):
        nombre   = options['nombre']
        slug     = options['slug'] or slugify(nombre)
        username = options['username']

        # 1. Crear tenant
        tenant, t_created = Tenant.objects.get_or_create(
            slug=slug,
            defaults={'nombre': nombre, 'nit': options['nit']},
        )
        if t_created:
            self.stdout.write(self.style.SUCCESS(f"  [OK] Establecimiento creado: {tenant.nombre} (slug: {slug})"))
        else:
            self.stdout.write(f"  [--] Establecimiento ya existe: {tenant.nombre}")

        # 2. Crear usuario Director
        user, u_created = User.objects.get_or_create(
            username=username,
            defaults={'email': options['email']},
        )
        if u_created:
            user.set_password(options['password'])
            user.save()
            self.stdout.write(self.style.SUCCESS(f"  [OK] Usuario creado: {username}"))
        else:
            self.stdout.write(f"  [--] Usuario ya existe: {username}")

        # 3. Asignar rol Director
        director_group, _ = Group.objects.get_or_create(name='Director')
        user.groups.add(director_group)

        # 4. Crear perfil PersonalSalud vinculado al tenant
        perfil, p_created = PersonalSalud.objects.get_or_create(
            user=user,
            defaults={
                'tenant': tenant,
                'item_min_salud': 'DIR-001',
                'rol': PersonalSalud.ROL_ADMIN,
            },
        )
        if not p_created and perfil.tenant != tenant:
            perfil.tenant = tenant
            perfil.save(update_fields=['tenant'])

        if p_created:
            self.stdout.write(self.style.SUCCESS(f"  [OK] Perfil Director asignado al establecimiento"))
        else:
            self.stdout.write(f"  [--] Perfil ya existe, tenant actualizado si era diferente")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Listo -- Establecimiento '{tenant.nombre}' con Director '{username}' configurado."
        ))
