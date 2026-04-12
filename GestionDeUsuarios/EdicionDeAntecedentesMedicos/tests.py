from datetime import date

from django.test import TestCase

from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente

from .serializers import RegistroAntecedenteSerializer


class AntecedenteSerializerTests(TestCase):
    def setUp(self):
        self.paciente = Paciente.objects.create(
            ci="5555666",
            ci_complemento="",
            nombres="Carla",
            apellido_paterno="Mendez",
            fecha_nacimiento=date(1991, 11, 11),
            sexo="F",
        )

    def test_valid_antecedente_data(self):
        serializer = RegistroAntecedenteSerializer(
            data={
                "paciente": self.paciente.pk,
                "tipo": "alergia",
                "descripcion": "Alergia a penicilina",
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_paciente_no_existente(self):
        serializer = RegistroAntecedenteSerializer(
            data={
                "paciente": 999_999,
                "tipo": "personal",
                "descripcion": "Hipertensión controlada",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("paciente", serializer.errors)

    def test_descripcion_demasiado_larga(self):
        serializer = RegistroAntecedenteSerializer(
            data={
                "paciente": self.paciente.pk,
                "tipo": "quirurgico",
                "descripcion": "x" * 501,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("descripcion", serializer.errors)

    def test_tipo_invalido(self):
        serializer = RegistroAntecedenteSerializer(
            data={
                "paciente": self.paciente.pk,
                "tipo": "inventado",
                "descripcion": "Texto válido",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("tipo", serializer.errors)
