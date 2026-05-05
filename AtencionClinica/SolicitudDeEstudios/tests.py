# T009 — Pruebas OrdenEstudio

from datetime import date

from django.contrib.auth.models import Group, User
from django.db import connection
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from AtencionClinica.ConsultaMedicaSOAP.models import Consulta
from AtencionClinica.SolicitudDeEstudios.models import OrdenEstudio
from GestionDeUsuarios.GestionDePersonalDeSalud.models import PersonalSalud
from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente


def _paciente(ci="11223344"):
    return Paciente.objects.create(
        ci=ci,
        ci_complemento="",
        nombres="Ana",
        apellido_paterno="Pérez",
        apellido_materno="",
        fecha_nacimiento=date(1991, 5, 5),
        sexo="F",
    )


class OrdenEstudioModeloTests(TestCase):
    def setUp(self):
        self.u_doc = User.objects.create_user(username="m1", password="x")
        self.u_lab = User.objects.create_user(username="lab1", password="x")
        self.ps_doc = PersonalSalud.objects.create(
            user=self.u_doc,
            item_min_salud="ME-T009-01",
            rol=PersonalSalud.ROL_MEDICO,
        )
        self.ps_lab = PersonalSalud.objects.create(
            user=self.u_lab,
            item_min_salud="LAB-T009-01",
            rol=PersonalSalud.ROL_ENFERMERA,
        )
        self.p = _paciente()
        from AtencionClinica.AperturaFichaYColaDeAtencion.models import Ficha

        self.ficha = Ficha.objects.create(
            paciente=self.p,
            profesional_apertura=self.ps_doc,
            estado=Ficha.Estado.CERRADA,
        )
        self.consulta = Consulta.objects.create(
            ficha=self.ficha,
            medico=self.u_doc,
            motivo_consulta="m",
            historia_enfermedad_actual="h",
            impresion_diagnostica="i",
            codigo_cie10_principal="A00",
        )

    def test_urgente_requiere_motivo(self):
        o = OrdenEstudio(
            consulta=self.consulta,
            tipo=OrdenEstudio.TipoEstudio.LAB,
            descripcion="Hemograma",
            indicacion_clinica="fiebre",
            urgente=True,
            motivo_urgencia="",
            medico_solicitante=self.ps_doc,
            estado=OrdenEstudio.Estado.SOLICITADA,
        )
        from django.core.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            o.full_clean()

    def test_transicion_invalida_solicitada_completada(self):
        from django.core.exceptions import ValidationError

        o = OrdenEstudio.objects.create(
            consulta=self.consulta,
            tipo=OrdenEstudio.TipoEstudio.LAB,
            descripcion="Hemograma",
            indicacion_clinica="fiebre",
            medico_solicitante=self.ps_doc,
            urgente=False,
        )
        o.estado = OrdenEstudio.Estado.COMPLETADA
        o.resultado_texto = "X"
        with self.assertRaises(ValidationError):
            o.save()

    def test_transiciones_estado(self):
        o = OrdenEstudio.objects.create(
            consulta=self.consulta,
            tipo=OrdenEstudio.TipoEstudio.LAB,
            descripcion="Hemograma",
            indicacion_clinica="fiebre",
            medico_solicitante=self.ps_doc,
            urgente=False,
        )
        o.estado = OrdenEstudio.Estado.EN_PROCESO
        o.full_clean()
        o.save()
        self.assertIsNotNone(o.fecha_inicio_proceso)
        o.estado = OrdenEstudio.Estado.COMPLETADA
        o.resultado_texto = "Normal"
        o.full_clean()
        o.save()
        self.assertIsNotNone(o.fecha_completada)

    def test_indice_estado_urgente_existe_postgresql(self):
        if connection.vendor != "postgresql":
            self.skipTest("EXPLAIN solo en PostgreSQL")
        with connection.cursor() as c:
            c.execute(
                "EXPLAIN SELECT * FROM \"SolicitudDeEstudios_ordenestudio\" "
                "WHERE estado = %s AND urgente = %s",
                [OrdenEstudio.Estado.SOLICITADA, True],
            )
            plan = "\n".join(row[0] for row in c.fetchall()).lower()
            self.assertTrue("scan" in plan, msg=plan)


