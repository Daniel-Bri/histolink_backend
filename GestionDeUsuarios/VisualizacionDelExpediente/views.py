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
            paciente = (
                Paciente.objects
                .prefetch_related(
                    "antecedentes",
                    # Triajes y su enfermera
                    "triajes",
                    "triajes__enfermera",
                    # Consultas y su médico
                    "consultas",
                    "consultas__medico",
                    "consultas__triaje",
                    # Recetas dentro de cada consulta
                    "consultas__recetas",
                    "consultas__recetas__medico",
                    "consultas__recetas__detalles",
                    # Órdenes de estudio dentro de cada consulta
                    "consultas__ordenes",
                    "consultas__ordenes__medico_solicitante",
                    "consultas__ordenes__resultado",
                    "consultas__ordenes__resultado__ingresado_por",
                )
                .get(pk=id)
            )
        except Paciente.DoesNotExist:
            return Response(
                {"error": "Paciente no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ExpedienteSerializer(paciente)
        return Response(serializer.data, status=status.HTTP_200_OK)
