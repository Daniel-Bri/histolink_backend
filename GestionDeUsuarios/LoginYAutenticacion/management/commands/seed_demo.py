import json
from datetime import date
from pathlib import Path

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import FieldError, ValidationError
from django.db import IntegrityError, ProgrammingError, transaction

from AtencionClinica.AperturaFichaYColaDeAtencion.models import Ficha, TipoAtencion
from AtencionClinica.ConsultaMedicaSOAP.models import Consulta
from GestionDeUsuarios.GestionDePersonalDeSalud.models import (
    Especialidad,
    PersonalSalud,
    normalizar_nombre_especialidad,
)
from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente
from Tenants.models import Tenant


TIPOS_ATENCION_BASE = [
    ("Consulta general", "Atención médica ambulatoria general."),
    ("Emergencia", "Atención prioritaria por urgencia o riesgo inmediato."),
    ("Control", "Consulta de control de tratamiento o evolución."),
    ("Seguimiento", "Seguimiento clínico posterior a consulta o alta."),
]

USUARIOS_DEMO = [
    {
        "username": "demo.medico",
        "first_name": "Mario",
        "last_name": "Soria",
        "email": "demo.medico@histolink.local",
        "group": "Médico",
        "rol": PersonalSalud.ROL_MEDICO,
        "item_min_salud": "DEMO-MED-001",
        "especialidad": "Medicina General",
    },
    {
        "username": "demo.medico2",
        "first_name": "Andrea",
        "last_name": "Torrez",
        "email": "demo.medico2@histolink.local",
        "group": "Médico",
        "rol": PersonalSalud.ROL_MEDICO,
        "item_min_salud": "DEMO-MED-002",
        "especialidad": "Pediatría",
    },
    {
        "username": "demo.enfermera",
        "first_name": "Lucia",
        "last_name": "Vargas",
        "email": "demo.enfermera@histolink.local",
        "group": "Enfermera",
        "rol": PersonalSalud.ROL_ENFERMERA,
        "item_min_salud": "DEMO-ENF-001",
        "especialidad": "Enfermería General",
    },
    {
        "username": "demo.admin",
        "first_name": "Martin",
        "last_name": "Suarez",
        "email": "demo.admin@histolink.local",
        "group": "Administrativo",
        "rol": PersonalSalud.ROL_ADMIN,
        "item_min_salud": "DEMO-ADM-001",
        "especialidad": None,
    },
]

PACIENTES_DEMO = [
    {"ci": "DEMO1001", "nombres": "Camila", "apellido_paterno": "Rojas", "apellido_materno": "Flores", "fecha_nacimiento": date(1992, 3, 14), "sexo": "F", "autoidentificacion": "MESTIZO", "tipo_seguro": "SUS"},
    {"ci": "DEMO1002", "nombres": "Luis", "apellido_paterno": "Quispe", "apellido_materno": "Mamani", "fecha_nacimiento": date(1985, 8, 2), "sexo": "M", "autoidentificacion": "AYMARA", "tipo_seguro": "PARTICULAR"},
    {"ci": "DEMO1003", "nombres": "Valeria", "apellido_paterno": "Paz", "apellido_materno": "Vega", "fecha_nacimiento": date(2000, 11, 22), "sexo": "F", "autoidentificacion": "QUECHUA", "tipo_seguro": "CNS"},
    {"ci": "DEMO1004", "nombres": "Diego", "apellido_paterno": "Santos", "apellido_materno": "Lopez", "fecha_nacimiento": date(1977, 6, 18), "sexo": "M", "autoidentificacion": "MESTIZO", "tipo_seguro": "SUS"},
    {"ci": "DEMO1005", "nombres": "Paola", "apellido_paterno": "Rivera", "apellido_materno": "Cruz", "fecha_nacimiento": date(1995, 1, 9), "sexo": "F", "autoidentificacion": "NE", "tipo_seguro": "COSSMIL"},
]

