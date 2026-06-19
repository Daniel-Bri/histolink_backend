from unittest.mock import patch, MagicMock

from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from Tenants.models import Tenant
from GestionDeUsuarios.GestionDePersonalDeSalud.models import PersonalSalud
from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente
from AtencionClinica.AperturaFichaYColaDeAtencion.models import Ficha

from .models import Cobro


class CobroTestBase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(nombre="Clinica Test", slug="clinica-test")

        grupo_admin, _ = Group.objects.get_or_create(name="Administrativo")
        self.user_admin = User.objects.create_user(username="admin_test", password="12345678")
        self.user_admin.groups.add(grupo_admin)

        self.user_medico = User.objects.create_user(username="medico_test", password="12345678")
        self.personal_medico = PersonalSalud.objects.create(
            user=self.user_medico,
            tenant=self.tenant,
            item_min_salud="MED-T1",
            rol=PersonalSalud.ROL_MEDICO,
        )

        self.paciente = Paciente.objects.create(
            tenant=self.tenant,
            ci="9999001",
            nombres="Test",
            apellido_paterno="Paciente",
            fecha_nacimiento="1990-01-01",
            sexo="M",
        )

        self.ficha_abierta = Ficha.objects.create(
            paciente=self.paciente,
            profesional_apertura=self.personal_medico,
            estado=Ficha.Estado.ABIERTA,
        )
        self.ficha_cerrada = Ficha.objects.create(
            paciente=self.paciente,
            profesional_apertura=self.personal_medico,
            estado=Ficha.Estado.CERRADA,
        )

        token = AccessToken.for_user(self.user_admin)
        token["tenant_id"] = self.tenant.id

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")


class CrearSesionCobroTests(CobroTestBase):
    @patch("GestionDeCobros.views.stripe.checkout.Session.create")
    def test_crear_cobro_datos_validos(self, mock_create):
        mock_create.return_value = MagicMock(id="cs_test_fake123", url="https://checkout.stripe.com/fake")

        response = self.client.post("/api/cobros/crear-sesion/", {
            "ficha_id": self.ficha_abierta.id,
            "concepto": "Consulta general",
            "monto": "100.00",
        }, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["checkout_url"], "https://checkout.stripe.com/fake")
        cobro = Cobro.objects.get(id=response.data["cobro_id"])
        self.assertEqual(cobro.estado, Cobro.Estado.PENDIENTE)
        self.assertEqual(cobro.stripe_session_id, "cs_test_fake123")

    @patch("GestionDeCobros.views.stripe.checkout.Session.create")
    def test_cobrar_ficha_cerrada_falla(self, mock_create):
        response = self.client.post("/api/cobros/crear-sesion/", {
            "ficha_id": self.ficha_cerrada.id,
            "concepto": "Consulta general",
            "monto": "100.00",
        }, format="json")

        self.assertEqual(response.status_code, 400)
        mock_create.assert_not_called()


class WebhookCobroTests(CobroTestBase):
    def setUp(self):
        super().setUp()
        self.cobro = Cobro.objects.create(
            tenant=self.tenant,
            ficha=self.ficha_abierta,
            paciente=self.paciente,
            concepto="Consulta general",
            monto="100.00",
            estado=Cobro.Estado.PENDIENTE,
            stripe_session_id="cs_test_webhook123",
        )

    @patch("GestionDeCobros.views.stripe.Webhook.construct_event")
    def test_webhook_checkout_completed_actualiza_estado(self, mock_construct_event):
        mock_construct_event.return_value = {
            "type": "checkout.session.completed",
            "data": {"object": {"id": "cs_test_webhook123"}},
        }

        response = self.client.post(
            "/api/cobros/webhook/",
            data="{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="fake_signature",
        )

        self.assertEqual(response.status_code, 200)
        self.cobro.refresh_from_db()
        self.assertEqual(self.cobro.estado, Cobro.Estado.PAGADO)
        self.assertIsNotNone(self.cobro.fecha_pago)

    @patch("GestionDeCobros.views.stripe.Webhook.construct_event")
    def test_webhook_firma_invalida_falla(self, mock_construct_event):
        import stripe
        mock_construct_event.side_effect = stripe.error.SignatureVerificationError(
            "Firma inválida", "fake_signature"
        )

        response = self.client.post(
            "/api/cobros/webhook/",
            data="{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="firma_falsa",
        )

        self.assertEqual(response.status_code, 400)
        self.cobro.refresh_from_db()
        self.assertEqual(self.cobro.estado, Cobro.Estado.PENDIENTE)


class AnularCobroTests(CobroTestBase):
    def test_anular_cobro_pagado_falla(self):
        cobro_pagado = Cobro.objects.create(
            tenant=self.tenant,
            ficha=self.ficha_abierta,
            paciente=self.paciente,
            concepto="Consulta general",
            monto="100.00",
            estado=Cobro.Estado.PAGADO,
            fecha_pago=timezone.now(),
        )

        response = self.client.post(f"/api/cobros/{cobro_pagado.id}/anular/")

        self.assertEqual(response.status_code, 400)
        cobro_pagado.refresh_from_db()
        self.assertEqual(cobro_pagado.estado, Cobro.Estado.PAGADO)

    def test_anular_cobro_pendiente_funciona(self):
        cobro_pendiente = Cobro.objects.create(
            tenant=self.tenant,
            ficha=self.ficha_abierta,
            paciente=self.paciente,
            concepto="Consulta general",
            monto="100.00",
            estado=Cobro.Estado.PENDIENTE,
        )

        response = self.client.post(f"/api/cobros/{cobro_pendiente.id}/anular/")

        self.assertEqual(response.status_code, 200)
        cobro_pendiente.refresh_from_db()
        self.assertEqual(cobro_pendiente.estado, Cobro.Estado.ANULADO)