from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PermisoPaciente
from .serializers import (
    OtorgarPermisoSerializer,
    PermisoPacienteSerializer,
    RevocarPermisoSerializer,
)


class OtorgarPermisoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Permisos"],
        summary="Otorgar permiso a médico",
        description=(
            "Otorga permiso a un médico para visualizar el expediente clínico de un paciente. "
            "Si ya existe un registro activo, devuelve error. Si existe un registro inactivo, "
            "lo reactiva en lugar de crear uno nuevo."
        ),
        request=OtorgarPermisoSerializer,
        responses={
            201: PermisoPacienteSerializer,
            200: PermisoPacienteSerializer,
            400: OpenApiResponse(description="Datos inválidos o permiso ya activo."),
            401: OpenApiResponse(description="No autorizado (JWT faltante o inválido)."),
        },
    )
    def post(self, request):
        serializer = OtorgarPermisoSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        
        # Guardar/reactivar
        permiso = serializer.save()
        
        # Retornar representación
        out_serializer = PermisoPacienteSerializer(permiso)
        # Si fue reactivado, podemos retornar 200 OK, si fue recién creado 201 Created
        # Podemos verificar si fue creado o no comparando la fecha de otorgamiento aproximada o guardando estado en create,
        # pero retornamos 201 Created o 200 OK según la convención. Retornaremos 201 por defecto.
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)


class RevocarPermisoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Permisos"],
        summary="Revocar permiso de médico",
        description=(
            "Revoca el acceso de un médico al expediente de un paciente. "
            "El registro no se elimina de la base de datos, solo se desactiva y se registra la fecha."
        ),
        request=RevocarPermisoSerializer,
        responses={
            200: PermisoPacienteSerializer,
            400: OpenApiResponse(description="Datos inválidos o no existe un permiso activo."),
            401: OpenApiResponse(description="No autorizado."),
        },
    )
    def post(self, request):
        serializer = RevocarPermisoSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        permiso = serializer.save()
        
        out_serializer = PermisoPacienteSerializer(permiso)
        return Response(out_serializer.data, status=status.HTTP_200_OK)


class PermisoPacienteListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Permisos"],
        summary="Listar permisos de paciente",
        description="Devuelve todos los registros de permisos de paciente (trazabilidad de accesos) filtrados por el tenant actual.",
        responses={
            200: PermisoPacienteSerializer(many=True),
            401: OpenApiResponse(description="No autorizado."),
        },
    )
    def get(self, request):
        # TenantManager ya filtra por tenant si está en el contexto
        qs = PermisoPaciente.objects.all().select_related("paciente", "medico", "otorgado_por")
        
        # Filtros opcionales
        paciente_id = request.query_params.get("paciente_id")
        if paciente_id:
            qs = qs.filter(paciente_id=paciente_id)
            
        medico_id = request.query_params.get("medico_id")
        if medico_id:
            qs = qs.filter(medico_id=medico_id)
            
        activo = request.query_params.get("activo")
        if activo is not None:
            activo_bool = activo.lower() in ("true", "1", "yes")
            qs = qs.filter(activo=activo_bool)

        serializer = PermisoPacienteSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
