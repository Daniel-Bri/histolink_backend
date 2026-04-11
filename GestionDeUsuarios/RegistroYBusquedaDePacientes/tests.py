from datetime import date, timedelta

from django.test import TestCase

from .models import Paciente
from .serializers import PacienteSerializer


class PacienteSerializerTests(TestCase):
    def test_valid_paciente_data(self):
        data = {
            "ci": "1234567",
            "ci_complemento": "",
            "nombre": "Maria",
            "apellido": "Lopez",
            "fecha_nacimiento": "1995-03-15",
            "genero": "F",
            "email": "maria@example.com",
            "telefono": "71234567",
            "direccion": "Calle Sin Nombre 100",
        }
        serializer = PacienteSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_invalid_ci_format(self):
        data = {
            "ci": "12ab45",
            "nombre": "Juan",
            "apellido": "Perez",
            "fecha_nacimiento": "2000-01-01",
            "genero": "M",
        }
        serializer = PacienteSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("ci", serializer.errors)

    def test_ci_unique(self):
        Paciente.objects.create(
            ci="8765432",
            ci_complemento="",
            nombres="Ana",
            apellido_paterno="Gomez",
            fecha_nacimiento=date(1988, 6, 1),
            sexo="F",
        )
        data = {
            "ci": "8765432",
            "ci_complemento": "",
            "nombre": "Otro",
            "apellido": "Paciente",
            "fecha_nacimiento": "1990-01-01",
            "genero": "M",
        }
        serializer = PacienteSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("ci", serializer.errors)

    def test_invalid_email(self):
        data = {
            "ci": "1111222",
            "nombre": "Luis",
            "apellido": "Vargas",
            "fecha_nacimiento": "1992-07-20",
            "genero": "M",
            "email": "no-es-un-email",
        }
        serializer = PacienteSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_fecha_nacimiento_futura(self):
        futura = (date.today() + timedelta(days=30)).isoformat()
        data = {
            "ci": "2222333",
            "nombre": "Pedro",
            "apellido": "Rojas",
            "fecha_nacimiento": futura,
            "genero": "O",
        }
        serializer = PacienteSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("fecha_nacimiento", serializer.errors)