class OrdenEstudioAPITests(APITestCase):
    LIST = "/api/ordenes-estudio/"

    def setUp(self):
        Group.objects.get_or_create(name="Médico")
        Group.objects.get_or_create(name="Laboratorio")
        Group.objects.get_or_create(name="Director")

        self.user_med = User.objects.create_user(username="md", password="pw")
        self.user_lab = User.objects.create_user(username="lb", password="pw")
        self.user_dir = User.objects.create_user(username="dr", password="pw")

        self.user_med.groups.add(Group.objects.get(name="Médico"))
        self.user_lab.groups.add(Group.objects.get(name="Laboratorio"))
        self.user_dir.groups.add(Group.objects.get(name="Director"))

        self.ps_med = PersonalSalud.objects.create(
            user=self.user_med,
            item_min_salud="APIMED-1",
            rol=PersonalSalud.ROL_MEDICO,
        )
        self.ps_lab = PersonalSalud.objects.create(
            user=self.user_lab,
            item_min_salud="APILAB-1",
            rol=PersonalSalud.ROL_ENFERMERA,
        )
        self.ps_dir = PersonalSalud.objects.create(
            user=self.user_dir,
            item_min_salud="APIDIR-1",
            rol=PersonalSalud.ROL_ADMIN,
        )

        self.p = _paciente("55667788")
        from AtencionClinica.AperturaFichaYColaDeAtencion.models import Ficha

        self.ficha = Ficha.objects.create(
            paciente=self.p,
            profesional_apertura=self.ps_med,
            estado=Ficha.Estado.CERRADA,
        )
        self.consulta = Consulta.objects.create(
            ficha=self.ficha,
            medico=self.user_med,
            motivo_consulta="m",
            historia_enfermedad_actual="h",
            impresion_diagnostica="i",
            codigo_cie10_principal="B01",
        )

    def test_crear_orden_medico(self):
        self.client.force_authenticate(self.user_med)
        r = self.client.post(
            self.LIST,
            {
                "consulta_id": self.consulta.pk,
                "tipo": "LAB",
                "descripcion": "PCR",
                "indicacion_clinica": "fiebre",
                "urgente": False,
            },
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertTrue(r.data["correlativo_orden"].startswith("ORD-"))

    def test_urgente_sin_motivo_400(self):
        self.client.force_authenticate(self.user_med)
        r = self.client.post(
            self.LIST,
            {
                "consulta_id": self.consulta.pk,
                "tipo": "LAB",
                "descripcion": "PCR",
                "indicacion_clinica": "fiebre",
                "urgente": True,
            },
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filtro_urgente_false_list(self):
        self.client.force_authenticate(self.user_med)
        OrdenEstudio.objects.create(
            consulta=self.consulta,
            tipo=OrdenEstudio.TipoEstudio.LAB,
            descripcion="A",
            indicacion_clinica="i",
            medico_solicitante=self.ps_med,
            urgente=True,
            motivo_urgencia="crit",
        )
        OrdenEstudio.objects.create(
            consulta=self.consulta,
            tipo=OrdenEstudio.TipoEstudio.LAB,
            descripcion="B",
            indicacion_clinica="i",
            medico_solicitante=self.ps_med,
            urgente=False,
        )
        r = self.client.get(self.LIST + "?urgente=false")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        data = r.data
        rows = data["results"] if isinstance(data, dict) and "results" in data else data
        self.assertGreater(len(rows), 0)
        self.assertTrue(all(not row["urgente"] for row in rows))

    def test_filtro_urgente_list(self):
        self.client.force_authenticate(self.user_med)
        OrdenEstudio.objects.create(
            consulta=self.consulta,
            tipo=OrdenEstudio.TipoEstudio.LAB,
            descripcion="A",
            indicacion_clinica="i",
            medico_solicitante=self.ps_med,
            urgente=True,
            motivo_urgencia="sep",
        )
        OrdenEstudio.objects.create(
            consulta=self.consulta,
            tipo=OrdenEstudio.TipoEstudio.LAB,
            descripcion="B",
            indicacion_clinica="i",
            medico_solicitante=self.ps_med,
            urgente=False,
        )
        r = self.client.get(self.LIST + "?urgente=true")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        data = r.data
        rows = data["results"] if isinstance(data, dict) and "results" in data else data
        self.assertTrue(all(row["urgente"] for row in rows))

    def test_cola_laboratorio_lab_ok_medico_403(self):
        o1 = OrdenEstudio.objects.create(
            consulta=self.consulta,
            tipo=OrdenEstudio.TipoEstudio.LAB,
            descripcion="x",
            indicacion_clinica="y",
            medico_solicitante=self.ps_med,
            urgente=True,
            motivo_urgencia="critico",
        )
        self.client.force_authenticate(self.user_lab)
        r = self.client.get("/api/ordenes-estudio/cola-laboratorio/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn("urgentes", r.data)
        self.assertIn("total_pendientes", r.data)
        self.assertGreaterEqual(r.data["total_pendientes"], 1)

        self.client.force_authenticate(self.user_med)
        r2 = self.client.get("/api/ordenes-estudio/cola-laboratorio/")
        self.assertEqual(r2.status_code, status.HTTP_403_FORBIDDEN)

    def test_lab_cambiar_estado_a_completada(self):
        o = OrdenEstudio.objects.create(
            consulta=self.consulta,
            tipo=OrdenEstudio.TipoEstudio.LAB,
            descripcion="x",
            indicacion_clinica="y",
            medico_solicitante=self.ps_med,
        )
        o.estado = OrdenEstudio.Estado.EN_PROCESO
        o.save()
        self.client.force_authenticate(self.user_lab)
        url = f"{self.LIST}{o.pk}/cambiar-estado/"
        r = self.client.patch(
            url,
            {"estado": OrdenEstudio.Estado.COMPLETADA, "resultado_texto": "OK"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["estado"], OrdenEstudio.Estado.COMPLETADA)

    def test_cambiar_estado_tecnico_responsable_id(self):
        o = OrdenEstudio.objects.create(
            consulta=self.consulta,
            tipo=OrdenEstudio.TipoEstudio.LAB,
            descripcion="x",
            indicacion_clinica="y",
            medico_solicitante=self.ps_med,
        )
        self.client.force_authenticate(self.user_lab)
        url = f"{self.LIST}{o.pk}/cambiar-estado/"
        r = self.client.patch(
            url,
            {"estado": OrdenEstudio.Estado.EN_PROCESO, "tecnico_responsable_id": self.ps_lab.pk},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        o.refresh_from_db()
        self.assertEqual(o.tecnico_responsable_id, self.ps_lab.pk)
