"""
Tests unitarios del CU7 — Registro de Triaje.

Se cubren casos felices y validaciones de rangos fisiológicos usando:
- Validación de modelo con ``full_clean``.
- Validación de serializer (DRF) para asignación automática de enfermera.
"""

from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente
from .models import Triaje
from .serializers import TriajeSerializer


class TriajeTests(TestCase):
    """Suite de tests para el modelo/serializer de Triaje."""

    def setUp(self):
        User = get_user_model()
        self.user_enfermera = User.objects.create_user(
            username='enfermera',
            password='test123',
        )
        self.grupo_enfermera, _ = Group.objects.get_or_create(name='Enfermera')
        self.user_enfermera.groups.add(self.grupo_enfermera)

        self.paciente = Paciente.objects.create(
            ci='12345678',
            ci_complemento='',
            nombres='Paciente',
            apellido_paterno='Test',
            apellido_materno='',
            fecha_nacimiento=date(1990, 1, 1),
            sexo='M',
            email='test@test.com',
            telefono='70000000',
        )

        self.factory = APIRequestFactory()

    def test_crear_triaje_valido_modelo(self):
        """Crea un triaje válido y verifica que el nivel de urgencia se guarda."""
        triaje = Triaje(
            paciente=self.paciente,
            enfermera=self.user_enfermera,
            frecuencia_cardiaca=80,
            saturacion_oxigeno=98,
            escala_dolor=4,
            motivo_consulta_triaje='Dolor de cabeza',
            nivel_urgencia='VERDE',
        )
        triaje.full_clean()
        triaje.save()
        self.assertEqual(triaje.nivel_urgencia, 'VERDE')

    def test_validar_rango_frecuencia_cardiaca_baja_falla(self):
        """Frecuencia cardíaca fuera de rango (baja) debe fallar en full_clean."""
        triaje = Triaje(
            paciente=self.paciente,
            enfermera=self.user_enfermera,
            frecuencia_cardiaca=10,
        )
        with self.assertRaises(ValidationError):
            triaje.full_clean()

    def test_validar_rango_frecuencia_cardiaca_alta_falla(self):
        """Frecuencia cardíaca fuera de rango (alta) debe fallar en full_clean."""
        triaje = Triaje(
            paciente=self.paciente,
            enfermera=self.user_enfermera,
            frecuencia_cardiaca=500,
        )
        with self.assertRaises(ValidationError):
            triaje.full_clean()

    def test_validar_rango_spo2_bajo_falla(self):
        """SpO2 fuera de rango (baja) debe fallar en full_clean."""
        triaje = Triaje(
            paciente=self.paciente,
            enfermera=self.user_enfermera,
            saturacion_oxigeno=40,
        )
        with self.assertRaises(ValidationError):
            triaje.full_clean()

    def test_validar_rango_spo2_alto_falla(self):
        """SpO2 fuera de rango (alta) debe fallar en full_clean."""
        triaje = Triaje(
            paciente=self.paciente,
            enfermera=self.user_enfermera,
            saturacion_oxigeno=120,
        )
        with self.assertRaises(ValidationError):
            triaje.full_clean()

    def test_validar_rango_dolor_falla(self):
        """Escala de dolor fuera de rango debe fallar en full_clean."""
        triaje = Triaje(
            paciente=self.paciente,
            enfermera=self.user_enfermera,
            escala_dolor=11,
        )
        with self.assertRaises(ValidationError):
            triaje.full_clean()

    def test_serializer_asigna_enfermera_desde_request(self):
        """El serializer debe auto-asignar enfermera desde request.user."""
        payload = {
            'paciente': self.paciente.id,
            'frecuencia_cardiaca': 75,
            'saturacion_oxigeno': 97,
            'escala_dolor': 2,
            'nivel_urgencia': 'AMARILLO',
            'motivo_consulta_triaje': 'Fiebre y tos',
        }
        request = self.factory.post('/api/triaje/', payload, format='json')
        request.user = self.user_enfermera

        serializer = TriajeSerializer(data=payload, context={'request': request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        triaje = serializer.save()

        self.assertEqual(triaje.enfermera_id, self.user_enfermera.id)
        self.assertEqual(triaje.nivel_urgencia, 'AMARILLO')
