# Tests T003 — Ficha / correlativo / transiciones / API

from datetime import date
from urllib.parse import urlencode

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from AtencionClinica.AperturaFichaYColaDeAtencion.models import Ficha
from GestionDeUsuarios.GestionDePersonalDeSalud.models import PersonalSalud
from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente


def _paciente_basico(ci="87654321"):
    return Paciente.objects.create(
        ci=ci,
        ci_complemento="",
        nombres="Ana María",
        apellido_paterno="Pérez",
        apellido_materno="López",
        fecha_nacimiento=date(1990, 1, 15),
        sexo="F",
    )


class FichaCorrelativoYTransicionesTest(TestCase):
    """Correlativo y reglas de negocio a nivel modelo."""

    def setUp(self):
        self.user = User.objects.create_user(username="doc1", password="x")
        self.ps = PersonalSalud.objects.create(
            user=self.user,
            item_min_salud="DOC-UNIT-001",
            rol=PersonalSalud.ROL_MEDICO,
        )
        self.p1 = _paciente_basico("11111111")
        self.p2 = _paciente_basico("22222222")

    def test_correlativo_primer_year_secuencial(self):
        f1 = Ficha(
            paciente=self.p1,
            profesional_apertura=self.ps,
            estado=Ficha.Estado.ABIERTA,
        )
        f1.full_clean()
        f1.save()
        y = timezone.now().year
        self.assertRegex(f1.correlativo, rf"^FICHA-{y}-00001$")

        f2 = Ficha(
            paciente=self.p2,
            profesional_apertura=self.ps,
            estado=Ficha.Estado.ABIERTA,
        )
        f2.full_clean()
        f2.save()
        self.assertRegex(f2.correlativo, rf"^FICHA-{y}-00002$")

    def test_transiciones_validas_abierta_a_cerrada_flujo_lineal(self):
        f = Ficha.objects.create(
            paciente=self.p1,
            profesional_apertura=self.ps,
            estado=Ficha.Estado.ABIERTA,
        )
        # ABIERTA → EN_TRIAJE
        f.estado = Ficha.Estado.EN_TRIAJE
        f.full_clean()
        f.save()
        # → EN_ATENCION
        f.estado = Ficha.Estado.EN_ATENCION
        f.full_clean()
        f.save()
        self.assertIsNotNone(f.fecha_inicio_atencion)
        # → CERRADA
        f.estado = Ficha.Estado.CERRADA
        f.full_clean()
        f.save()
        self.assertIsNotNone(f.fecha_cierre)

    def test_transicion_cancelada_desde_abierta_ok(self):
        f = Ficha.objects.create(
            paciente=self.p1,
            profesional_apertura=self.ps,
            estado=Ficha.Estado.ABIERTA,
        )
        f.estado = Ficha.Estado.CANCELADA
        f.full_clean()
        f.save()
        self.assertIsNotNone(f.fecha_cierre)

    def test_no_retroceder_en_atencion_a_triaje(self):
        f = Ficha.objects.create(
            paciente=self.p1,
            profesional_apertura=self.ps,
            estado=Ficha.Estado.ABIERTA,
        )
        f.estado = Ficha.Estado.EN_TRIAJE
        f.save()
        f.estado = Ficha.Estado.EN_ATENCION
        f.save()
        f.estado = Ficha.Estado.EN_TRIAJE
        with self.assertRaises(ValidationError):
            f.full_clean()

    def test_no_cambiar_estado_tras_cerrada(self):
        f = Ficha.objects.create(
            paciente=self.p1,
            profesional_apertura=self.ps,
            estado=Ficha.Estado.ABIERTA,
        )
        for e in (
            Ficha.Estado.EN_TRIAJE,
            Ficha.Estado.EN_ATENCION,
            Ficha.Estado.CERRADA,
        ):
            f.estado = e
            f.full_clean()
            f.save()
        f.estado = Ficha.Estado.CANCELADA
        with self.assertRaises(ValidationError):
            f.full_clean()


class FichaAPIFiltrosTest(APITestCase):
    """CRUD REST y filtros."""

    LIST_URL = "/api/fichas/"

    def setUp(self):
        self.user = User.objects.create_user(username="adm1", password="pass123XX")
        self.ps = PersonalSalud.objects.create(
            user=self.user,
            item_min_salud="PER-UNIT-901",
            rol=PersonalSalud.ROL_ADMIN,
        )
        self.p = _paciente_basico("55667777")
        self.client.force_authenticate(user=self.user)

    def test_crear_via_post_profesional_apertura_implicito(self):
        res = self.client.post(
            self.LIST_URL,
            {"paciente_id": self.p.pk},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["paciente"]["ci"], "55667777")
        self.assertIn("nombre_completo", res.data["paciente"])
        self.assertEqual(res.data["profesional_apertura"]["id"], self.ps.pk)

    def test_filtros_listado_estado_y_en_curso(self):
        f_cerrada = Ficha.objects.create(
            paciente=self.p,
            profesional_apertura=self.ps,
            estado=Ficha.Estado.CERRADA,
        )
        f_abierta = Ficha.objects.create(
            paciente=_paciente_basico("99887777"),
            profesional_apertura=self.ps,
            estado=Ficha.Estado.ABIERTA,
        )

        def _ids(resp_data):
            rows = resp_data["results"] if isinstance(resp_data, dict) and "results" in resp_data else resp_data
            return {row["id"] for row in rows}

        qs = urlencode({"estado": Ficha.Estado.CERRADA})
        r = self.client.get(f"{self.LIST_URL}?{qs}")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        ids_cerradas = _ids(r.data)
        self.assertIn(f_cerrada.pk, ids_cerradas)
        self.assertNotIn(f_abierta.pk, ids_cerradas)

        r2 = self.client.get(f"{self.LIST_URL}?en_curso=true")
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        cur = _ids(r2.data)
        self.assertIn(f_abierta.pk, cur)

    def test_cambiar_estado_action(self):
        f = Ficha.objects.create(
            paciente=self.p,
            profesional_apertura=self.ps,
            estado=Ficha.Estado.ABIERTA,
        )
        url = f"{self.LIST_URL}{f.pk}/cambiar-estado/"
        res = self.client.patch(url, {"estado": Ficha.Estado.EN_TRIAJE}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["estado"], Ficha.Estado.EN_TRIAJE)
