from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente
from Tenants.models import Tenant
from .models import PermisoPaciente


class PermisoPacienteAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for g in ["Médico", "Auditor", "Director", "Administrativo", "Enfermera"]:
            Group.objects.get_or_create(name=g)

    def setUp(self):
        self.client = APIClient()
        self.tenant = Tenant.objects.create(nombre="Hospital General", slug="hospital-general")

        self.medico = User.objects.create_user(username="dr.sanchez", password="Password123!", first_name="Juan", last_name="Sanchez")
        self.medico.groups.add(Group.objects.get(name="Médico"))

        self.medico2 = User.objects.create_user(username="dr.perez", password="Password123!", first_name="Pedro", last_name="Perez")
        self.medico2.groups.add(Group.objects.get(name="Médico"))

        self.paciente = Paciente.objects.create(
            tenant=self.tenant,
            ci="1234567",
            ci_complemento="",
            nombres="Maria",
            apellido_paterno="Gomez",
            apellido_materno="Lopez",
            fecha_nacimiento="1995-05-15",
            sexo="F",
            autoidentificacion="NE",
            tipo_seguro="CNS",
            creado_por=self.medico,
        )

        self.paciente2 = Paciente.objects.create(
            tenant=self.tenant,
            ci="7654321",
            ci_complemento="",
            nombres="Carlos",
            apellido_paterno="Rojas",
            apellido_materno="Paz",
            fecha_nacimiento="1988-10-20",
            sexo="M",
            autoidentificacion="NE",
            tipo_seguro="SUS",
            creado_por=self.medico,
        )

        self.user_admin = User.objects.create_user(username="admin.user", password="Password123!")
        self.user_admin.groups.add(Group.objects.get(name="Administrativo"))

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_otorgar_permiso_exitoso(self):
        self._auth(self.user_admin)
        payload = {
            "paciente_id": self.paciente.id,
            "medico_id": self.medico.id,
        }
        res = self.client.post("/api/permisos/otorgar/", payload, format="json")
        self.assertEqual(res.status_code, 201)
        self.assertTrue(res.data["activo"])
        self.assertEqual(res.data["paciente_id"], self.paciente.id)
        self.assertEqual(res.data["medico_id"], self.medico.id)
        self.assertEqual(res.data["otorgado_por_id"], self.user_admin.id)
        self.assertIsNone(res.data["fecha_revocacion"])

        # Verificar en base de datos
        db_permiso = PermisoPaciente.objects.get(id=res.data["id"])
        self.assertTrue(db_permiso.activo)
        self.assertEqual(db_permiso.otorgado_por, self.user_admin)

    def test_otorgar_permiso_duplicado_activo_falla(self):
        self._auth(self.user_admin)
        # Otorga el primero
        payload = {
            "paciente_id": self.paciente.id,
            "medico_id": self.medico.id,
        }
        res1 = self.client.post("/api/permisos/otorgar/", payload, format="json")
        self.assertEqual(res1.status_code, 201)

        # Otorga el segundo (duplicado activo)
        res2 = self.client.post("/api/permisos/otorgar/", payload, format="json")
        self.assertEqual(res2.status_code, 400)
        self.assertIn("non_field_errors", res2.data)

    def test_otorgar_permiso_reactiva_inactivo(self):
        self._auth(self.user_admin)
        
        # 1. Crear el permiso
        payload = {
            "paciente_id": self.paciente.id,
            "medico_id": self.medico.id,
        }
        res_create = self.client.post("/api/permisos/otorgar/", payload, format="json")
        self.assertEqual(res_create.status_code, 201)
        permiso_id = res_create.data["id"]

        # 2. Revocar el permiso
        res_revoke = self.client.post("/api/permisos/revocar/", payload, format="json")
        self.assertEqual(res_revoke.status_code, 200)
        self.assertFalse(res_revoke.data["activo"])
        self.assertIsNotNone(res_revoke.data["fecha_revocacion"])

        # 3. Otorgar de nuevo (debe reactivar el mismo permiso)
        # Usamos otro usuario para otorgar de nuevo y comprobar que cambia el otorgado_por
        self._auth(self.medico2)
        res_reactivate = self.client.post("/api/permisos/otorgar/", payload, format="json")
        self.assertEqual(res_reactivate.status_code, 201)
        self.assertEqual(res_reactivate.data["id"], permiso_id)
        self.assertTrue(res_reactivate.data["activo"])
        self.assertIsNone(res_reactivate.data["fecha_revocacion"])
        self.assertEqual(res_reactivate.data["otorgado_por_id"], self.medico2.id)

        # Verificar que solo hay 1 registro en la BD en total
        self.assertEqual(PermisoPaciente.objects.filter(paciente=self.paciente, medico=self.medico).count(), 1)

    def test_revocar_permiso_exitoso(self):
        self._auth(self.user_admin)
        # Otorga
        payload = {
            "paciente_id": self.paciente.id,
            "medico_id": self.medico.id,
        }
        self.client.post("/api/permisos/otorgar/", payload, format="json")

        # Revoca
        res = self.client.post("/api/permisos/revocar/", payload, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.data["activo"])
        self.assertIsNotNone(res.data["fecha_revocacion"])

        db_permiso = PermisoPaciente.objects.get(id=res.data["id"])
        self.assertFalse(db_permiso.activo)
        self.assertIsNotNone(db_permiso.fecha_revocacion)

    def test_revocar_permiso_no_existente_falla(self):
        self._auth(self.user_admin)
        payload = {
            "paciente_id": self.paciente.id,
            "medico_id": self.medico.id,
        }
        res = self.client.post("/api/permisos/revocar/", payload, format="json")
        self.assertEqual(res.status_code, 400)
        self.assertIn("non_field_errors", res.data)

    def test_listar_permisos(self):
        self._auth(self.user_admin)
        # Crear permisos
        PermisoPaciente.objects.create(
            paciente=self.paciente,
            medico=self.medico,
            otorgado_por=self.user_admin,
            tenant=self.tenant,
            activo=True,
        )
        PermisoPaciente.objects.create(
            paciente=self.paciente2,
            medico=self.medico2,
            otorgado_por=self.user_admin,
            tenant=self.tenant,
            activo=False,
            fecha_revocacion=timezone.now(),
        )

        # GET sin filtros
        res = self.client.get("/api/permisos/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 2)

        # GET filtrado por paciente
        res_paciente = self.client.get(f"/api/permisos/?paciente_id={self.paciente.id}")
        self.assertEqual(len(res_paciente.data), 1)
        self.assertEqual(res_paciente.data[0]["paciente_id"], self.paciente.id)

        # GET filtrado por medico
        res_medico = self.client.get(f"/api/permisos/?medico_id={self.medico2.id}")
        self.assertEqual(len(res_medico.data), 1)
        self.assertEqual(res_medico.data[0]["medico_id"], self.medico2.id)

        # GET filtrado por activo
        res_activo = self.client.get("/api/permisos/?activo=true")
        self.assertEqual(len(res_activo.data), 1)
        self.assertTrue(res_activo.data[0]["activo"])
