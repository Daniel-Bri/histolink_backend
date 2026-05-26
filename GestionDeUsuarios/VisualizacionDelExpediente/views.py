# CU4 - Visualización del Expediente del Paciente

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from AtencionClinica.ConsultaMedicaSOAP.models import Consulta
from AtencionClinica.RegistroDeTriaje.models import Triaje
from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente
from SeguridadAvanzadaYAdministracion.BreakGlass_Solicitud.models import BreakGlassSolicitud
from .serializers import ExpedienteSerializer


class ExpedientePacienteView(APIView):
    """
    GET /api/pacientes/{id}/expediente/

    Retorna el expediente clínico completo del paciente:
    datos personales, antecedentes, triajes, consultas SOAP
    (con sus recetas + detalles + órdenes de estudio + resultados).

    Requiere autenticación JWT (Bearer token).

    Response 200: { datos del paciente + antecedentes + triajes + consultas[] }
    Response 404: { "error": "Paciente no encontrado." }
    """

    permission_classes = (IsAuthenticated,)

    @staticmethod
    def _nombre_paciente(paciente: Paciente) -> str:
        return " ".join(
            x for x in [paciente.nombres, paciente.apellido_paterno, paciente.apellido_materno] if x
        ).strip()

    @staticmethod
    def _es_privilegiado(user) -> bool:
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.groups.filter(name__in=["Director", "Administrativo", "Auditor"]).exists()

    def _tiene_acceso_clinico(self, request, paciente: Paciente) -> bool:
        user = request.user
        if self._es_privilegiado(user):
            return True

        if user.groups.filter(name="Médico").exists():
            if paciente.creado_por_id == user.id:
                return True
            tiene_consulta = Consulta.objects.filter(
                ficha__paciente=paciente,
                medico=user,
            ).exists()
            if tiene_consulta:
                return True

        if user.groups.filter(name="Enfermera").exists():
            tiene_triaje = Triaje.objects.filter(
                ficha__paciente=paciente,
                enfermera=user,
            ).exists()
            if tiene_triaje:
                return True

        return False

    def get(self, request, id):
        try:
            paciente = Paciente.objects.prefetch_related(
                "antecedentes",
            ).get(pk=id)
        except Paciente.DoesNotExist:
            return Response(
                {"error": "Paciente no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        tenant = getattr(request, "tenant", None)
        if tenant and paciente.tenant_id and paciente.tenant_id != tenant.id:
            return Response(
                {"detail": "No tiene permisos para acceder a este expediente."},
                status=status.HTTP_403_FORBIDDEN,
            )

        tiene_acceso_base = self._tiene_acceso_clinico(request, paciente)
        if not tiene_acceso_base:
            tiene_break_glass = BreakGlassSolicitud.objects.filter(
                solicitante=request.user,
                paciente=paciente,
                acceso_desde__isnull=False,
                acceso_hasta__gt=timezone.now(),
                estado__in=[
                    BreakGlassSolicitud.Estado.PENDIENTE,
                    BreakGlassSolicitud.Estado.APROBADA,
                ],
            ).exists()
            if not tiene_break_glass:
                return Response(
                    {
                        "detail": "No tiene permisos para acceder a este expediente.",
                        "paciente_id": paciente.id,
                        "paciente_nombre": self._nombre_paciente(paciente),
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        serializer = ExpedienteSerializer(paciente)
        return Response(serializer.data, status=status.HTTP_200_OK)
