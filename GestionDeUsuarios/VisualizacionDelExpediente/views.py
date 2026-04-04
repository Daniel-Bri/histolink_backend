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

    Retorna el expediente clínico completo de un paciente:
    datos personales, antecedentes médicos, triajes, consultas SOAP,
    recetas y estudios solicitados.

    Requiere autenticación JWT (Bearer token).

    Path params:
        id (int) — ID del paciente.

    Response 200:
        {
            "id": ...,
            "ci": "...",
            "nombre": "...",
            "apellido": "...",
            "fecha_nacimiento": "...",
            "sexo": "M",
            "sexo_label": "Masculino",
            "tipo_sangre": "O+",
            "telefono": "...",
            "email": "...",
            "direccion": "...",
            "fecha_registro": "...",
            "activo": true,
            "antecedentes": { ... },
            "triajes": [ ... ],
            "consultas": [ ... ],
            "recetas": [ ... ],
            "estudios": [ ... ]
        }

    Response 404:
        { "error": "Paciente no encontrado." }
    """

    permission_classes = (IsAuthenticated,)

    def get(self, request, id):
        try:
            paciente = (
                Paciente.objects
                .prefetch_related(
                    "antecedentes",
                    "triajes",
                    "triajes__enfermera",
                    "consultas",
                    "consultas__medico",
                    "consultas__recetas",
                    "consultas__recetas__items",
                    "consultas__estudios",
                    "recetas",
                    "recetas__items",
                    "recetas__medico",
                    "estudios",
                    "estudios__solicitante",
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
