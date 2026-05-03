# CU4 - Visualización del Expediente del Paciente

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente
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

        serializer = ExpedienteSerializer(paciente)
        return Response(serializer.data, status=status.HTTP_200_OK)
