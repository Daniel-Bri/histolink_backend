from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Especialidad, PersonalSalud
from .serializers import EspecialidadSerializer, PersonalSaludSerializer

User = get_user_model()


class EspecialidadSerializerTests(TestCase):
    def test_serializer_valid_data(self):
        serializer = EspecialidadSerializer(data={"nombre": "Cardiologia"})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_serializer_invalid_data(self):
        serializer = EspecialidadSerializer(data={"nombre": "Cardio123"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("nombre", serializer.errors)

    def test_serializer_unique_constraints(self):
        Especialidad.objects.create(nombre="Pediatria")
        serializer = EspecialidadSerializer(data={"nombre": "Pediatria"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("nombre", serializer.errors)

    def test_serializer_optional_fields(self):
        serializer = EspecialidadSerializer(data={"nombre": "Medicina Interna"})
        self.assertTrue(serializer.is_valid(), serializer.errors)


class PersonalSaludSerializerTests(TestCase):
    def setUp(self):
        self.user_1 = User.objects.create_user(
            username="medico1", email="medico1@test.com", password="pass1234"
        )
        self.user_2 = User.objects.create_user(
            username="medico2", email="medico2@test.com", password="pass1234"
        )
        self.especialidad = Especialidad.objects.create(nombre="Neurologia")

    def test_serializer_valid_data(self):
        serializer = PersonalSaludSerializer(
            data={
                "user_id": self.user_1.id,
                "item_min_salud": "MED-123",
                "rol": "medico",
                "especialidad": self.especialidad.id,
                "telefono": "76543210",
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_serializer_invalid_data(self):
        serializer = PersonalSaludSerializer(
            data={
                "user_id": self.user_1.id,
                "item_min_salud": "med-123",
                "rol": "medico",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("item_min_salud", serializer.errors)
        self.assertIn("especialidad", serializer.errors)

    def test_serializer_unique_constraints(self):
        PersonalSalud.objects.create(
            user=self.user_1,
            item_min_salud="ENF-999",
            rol="enfermera",
            especialidad=None,
        )
        serializer = PersonalSaludSerializer(
            data={
                "user_id": self.user_2.id,
                "item_min_salud": "ENF-999",
                "rol": "admin",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("item_min_salud", serializer.errors)

    def test_serializer_optional_fields(self):
        serializer = PersonalSaludSerializer(
            data={
                "user_id": self.user_1.id,
                "item_min_salud": "ADM-001",
                "rol": "admin",
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