CONSULTAS_DEMO = [
    {"motivo_consulta": "Cefalea tensional de 2 días.", "historia_enfermedad_actual": "Dolor opresivo frontal, sin vómitos ni fiebre.", "impresion_diagnostica": "Cefalea tensional", "codigo_cie10_principal": "G44.2", "estado": "COMPLETADA"},
    {"motivo_consulta": "Dolor lumbar posterior a esfuerzo físico.", "historia_enfermedad_actual": "Lumbalgia mecánica sin irradiación.", "impresion_diagnostica": "Lumbalgia", "codigo_cie10_principal": "M54.5", "estado": "COMPLETADA"},
    {"motivo_consulta": "Control de hipertensión arterial.", "historia_enfermedad_actual": "Paciente estable, adherencia parcial a medicación.", "impresion_diagnostica": "Hipertensión esencial", "codigo_cie10_principal": "I10", "estado": "BORRADOR"},
    {"motivo_consulta": "Rinofaringitis aguda.", "historia_enfermedad_actual": "Congestión nasal y odinofagia leve de 48 horas.", "impresion_diagnostica": "Resfriado común", "codigo_cie10_principal": "J00", "estado": "COMPLETADA"},
    {"motivo_consulta": "Dolor abdominal inespecífico.", "historia_enfermedad_actual": "Dolor tipo cólico, sin signos de alarma.", "impresion_diagnostica": "Dolor abdominal no especificado", "codigo_cie10_principal": "R10.4", "estado": "BORRADOR"},
]


