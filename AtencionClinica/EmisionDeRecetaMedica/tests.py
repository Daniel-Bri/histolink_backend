
# CU9 — Tests para PATCH /api/clinica/recetas/{id}/dispensar/
# T011: solo rol Farmacia puede dispensar

from datetime import date

from django.contrib.auth.models import Group, User
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from AtencionClinica.ConsultaMedicaSOAP.models import Consulta
from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente

from .models import DetalleReceta, Receta


# ── Helpers ──────────────────────────────────────────────────────────────────

def _crear_usuario(username, grupo_nombre):
    grupo, _ = Group.objects.get_or_create(name=grupo_nombre)
    user = User.objects.create_user(username=username, password='testpass123')
    user.groups.add(grupo)
    return user


def _crear_receta(consulta, medico, estado='EMITIDA', numero=None):
    receta = Receta.objects.create(
        consulta=consulta,
        medico=medico,
        numero_receta=numero or f'REC-TEST-{Receta.objects.count():05d}',
        estado=estado,
    )
    DetalleReceta.objects.create(
        receta=receta,
        medicamento='Amoxicilina',
        concentracion='500mg',
        forma_farmaceutica='Tableta',
        dosis='1 tableta',
        frecuencia='cada 8 horas',
        duracion='7 días',
    )
    return receta


# ── Fixture base ─────────────────────────────────────────────────────────────

class RecetaTestBase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_farmacia  = _crear_usuario('farmacia_test',  'Farmacia')
        cls.user_medico    = _crear_usuario('medico_test',    'Médico')
        cls.user_enfermera = _crear_usuario('enfermera_test', 'Enfermera')
        cls.user_sin_rol   = User.objects.create_user(username='sinrol_test', password='pass')

        cls.paciente = Paciente.objects.create(
            ci='9990001',
            nombres='Paciente',
            apellido_paterno='Test',
            fecha_nacimiento=date(1990, 1, 1),
            sexo='M',
        )
        cls.consulta = Consulta.objects.create(
            paciente=cls.paciente,
            medico=cls.user_medico,
            motivo_consulta='Dolor de cabeza',
            historia_enfermedad_actual='Cefalea de 2 días de evolución.',
            impresion_diagnostica='Cefalea tensional',
            codigo_cie10_principal='G44.2',
        )


# ── Tests del endpoint dispensar ─────────────────────────────────────────────

class DispensarRecetaTests(RecetaTestBase):
    """PATCH /api/clinica/recetas/{id}/dispensar/"""

    def setUp(self):
        self.receta = _crear_receta(self.consulta, self.user_medico)
        self.url = reverse('EmisionDeRecetaMedica:receta-dispensar', args=[self.receta.id])

    # ── Caso exitoso ─────────────────────────────────────────────────────────

    def test_farmacia_dispensa_receta_emitida_ok(self):
        self.client.force_authenticate(user=self.user_farmacia)
        response = self.client.patch(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.receta.refresh_from_db()
        self.assertEqual(self.receta.estado, 'DISPENSADA')

    def test_dispensa_asigna_dispensada_por(self):
        self.client.force_authenticate(user=self.user_farmacia)
        self.client.patch(self.url)

        self.receta.refresh_from_db()
        self.assertEqual(self.receta.dispensada_por_id, self.user_farmacia.id)

    def test_dispensa_registra_timestamp(self):
        self.client.force_authenticate(user=self.user_farmacia)
        antes = timezone.now()
        self.client.patch(self.url)
        despues = timezone.now()

        self.receta.refresh_from_db()
        self.assertIsNotNone(self.receta.fecha_dispensacion)
        self.assertGreaterEqual(self.receta.fecha_dispensacion, antes)
        self.assertLessEqual(self.receta.fecha_dispensacion, despues)

    def test_respuesta_incluye_estado_y_numero_receta(self):
        self.client.force_authenticate(user=self.user_farmacia)
        response = self.client.patch(self.url)

        self.assertIn('estado', response.data)
        self.assertEqual(response.data['estado'], 'DISPENSADA')
        self.assertIn('numero_receta', response.data)
        self.assertIn('fecha_dispensacion', response.data)

    # ── Control de acceso ─────────────────────────────────────────────────────

    def test_sin_autenticacion_devuelve_401(self):
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_rol_medico_devuelve_403(self):
        self.client.force_authenticate(user=self.user_medico)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_rol_enfermera_devuelve_403(self):
        self.client.force_authenticate(user=self.user_enfermera)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_usuario_sin_rol_devuelve_403(self):
        self.client.force_authenticate(user=self.user_sin_rol)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ── Reglas de negocio ─────────────────────────────────────────────────────

    def test_dispensar_receta_ya_dispensada_devuelve_400(self):
        self.receta.estado            = 'DISPENSADA'
        self.receta.dispensada_por    = self.user_farmacia
        self.receta.fecha_dispensacion = timezone.now()
        self.receta.save()

        self.client.force_authenticate(user=self.user_farmacia)
        response = self.client.patch(self.url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_dispensar_receta_anulada_devuelve_400(self):
        self.receta.estado = 'ANULADA'
        self.receta.save()

        self.client.force_authenticate(user=self.user_farmacia)
        response = self.client.patch(self.url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_dispensar_receta_inexistente_devuelve_404(self):
        self.client.force_authenticate(user=self.user_farmacia)
        url = reverse('EmisionDeRecetaMedica:receta-dispensar', args=[99999])
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_estado_no_cambia_si_receta_anulada(self):
        self.receta.estado = 'ANULADA'
        self.receta.save()

        self.client.force_authenticate(user=self.user_farmacia)
        self.client.patch(self.url)

        self.receta.refresh_from_db()
        self.assertEqual(self.receta.estado, 'ANULADA')  # no cambió

    def test_mensaje_error_indica_estado_actual(self):
        self.receta.estado = 'DISPENSADA'
        self.receta.dispensada_por = self.user_farmacia
        self.receta.fecha_dispensacion = timezone.now()
        self.receta.save()

        self.client.force_authenticate(user=self.user_farmacia)
        response = self.client.patch(self.url)

        self.assertIn('DISPENSADA', response.data['error'])


# ── Tests del permiso EsFarmacia ─────────────────────────────────────────────

class EsFarmaciaPermissionTests(RecetaTestBase):
    """Verifica que EsFarmacia bloquea correctamente todos los otros roles."""

    def _dispensar_como(self, user):
        receta = _crear_receta(self.consulta, self.user_medico)
        url = reverse('EmisionDeRecetaMedica:receta-dispensar', args=[receta.id])
        self.client.force_authenticate(user=user)
        return self.client.patch(url)

    def test_solo_farmacia_puede_dispensar(self):
        self.assertEqual(
            self._dispensar_como(self.user_farmacia).status_code,
            status.HTTP_200_OK,
        )

    def test_medico_no_puede_dispensar(self):
        self.assertEqual(
            self._dispensar_como(self.user_medico).status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_enfermera_no_puede_dispensar(self):
        self.assertEqual(
            self._dispensar_como(self.user_enfermera).status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_usuario_sin_grupo_no_puede_dispensar(self):
        self.assertEqual(
            self._dispensar_como(self.user_sin_rol).status_code,
            status.HTTP_403_FORBIDDEN,
        )

"""
Tests unitarios del CU9 — Emisión de Receta Médica.

Cobertura principal:
- Creación de receta asociada a una consulta.
- Transición EMITIDA → DISPENSADA (solo Farmacia).
- Transición EMITIDA → ANULADA (solo médico creador).
- Transición inválida DISPENSADA → ANULADA (debe fallar).
"""
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
