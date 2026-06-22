from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente
from IA_Blockchain.GestionDeIdentidadBlockchain.models import EventoBlockchain
from SeguridadAvanzadaYAdministracion.Auditoria.models import RegistroAuditoria
from SeguridadAvanzadaYAdministracion.BreakGlass_Solicitud.models import BreakGlassSolicitud
from Tenants.models import Tenant


class BreakGlassAprobacionAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for group_name in ["Médico", "Auditor", "Director", "Administrativo"]:
            Group.objects.get_or_create(name=group_name)

    def setUp(self):
        self.client = APIClient()
        self.tenant = Tenant.objects.create(nombre="Hospital BG", slug="hospital-bg-aprobacion")
        self.medico = User.objects.create_user(username="med.apr", password="Demo12345!")
        self.medico.groups.add(Group.objects.get(name="Médico"))
        self.auditor = User.objects.create_user(username="aud.apr", password="Demo12345!")
        self.auditor.groups.add(Group.objects.get(name="Auditor"))
        self.director = User.objects.create_user(username="dir.apr", password="Demo12345!")
        self.director.groups.add(Group.objects.get(name="Director"))
        self.otro_medico = User.objects.create_user(username="med.otro", password="Demo12345!")
        self.otro_medico.groups.add(Group.objects.get(name="Médico"))

        self.paciente = Paciente.objects.create(
            tenant=self.tenant,
            ci="BG2001",
            ci_complemento="",
            nombres="Carlos",
            apellido_paterno="Prueba",
            apellido_materno="Demo",
            fecha_nacimiento="1990-01-01",
            sexo="M",
            autoidentificacion="NE",
            tipo_seguro="SUS",
            creado_por=self.medico,
        )

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def _solicitud(self, **kwargs):
        data = {
            "tenant": self.tenant,
            "solicitante": self.medico,
            "paciente": self.paciente,
            "justificacion": "Paciente inconsciente y con riesgo vital, se requiere acceso inmediato.",
            "nivel_urgencia": "MEDIA",
            "estado": "PENDIENTE",
        }
        data.update(kwargs)
        return BreakGlassSolicitud.objects.create(**data)

    def test_aprobar_solicitud_pendiente_como_auditor(self):
        solicitud = self._solicitud()
        self._auth(self.auditor)
        res = self.client.post(f"/api/emergencia/{solicitud.id}/aprobar/", {}, format="json")
        self.assertEqual(res.status_code, 200)
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, "APROBADA")
        self.assertEqual(solicitud.aprobado_por, self.auditor)
        self.assertTrue(BreakGlassSolicitud.objects.filter(id=solicitud.id, estado="APROBADA").exists())
        self.assertTrue(
            RegistroAuditoria.objects.filter(
                modelo="BreakGlassSolicitud",
                objeto_id=str(solicitud.id),
                accion="UPDATE",
            ).exists()
        )
        self.assertTrue(
            EventoBlockchain.objects.filter(
                tipo_evento="APROBACION_BREAK_GLASS",
                documento_tipo="BreakGlassSolicitud",
                documento_id=solicitud.id,
            ).exists()
        )

    def test_aprobar_bloquea_autoaprobacion(self):
        solicitud = self._solicitud()
        self._auth(self.medico)
        res = self.client.post(f"/api/emergencia/{solicitud.id}/aprobar/", {}, format="json")
        self.assertEqual(res.status_code, 403)

    def test_aprobar_bloquea_rol_no_permitido(self):
        solicitud = self._solicitud()
        self._auth(self.otro_medico)
        res = self.client.post(f"/api/emergencia/{solicitud.id}/aprobar/", {}, format="json")
        self.assertEqual(res.status_code, 403)

    def test_aprobar_inexistente(self):
        self._auth(self.auditor)
        res = self.client.post("/api/emergencia/9999/aprobar/", {}, format="json")
        self.assertEqual(res.status_code, 404)

    def test_aprobar_ya_aprobada(self):
        solicitud = self._solicitud(estado="APROBADA", aprobado_por=self.director)
        self._auth(self.auditor)
        res = self.client.post(f"/api/emergencia/{solicitud.id}/aprobar/", {}, format="json")
        self.assertEqual(res.status_code, 409)

    def test_rechazar_solicitud_pendiente_con_motivo_valido(self):
        solicitud = self._solicitud()
        self._auth(self.director)
        res = self.client.post(
            f"/api/emergencia/{solicitud.id}/rechazar/",
            {"motivo_rechazo": "No existe justificacion clinica suficiente"},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, "RECHAZADA")
        self.assertEqual(solicitud.aprobado_por, self.director)
        self.assertEqual(solicitud.motivo_rechazo, "No existe justificacion clinica suficiente")
        self.assertIn("notificacion", res.data)
        self.assertTrue(
            RegistroAuditoria.objects.filter(
                modelo="BreakGlassSolicitud",
                objeto_id=str(solicitud.id),
                accion="UPDATE",
            ).exists()
        )
        self.assertTrue(
            EventoBlockchain.objects.filter(
                tipo_evento="RECHAZO_BREAK_GLASS",
                documento_tipo="BreakGlassSolicitud",
                documento_id=solicitud.id,
            ).exists()
        )

    def test_rechazar_bloquea_motivo_corto(self):
        solicitud = self._solicitud()
        self._auth(self.director)
        res = self.client.post(
            f"/api/emergencia/{solicitud.id}/rechazar/",
            {"motivo_rechazo": "corto"},
            format="json",
        )
        self.assertEqual(res.status_code, 400)

    def test_rechazar_bloquea_autoaprobacion(self):
        solicitud = self._solicitud()
        self._auth(self.medico)
        res = self.client.post(
            f"/api/emergencia/{solicitud.id}/rechazar/",
            {"motivo_rechazo": "No cumple criterios clinicos suficientes"},
            format="json",
        )
        self.assertEqual(res.status_code, 403)

    def test_rechazar_ya_rechazada(self):
        solicitud = self._solicitud(estado="RECHAZADA", aprobado_por=self.director)
        self._auth(self.auditor)
        res = self.client.post(
            f"/api/emergencia/{solicitud.id}/rechazar/",
            {"motivo_rechazo": "No cumple criterios clinicos suficientes"},
            format="json",
        )
        self.assertEqual(res.status_code, 409)
