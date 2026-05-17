from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente
from IA_Blockchain.GestionDeIdentidadBlockchain.models import EventoBlockchain
from SeguridadAvanzadaYAdministracion.Auditoria.models import RegistroAuditoria
from Tenants.models import Tenant

from .models import BreakGlassSolicitud


class BreakGlassSolicitudAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for g in ["Médico", "Auditor", "Director", "Administrativo", "Enfermera"]:
            Group.objects.get_or_create(name=g)

    def setUp(self):
        self.client = APIClient()
        self.tenant = Tenant.objects.create(nombre="Hospital BG", slug="hospital-bg")

        self.medico = User.objects.create_user(username="med.bg", password="Demo12345!", first_name="Med")
        self.medico.groups.add(Group.objects.get(name="Médico"))
        self.auditor = User.objects.create_user(username="aud.bg", password="Demo12345!")
        self.auditor.groups.add(Group.objects.get(name="Auditor"))
        self.enfermera = User.objects.create_user(username="enf.bg", password="Demo12345!")
        self.enfermera.groups.add(Group.objects.get(name="Enfermera"))

        self.paciente = Paciente.objects.create(
            tenant=self.tenant,
            ci="BG1001",
            ci_complemento="",
            nombres="Ana",
            apellido_paterno="Prueba",
            apellido_materno="Demo",
            fecha_nacimiento="1990-01-01",
            sexo="F",
            autoidentificacion="NE",
            tipo_seguro="SUS",
            creado_por=self.medico,
        )

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def _post(self, **kwargs):
        payload = {
            "paciente_id": self.paciente.id,
            "justificacion": "Paciente inconsciente en shock, se requiere acceso clínico inmediato.",
            "nivel_urgencia": "MEDIA",
        }
        payload.update(kwargs)
        return self.client.post("/api/seguridad/break-glass/solicitar/", payload, format="json")

    def test_solicitud_normal_crea_pendiente(self):
        self._auth(self.medico)
        res = self._post()
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["estado"], "PENDIENTE")
        self.assertIsNone(res.data["acceso_desde"])
        self.assertIsNone(res.data["acceso_hasta"])

    def test_solicitud_alta_otorga_acceso_temporal_2h(self):
        self._auth(self.medico)
        res = self._post(nivel_urgencia="ALTA")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["estado"], "PENDIENTE")
        self.assertIn("advertencia", res.data)
        obj = BreakGlassSolicitud.objects.get(id=res.data["id"])
        self.assertIsNotNone(obj.acceso_desde)
        self.assertIsNotNone(obj.acceso_hasta)
        delta = obj.acceso_hasta - obj.acceso_desde
        self.assertTrue(timedelta(hours=1, minutes=59) <= delta <= timedelta(hours=2, minutes=1))

    def test_bloqueo_duplicado_pendiente(self):
        self._auth(self.medico)
        r1 = self._post()
        self.assertEqual(r1.status_code, 201)
        r2 = self._post()
        self.assertEqual(r2.status_code, 400)

    def test_justificacion_corta(self):
        self._auth(self.medico)
        res = self._post(justificacion="muy corta")
        self.assertEqual(res.status_code, 400)
        self.assertIn("justificacion", res.data)

    def test_usuario_sin_auth(self):
        res = self._post()
        self.assertEqual(res.status_code, 401)

    def test_usuario_sin_rol_medico_no_puede_solicitar(self):
        self._auth(self.enfermera)
        res = self._post()
        self.assertEqual(res.status_code, 403)

    def test_mis_solicitudes(self):
        self._auth(self.medico)
        self._post()
        res = self.client.get("/api/seguridad/break-glass/mis-solicitudes/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)

    def test_pendientes_permitido_auditor(self):
        self._auth(self.medico)
        self._post()
        self._auth(self.auditor)
        res = self.client.get("/api/seguridad/break-glass/pendientes/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)

    def test_pendientes_denegado_otro_rol(self):
        self._auth(self.medico)
        self._post()
        self._auth(self.enfermera)
        res = self.client.get("/api/seguridad/break-glass/pendientes/")
        self.assertEqual(res.status_code, 403)

    def test_anti_autoaprobacion_modelo(self):
        solicitud = BreakGlassSolicitud(
            tenant=self.tenant,
            solicitante=self.medico,
            paciente=self.paciente,
            justificacion="Justificación suficientemente larga para validación.",
            nivel_urgencia="MEDIA",
            estado="APROBADA",
            aprobado_por=self.medico,
        )
        with self.assertRaises(Exception):
            solicitud.save()

    def test_registra_blockchain_y_auditoria(self):
        self._auth(self.medico)
        res = self._post()
        self.assertEqual(res.status_code, 201)
        solicitud = BreakGlassSolicitud.objects.get(id=res.data["id"])
        self.assertIsNotNone(solicitud.evento_blockchain_id)
        ev = EventoBlockchain.objects.get(id=solicitud.evento_blockchain_id)
        self.assertEqual(ev.tipo_evento, "BREAK_GLASS_SOLICITUD")
        self.assertEqual(ev.payload["paciente_id"], self.paciente.id)
        self.assertTrue(
            RegistroAuditoria.objects.filter(
                modelo="BreakGlassSolicitud",
                objeto_id=str(solicitud.id),
                accion="CREATE",
            ).exists()
        )

    def test_acceso_expirado_helper(self):
        solicitud = BreakGlassSolicitud.objects.create(
            tenant=self.tenant,
            solicitante=self.medico,
            paciente=self.paciente,
            justificacion="Justificación suficientemente larga para validación.",
            nivel_urgencia="MEDIA",
            estado="PENDIENTE",
            acceso_desde=timezone.now() - timedelta(hours=3),
            acceso_hasta=timezone.now() - timedelta(hours=1),
        )
        self.assertTrue(solicitud.acceso_expirado)
        self.assertFalse(solicitud.acceso_activo)
