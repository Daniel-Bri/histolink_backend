"""
Vistas del CU9 — Emisión de Receta Médica.

Este módulo expone endpoints para:
- Crear recetas (médico).
- Dispensar recetas (farmacia).
- Anular recetas (médico creador o Admin/Director).
"""
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from GestionDeUsuarios.LoginYAutenticacion.permissions import EsFarmacia, EsMedico
from .models import Receta
from .serializers import RecetaSerializer


class RecetaViewSet(viewsets.ModelViewSet):
    """ViewSet de Receta con acciones de dispensación y anulación."""

    serializer_class = RecetaSerializer

    def get_permissions(self):
        """Define permisos por acción (RBAC)."""
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]

        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [EsMedico()]

        if self.action == 'dispensar':
            return [EsFarmacia()]

        if self.action == 'anular':
            return [permissions.IsAuthenticated()]

        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        """Devuelve recetas con sus detalles."""
        return Receta.objects.prefetch_related('detalles').order_by('-fecha_emision')

    @action(detail=True, methods=['patch'], url_path='dispensar')
    def dispensar(self, request, pk=None):
        """
        PATCH /recetas/{id}/dispensar/ — solo rol Farmacia.
        Reglas:
        - Solo se pueden dispensar recetas en estado EMITIDA.
        - Marca dispensada_por y fecha_dispensacion.
        """
        receta = self.get_object()

        if not (
            request.user.is_superuser
            or request.user.groups.filter(name='Farmacia').exists()
        ):
            return Response(
                {'error': 'Solo el rol Farmacia puede dispensar recetas.'},
                status=status.HTTP_403_FORBIDDEN,
            )

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
        """
        PATCH /recetas/{id}/anular/

        Reglas:
        - No se puede anular una receta DISPENSADA.
        - Puede anular: médico creador, Admin/Director o superuser.
        """
        receta = self.get_object()

        if not (
            request.user.is_superuser
            or request.user.groups.filter(name__in=['Administrativo', 'Director']).exists()
            or (
                request.user.groups.filter(name='Médico').exists()
                and receta.medico_id == request.user.id
            )
        ):
            return Response(
                {
                    'error': (
                        'Solo el médico creador (o Admin/Director) puede anular '
                        'la receta.'
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if receta.estado == 'DISPENSADA':
            return Response(
                {'error': 'No se puede anular una receta ya dispensada.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        receta.estado = 'ANULADA'
        receta.save(update_fields=['estado'])
        return Response(RecetaSerializer(receta, context={'request': request}).data)