class Command(BaseCommand):
    help = "T014: Carga datos demo idempotentes (especialidades, tipos de atención, personal, pacientes, fichas y consultas)."

    def add_arguments(self, parser):
        parser.add_argument("--tenant-slug", default="demo-hospital", help="Slug del tenant demo.")
        parser.add_argument("--password", default="Demo12345!", help="Contraseña demo para usuarios creados.")

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                tenant = self._seed_tenant(options["tenant_slug"])
                especialidades = self._seed_especialidades()
                self._seed_tipos_atencion()
                users_by_username = self._seed_usuarios_y_personal(
                    tenant=tenant,
                    especialidades=especialidades,
                    default_password=options["password"],
                )
                self._seed_pacientes_fichas_consultas(tenant=tenant, users_by_username=users_by_username)
        except ProgrammingError as exc:
            raise CommandError(
                f"ProgrammingError: {exc}\n"
                "Probable causa: faltan migraciones aplicadas.\n"
                "Solución: python manage.py migrate"
            ) from exc
        except IntegrityError as exc:
            raise CommandError(
                f"IntegrityError: {exc}\n"
                "Probable causa: conflicto de FK o unicidad.\n"
                "Solución: revisa que existan Tenant/User/PersonalSalud y que item_min_salud sea único por tenant."
            ) from exc
        except FieldError as exc:
            raise CommandError(
                f"FieldError: {exc}\n"
                "Probable causa: campo inexistente por diferencia de modelos/migraciones.\n"
                "Solución: verifica cambios locales y corre migrate."
            ) from exc
        except ValidationError as exc:
            raise CommandError(
                f"ValidationError: {exc}\n"
                "Probable causa: datos demo inválidos para reglas del modelo."
            ) from exc

        self.stdout.write(self.style.SUCCESS("T014 completada: datos demo cargados sin duplicar."))

    def _seed_tenant(self, slug: str) -> Tenant:
        tenant, _ = Tenant.objects.update_or_create(
            slug=slug,
            defaults={
                "nombre": "Hospital Demo Histolink",
                "nit": "DEMO-0001",
                "direccion": "Zona Demo 123",
                "telefono": "70000000",
                "activo": True,
            },
        )
        return tenant

    def _seed_especialidades(self) -> dict[str, Especialidad]:
        base_dir = Path(__file__).resolve().parents[4]
        fixture_path = base_dir / "GestionDeUsuarios" / "GestionDePersonalDeSalud" / "fixtures" / "especialidades.json"
        if not fixture_path.exists():
            raise CommandError(
                f"No existe fixture de especialidades en: {fixture_path}\n"
                "Solución: crea/restaura especialidades.json antes de correr seed_demo."
            )

        with fixture_path.open("r", encoding="utf-8") as fh:
            rows = json.load(fh)

        resultado: dict[str, Especialidad] = {}
        existentes = list(Especialidad.objects.filter(tenant__isnull=True).order_by("id"))
        for row in rows:
            nombre = row.get("fields", {}).get("nombre", "").strip()
            if not nombre:
                continue
            nombre_normalizado = normalizar_nombre_especialidad(nombre)

            obj = next(
                (e for e in existentes if normalizar_nombre_especialidad(e.nombre) == nombre_normalizado),
                None,
            )
            if obj is None:
                obj = Especialidad.objects.create(nombre=nombre, tenant=None)
                existentes.append(obj)
            elif obj.nombre != nombre:
                # Conserva forma canónica del fixture (con tildes correctas) sin crear duplicado.
                obj.nombre = nombre
                obj.save(update_fields=["nombre"])
            resultado[nombre] = obj
        return resultado

    def _seed_tipos_atencion(self):
        for nombre, descripcion in TIPOS_ATENCION_BASE:
            TipoAtencion.objects.update_or_create(
                nombre=nombre,
                defaults={"descripcion": descripcion, "activo": True},
            )

    def _seed_usuarios_y_personal(self, tenant: Tenant, especialidades: dict[str, Especialidad], default_password: str):
        by_username: dict[str, User] = {}
        for d in USUARIOS_DEMO:
            group, _ = Group.objects.get_or_create(name=d["group"])
            user, created = User.objects.get_or_create(
                username=d["username"],
                defaults={
                    "first_name": d["first_name"],
                    "last_name": d["last_name"],
                    "email": d["email"],
                    "is_active": True,
                },
            )
            if created:
                user.set_password(default_password)
                user.save()
            user.groups.add(group)

            especialidad = especialidades.get(d["especialidad"]) if d["especialidad"] else None
            if d["especialidad"] and especialidad is None:
                raise CommandError(
                    f"Especialidad requerida no encontrada: {d['especialidad']}\n"
                    "Solución: verifica especialidades.json y evita renombrar acentos."
                )

            PersonalSalud.objects.update_or_create(
                user=user,
                defaults={
                    "tenant": tenant,
                    "item_min_salud": d["item_min_salud"],
                    "rol": d["rol"],
                    "especialidad": especialidad,
                    "is_active": True,
                },
            )
            by_username[d["username"]] = user
        return by_username

    def _seed_pacientes_fichas_consultas(self, tenant: Tenant, users_by_username: dict[str, User]):
        user_medico = users_by_username.get("demo.medico")
        if not user_medico:
            raise CommandError("Falta usuario demo.medico; no se pueden crear pacientes/fichas/consultas.")

        try:
            ps_medico = user_medico.perfil_personal_salud
        except PersonalSalud.DoesNotExist as exc:
            raise CommandError("Falta PersonalSalud para demo.medico; no se pueden crear fichas.") from exc

        for i, p in enumerate(PACIENTES_DEMO):
            paciente, _ = Paciente.objects.update_or_create(
                ci=p["ci"],
                ci_complemento="",
                tenant=tenant,
                defaults={
                    "nombres": p["nombres"],
                    "apellido_paterno": p["apellido_paterno"],
                    "apellido_materno": p["apellido_materno"],
                    "fecha_nacimiento": p["fecha_nacimiento"],
                    "sexo": p["sexo"],
                    "autoidentificacion": p["autoidentificacion"],
                    "tipo_seguro": p["tipo_seguro"],
                    "creado_por": user_medico,
                    "activo": True,
                },
            )

            fichas = Ficha.objects.filter(paciente=paciente).order_by("id")
            if fichas.exists():
                ficha = fichas.first()
                if ficha.profesional_apertura_id != ps_medico.id:
                    ficha.profesional_apertura = ps_medico
                if ficha.estado != Ficha.Estado.CERRADA:
                    ficha.estado = Ficha.Estado.CERRADA
                ficha.save()
            else:
                ficha = Ficha.objects.create(
                    paciente=paciente,
                    profesional_apertura=ps_medico,
                    estado=Ficha.Estado.CERRADA,
                )

            c = CONSULTAS_DEMO[i]
            Consulta.objects.update_or_create(
                ficha=ficha,
                codigo_cie10_principal=c["codigo_cie10_principal"],
                defaults={
                    "tenant": tenant,
                    "medico": user_medico,
                    "estado": c["estado"],
                    "motivo_consulta": c["motivo_consulta"],
                    "historia_enfermedad_actual": c["historia_enfermedad_actual"],
                    "impresion_diagnostica": c["impresion_diagnostica"],
                },
            )
