"""
Tests unitarios del CU9 — Emisión de Receta Médica.

Cobertura principal:
- Creación de receta asociada a una consulta.
- Transición EMITIDA → DISPENSADA (solo Farmacia).
- Transición EMITIDA → ANULADA (solo médico creador).
- Transición inválida DISPENSADA → ANULADA (debe fallar).
"""

from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from AtencionClinica.ConsultaMedicaSOAP.models import Consulta
from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente
from .models import Receta


class RecetaTests(TestCase):
    """Suite de tests para permisos y transiciones de estado de Receta."""

    def setUp(self):
        User = get_user_model()

        self.grupo_medico, _ = Group.objects.get_or_create(name='Médico')
        self.grupo_farmacia, _ = Group.objects.get_or_create(name='Farmacia')

        self.user_medico = User.objects.create_user(
            username='medico',
            password='test123',
        )
        self.user_medico.groups.add(self.grupo_medico)

        self.user_farmacia = User.objects.create_user(
            username='farmacia',
            password='test123',
        )
        self.user_farmacia.groups.add(self.grupo_farmacia)

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

        self.consulta = Consulta.objects.create(
            paciente=self.paciente,
            medico=self.user_medico,
            motivo_consulta='Motivo',
            historia_enfermedad_actual='Historia',
            impresion_diagnostica='Dx',
            codigo_cie10_principal='J15',
        )

        self.client = APIClient()
        self.base_url = '/api/clinica/recetas/'

    def _crear_receta_api(self):
        """Helper: crea una receta con un detalle vía API."""
        self.client.force_authenticate(user=self.user_medico)
        payload = {
            'consulta': self.consulta.id,
            'observaciones': 'Tomar con agua',
            'detalles': [
                {
                    'medicamento': 'Ibuprofeno',
                    'dosis': '1 tableta',
                    'frecuencia': 'cada 8 horas',
                    'duracion': '3 días',
                }
            ],
        }
        return self.client.post(self.base_url, payload, format='json')

    def test_crear_receta_asociada_a_consulta(self):
        """Crear receta devuelve 201 y estado EMITIDA."""
        res = self._crear_receta_api()
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['consulta'], self.consulta.id)
        self.assertEqual(res.data['estado'], 'EMITIDA')
        self.assertEqual(len(res.data['detalles']), 1)

    def test_solo_farmacia_puede_dispensar(self):
        """Médico no puede dispensar; Farmacia sí puede dispensar."""
        res = self._crear_receta_api()
        receta_id = res.data['id']
        url = f'{self.base_url}{receta_id}/dispensar/'

        self.client.force_authenticate(user=self.user_medico)
        res2 = self.client.patch(url, {}, format='json')
        self.assertEqual(res2.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.user_farmacia)
        res3 = self.client.patch(url, {}, format='json')
        self.assertEqual(res3.status_code, status.HTTP_200_OK)
        self.assertEqual(res3.data['estado'], 'DISPENSADA')

    def test_medico_creador_puede_anular_receta_emitida(self):
        """El médico creador puede anular una receta EMITIDA."""
        res = self._crear_receta_api()
        receta_id = res.data['id']
        url = f'{self.base_url}{receta_id}/anular/'

        self.client.force_authenticate(user=self.user_medico)
        res2 = self.client.patch(url, {}, format='json')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.data['estado'], 'ANULADA')

    def test_no_se_puede_anular_una_receta_dispensada(self):
        """Una receta DISPENSADA no debe permitir anulación (400)."""
        res = self._crear_receta_api()
        receta_id = res.data['id']
        dispensar_url = f'{self.base_url}{receta_id}/dispensar/'

        self.client.force_authenticate(user=self.user_farmacia)
        self.client.patch(dispensar_url, {}, format='json')

        anular_url = f'{self.base_url}{receta_id}/anular/'
        self.client.force_authenticate(user=self.user_medico)
        res2 = self.client.patch(anular_url, {}, format='json')
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_farmacia_no_puede_anular(self):
        """Farmacia no debe poder anular (403)."""
        res = self._crear_receta_api()
        receta_id = res.data['id']
        anular_url = f'{self.base_url}{receta_id}/anular/'

        self.client.force_authenticate(user=self.user_farmacia)
        res2 = self.client.patch(anular_url, {}, format='json')
        self.assertEqual(res2.status_code, status.HTTP_403_FORBIDDEN)

    def test_restriccion_estado_emitida_en_modelo(self):
        """Por defecto, el modelo Receta inicia en estado EMITIDA."""
        receta = Receta.objects.create(
            consulta=self.consulta,
            medico=self.user_medico,
            numero_receta='REC-2026-99999',
        )
        self.assertEqual(receta.estado, 'EMITIDA')
