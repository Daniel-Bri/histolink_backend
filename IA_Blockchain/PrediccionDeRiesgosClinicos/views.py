import logging
from django.utils import timezone
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente
from ml.servicio_ml import ServicioML
from .serializers import PrediccionRiesgosResponseSerializer

logger = logging.getLogger(__name__)

class PrediccionRiesgosView(APIView):
    """
    T004: Endpoint para consulta de riesgos clínicos con IA.
    Recibe paciente_id y tipo (opcional) por query params.
    No persiste datos en base de datos para evitar dependencias de migración.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # 1. Obtener parámetros de Query Params
        paciente_id = request.query_params.get('paciente_id')
        tipo_filtro = request.query_params.get('tipo')

        if not paciente_id:
            return Response(
                {"error": "Debe proporcionar el 'paciente_id' como parámetro de consulta."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Aislamiento Multi-Tenant con bypass para administradores
        if request.user.is_superuser or not request.tenant:
            paciente = Paciente.objects.filter(pk=paciente_id).first()
        else:
            paciente = Paciente.objects.filter(
                pk=paciente_id, 
                tenant=request.tenant
            ).first()

        if not paciente:
            return Response(
                {"error": "El expediente del paciente solicitado no existe o no está disponible para su perfil."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 3. Gestión de Caché Redis (24 horas)
        tenant_id = request.tenant.id if request.tenant else 0
        cache_key = f"riesgos_paciente:{tenant_id}:{paciente_id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            tenant_id_log = request.tenant.id if request.tenant else "Global/Admin"
            logger.info(f"Caché HIT para paciente {paciente_id} en tenant {tenant_id_log}")
            
            # Aplicar filtro de tipo si se solicitó
            if tipo_filtro:
                if tipo_filtro in cached_data:
                    return Response({tipo_filtro: cached_data[tipo_filtro]}, status=status.HTTP_200_OK)
                return Response(
                    {"error": f"El tipo de riesgo '{tipo_filtro}' no es válido."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(cached_data, status=status.HTTP_200_OK)

        # 4. Cálculo mediante ServicioML (Delegación estricta)
        try:
            servicio = ServicioML.obtener_instancia()
            riesgos = servicio.predecir_todos_los_riesgos(paciente_id)
            
            # Preparar respuesta
            response_data = {
                **riesgos,
                "paciente_id": int(paciente_id),
                "fecha_calculo": timezone.now()
            }

            # Validar con serializer
            serializer = PrediccionRiesgosResponseSerializer(response_data)
            data_final = serializer.data

            # 5. Guardar en Caché Redis por 24 horas (86400 seg)
            cache.set(cache_key, data_final, timeout=86400)
            logger.info(f"Caché MISS - Riesgos calculados y guardados para paciente {paciente_id}")

            # Filtrar respuesta si se solicitó un tipo específico
            if tipo_filtro:
                if tipo_filtro in data_final:
                    return Response({tipo_filtro: data_final[tipo_filtro]}, status=status.HTTP_200_OK)
                return Response(
                    {"error": f"El tipo de riesgo '{tipo_filtro}' no es válido."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(data_final, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error procesando riesgos para paciente {paciente_id}: {str(e)}")
            return Response(
                {"error": "No se pudo completar el análisis de riesgo en este momento. Intente más tarde."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
