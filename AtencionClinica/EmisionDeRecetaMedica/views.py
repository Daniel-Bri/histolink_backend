# CU9 - Emisión de Receta Médica

from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Receta
from .serializers import RecetaSerializer


class RecetaViewSet(viewsets.ModelViewSet):
    serializer_class = RecetaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Receta.objects.prefetch_related('detalles').order_by('-fecha_emision')

    @action(detail=True, methods=['patch'], url_path='dispensar')
    def dispensar(self, request, pk=None):
        """PATCH /recetas/{id}/dispensar/ — solo rol Farmacia."""
        receta = self.get_object()

        if receta.estado != 'EMITIDA':
            return Response(
                {'error': f'Solo se pueden dispensar recetas EMITIDAS. Estado actual: {receta.estado}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        receta.estado = 'DISPENSADA'
        receta.dispensada_por = request.user
        receta.fecha_dispensacion = timezone.now()
        receta.save()

        return Response(RecetaSerializer(receta, context={'request': request}).data)

    @action(detail=True, methods=['patch'], url_path='anular')
    def anular(self, request, pk=None):
        """PATCH /recetas/{id}/anular/"""
        receta = self.get_object()

        if receta.estado == 'DISPENSADA':
            return Response(
                {'error': 'No se puede anular una receta ya dispensada.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        receta.estado = 'ANULADA'
        receta.save()

        return Response(RecetaSerializer(receta, context={'request': request}).data)