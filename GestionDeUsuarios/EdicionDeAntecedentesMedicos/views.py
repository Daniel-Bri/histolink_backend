# CU5 - Edición de Antecedentes Médicos

import json
import logging

from django.core.cache import caches
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente
from .models import Antecedente
from .serializers import AntecedenteSerializer, AntecedenteUpdateSerializer

logger = logging.getLogger("histolink.antecedentes")

# Alias definido en settings.CACHES — apunta a Redis DB1
_cache = caches["antecedentes"]

# TTL de 15 minutos para datos de antecedentes
CACHE_TTL = 60 * 15


def _cache_key(paciente_id: int) -> str:
    return f"antecedente:paciente:{paciente_id}"


class AntecedenteView(APIView):
    """
    GET  /api/pacientes/{paciente_id}/antecedentes/
        Devuelve el antecedente del paciente.
        Respuesta cacheada en Redis DB1 durante 15 minutos.
        Si el paciente no tiene antecedente aún, crea uno vacío.

    PATCH /api/pacientes/{paciente_id}/antecedentes/
        Actualización parcial del antecedente.
        Solo se modifican los campos incluidos en el body.
        Invalida la entrada de caché tras guardar.
    """

    permission_classes = (IsAuthenticated,)

    # ── GET ──────────────────────────────────────────────────────────────

    def get(self, request, paciente_id):
        cache_key = _cache_key(paciente_id)
        cached = _cache.get(cache_key)

        if cached is not None:
            logger.debug("Cache HIT antecedente paciente_id=%s", paciente_id)
            return Response(json.loads(cached), status=status.HTTP_200_OK)

        logger.debug("Cache MISS antecedente paciente_id=%s", paciente_id)

        try:
            paciente = Paciente.objects.get(pk=paciente_id)
        except Paciente.DoesNotExist:
            return Response(
                {"error": "Paciente no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        antecedente, _ = Antecedente.objects.get_or_create(paciente=paciente)
        data = AntecedenteSerializer(antecedente).data

        _cache.set(cache_key, json.dumps(data), timeout=CACHE_TTL)

        return Response(data, status=status.HTTP_200_OK)

    # ── PATCH ─────────────────────────────────────────────────────────────

    def patch(self, request, paciente_id):
        try:
            paciente = Paciente.objects.get(pk=paciente_id)
        except Paciente.DoesNotExist:
            return Response(
                {"error": "Paciente no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        antecedente, _ = Antecedente.objects.get_or_create(paciente=paciente)

        serializer = AntecedenteUpdateSerializer(
            antecedente,
            data=request.data,
            partial=True,
            context={"request": request},
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        antecedente = serializer.save()

        # Invalidar caché tras escritura
        cache_key = _cache_key(paciente_id)
        _cache.delete(cache_key)
        logger.debug("Cache invalidado antecedente paciente_id=%s", paciente_id)

        return Response(
            AntecedenteSerializer(antecedente).data,
            status=status.HTTP_200_OK,
        )
