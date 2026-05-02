# CU9 - Emisión de Receta Médica

from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from GestionDeUsuarios.LoginYAutenticacion.permissions import EsFarmacia, EsMedico

from .models import Receta
from .serializers import RecetaSerializer


class RecetaViewSet(viewsets.ModelViewSet):
    serializer_class = RecetaSerializer

    def get_permissions(self):
        if self.action == 'dispensar':
            return [EsFarmacia()]
        if self.action in ('create', 'update', 'partial_update', 'anular'):
            return [EsMedico()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return Receta.objects.prefetch_related('detalles').order_by('-fecha_emision')

    @action(detail=True, methods=['patch'], url_path='dispensar')
    def dispensar(self, request, pk=None):
        """
        PATCH /api/clinica/recetas/{id}/dispensar/

        Marca la receta como DISPENSADA. Solo accesible para el rol Farmacia.
        La receta debe estar en estado EMITIDA; si ya fue dispensada o anulada
        devuelve 400.
        """
        receta = self.get_object()

        if receta.estado != 'EMITIDA':
            return Response(
                {
                    'error': (
                        f'Solo se pueden dispensar recetas en estado EMITIDA. '
                        f'Estado actual: {receta.estado}.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        receta.estado            = 'DISPENSADA'
        receta.dispensada_por    = request.user
        receta.fecha_dispensacion = timezone.now()
        receta.save(update_fields=['estado', 'dispensada_por', 'fecha_dispensacion'])

        return Response(
            RecetaSerializer(receta, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['patch'], url_path='anular')
    def anular(self, request, pk=None):
        """PATCH /api/clinica/recetas/{id}/anular/ — solo Médico."""
        receta = self.get_object()

        if receta.estado == 'DISPENSADA':
            return Response(
                {'error': 'No se puede anular una receta ya dispensada.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        receta.estado = 'ANULADA'
        receta.save(update_fields=['estado'])

        return Response(
            RecetaSerializer(receta, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )