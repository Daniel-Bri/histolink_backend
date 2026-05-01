"""
Tests unitarios del CU8 — Consulta Médica SOAP.

Cobertura principal:
- RBAC: Médico puede crear; Enfermera no puede crear.
- Validación de formato CIE-10.
- Transición BORRADOR → COMPLETADA mediante endpoint /completar/.
- Restricciones de edición (solo creador y solo en BORRADOR).
"""

from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from rest_framework import serializers
from rest_framework import status
from rest_framework.test import APIClient

from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente
from .models import Consulta
from .serializers import ConsultaSerializer


class ConsultaSoapTests(TestCase):
    """Suite de tests para endpoints y validaciones de Consulta SOAP."""

    def setUp(self):
        User = get_user_model()

        self.grupo_medico, _ = Group.objects.get_or_create(name='Médico')
        self.grupo_enfermera, _ = Group.objects.get_or_create(name='Enfermera')

        self.user_medico_1 = User.objects.create_user(
            username='medico1',
            password='test123',
        )
        self.user_medico_1.groups.add(self.grupo_medico)

        self.user_medico_2 = User.objects.create_user(
            username='medico2',
            password='test123',
        )
        self.user_medico_2.groups.add(self.grupo_medico)

        self.user_enfermera = User.objects.create_user(
            username='enfermera',
            password='test123',
        )
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

        self.client = APIClient()
        self.base_url = '/api/consultas/consultas/'

    def _crear_consulta_api(self, user, cie10='J15'):
        """Helper: crea una consulta SOAP vía API con payload mínimo funcional."""
        self.client.force_authenticate(user=user)
        payload = {
            'paciente': self.paciente.id,
            'motivo_consulta': 'Dolor abdominal',
            'historia_enfermedad_actual': 'Inicia hace 3 días',
            'impresion_diagnostica': 'Probable gastritis',
            'codigo_cie10_principal': cie10,
            'examen_fisico': 'Sin signos de alarma',
            'plan_tratamiento': 'Hidratación',
        }
        return self.client.post(self.base_url, payload, format='json')

    def test_es_medico_puede_crear_consulta(self):
        """Un usuario del grupo 'Médico' puede crear una consulta (BORRADOR)."""
        res = self._crear_consulta_api(self.user_medico_1, cie10='I10')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['estado'], 'BORRADOR')
        self.assertEqual(res.data['medico'], self.user_medico_1.id)

    def test_es_enfermera_no_puede_crear_consulta(self):
        """Un usuario del grupo 'Enfermera' no puede crear consultas SOAP."""
        res = self._crear_consulta_api(self.user_enfermera, cie10='I10')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_cie10_formato_valido(self):
        """CIE-10 válido (ej: E11.9) debe permitir creación."""
        self.client.force_authenticate(user=self.user_medico_1)
        payload = {
            'paciente': self.paciente.id,
            'motivo_consulta': 'Motivo',
            'historia_enfermedad_actual': 'Historia',
            'impresion_diagnostica': 'Dx',
            'codigo_cie10_principal': 'E11.9',
        }
        res = self.client.post(self.base_url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_cie10_formato_invalido_falla(self):
        """CIE-10 inválido (ej: J-15) debe retornar 400."""
        res = self._crear_consulta_api(self.user_medico_1, cie10='J-15')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_transicion_borrador_a_completada_via_completar(self):
        """PATCH /completar/ debe pasar BORRADOR → COMPLETADA."""
        res = self._crear_consulta_api(self.user_medico_1)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        consulta_id = res.data['id']
        completar_url = f'{self.base_url}{consulta_id}/completar/'
        res2 = self.client.patch(completar_url, {}, format='json')

        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.data['estado'], 'COMPLETADA')

    def test_no_permire_editar_despues_de_completada(self):
        """Después de COMPLETADA, no debe permitirse edición (403)."""
        res = self._crear_consulta_api(self.user_medico_1)
        consulta_id = res.data['id']
        completar_url = f'{self.base_url}{consulta_id}/completar/'
        self.client.patch(completar_url, {}, format='json')

        patch_url = f'{self.base_url}{consulta_id}/'
        res3 = self.client.patch(patch_url, {'motivo_consulta': 'Cambio'}, format='json')
        self.assertEqual(res3.status_code, status.HTTP_403_FORBIDDEN)

    def test_otro_medico_no_puede_editar(self):
        """Otro médico distinto al creador no debe poder editar (403 o 404)."""
        res = self._crear_consulta_api(self.user_medico_1)
        consulta_id = res.data['id']

        self.client.force_authenticate(user=self.user_medico_2)
        patch_url = f'{self.base_url}{consulta_id}/'
        res2 = self.client.patch(patch_url, {'motivo_consulta': 'Cambio'}, format='json')
        self.assertIn(res2.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_no_se_puede_modificar_una_consulta_firmada(self):
        """Una consulta en estado FIRMADA no debe permitir modificaciones."""
        consulta = Consulta.objects.create(
            paciente=self.paciente,
            medico=self.user_medico_1,
            motivo_consulta='Motivo',
            historia_enfermedad_actual='Historia',
            impresion_diagnostica='Dx',
            codigo_cie10_principal='J15',
            estado='FIRMADA',
        )
        self.client.force_authenticate(user=self.user_medico_1)
        patch_url = f'{self.base_url}{consulta.id}/'
        res = self.client.patch(patch_url, {'motivo_consulta': 'Cambio'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_validacion_transicion_estado_invalida_unitaria(self):
        """El serializer debe rechazar transiciones inválidas (COMPLETADA → BORRADOR)."""
        consulta = Consulta(
            paciente=self.paciente,
            medico=self.user_medico_1,
            motivo_consulta='Motivo',
            historia_enfermedad_actual='Historia',
            impresion_diagnostica='Dx',
            codigo_cie10_principal='J15',
            estado='COMPLETADA',
        )
        serializer = ConsultaSerializer(instance=consulta)
        with self.assertRaisesMessage(
            serializers.ValidationError,
            'Transición de estado inválida',
        ):
            serializer.validate_estado('BORRADOR')
