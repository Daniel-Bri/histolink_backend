from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Tenant
from .serializers import (
    ConfiguracionTenantSerializer,
    TenantConConfigSerializer,
    TenantSerializer,
)


class TenantListCreateView(generics.ListCreateAPIView):
    """GET /api/tenants/ — lista todos los establecimientos (solo superadmin)."""
    serializer_class   = TenantSerializer
    permission_classes = (IsAdminUser,)
    queryset           = Tenant.objects.all()


class TenantDetailView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/tenants/<pk>/ — detalle y edición (solo superadmin)."""
    serializer_class   = TenantSerializer
    permission_classes = (IsAdminUser,)
    queryset           = Tenant.objects.all()


class TenantConfigAdminView(APIView):
    """
    GET  /api/tenants/<pk>/configuracion/ — lee config de cualquier tenant.
    PATCH /api/tenants/<pk>/configuracion/ — edita config (solo superadmin).
    """
    permission_classes = (IsAdminUser,)

    def _get_config(self, pk):
        tenant = get_object_or_404(Tenant, pk=pk)
        return tenant.get_configuracion()

    def get(self, request, pk):
        config = self._get_config(pk)
        return Response(ConfiguracionTenantSerializer(config).data)

    def patch(self, request, pk):
        config = self._get_config(pk)
        ser = ConfiguracionTenantSerializer(config, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)


class TenantToggleActivoView(APIView):
    """POST /api/tenants/<pk>/toggle-activo/ — activa o desactiva un tenant."""
    permission_classes = (IsAdminUser,)

    def post(self, request, pk):
        tenant = get_object_or_404(Tenant, pk=pk)
        tenant.activo = not tenant.activo
        tenant.save(update_fields=['activo', 'actualizado_en'])
        return Response(TenantSerializer(tenant).data)


class MiTenantView(APIView):
    """GET /api/tenants/mi-tenant/ — devuelve el establecimiento del usuario autenticado."""
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        tenant = request.tenant
        if not tenant:
            return Response(
                {"detail": "Este usuario no está asociado a ningún establecimiento."},
                status=status.HTTP_404_NOT_FOUND,
            )
        tenant.get_configuracion()  # asegura que existe ConfiguracionTenant
        serializer = TenantConConfigSerializer(tenant)
        return Response(serializer.data)


class ConfiguracionTenantView(APIView):
    """
    GET  /api/tenants/mi-tenant/configuracion/ — lee config del tenant del usuario.
    PATCH /api/tenants/mi-tenant/configuracion/ — edita config (Director/Administrativo).
    """
    permission_classes = (IsAuthenticated,)

    _roles_permitidos = frozenset({'Director', 'Administrativo'})

    def _check_perms(self, user):
        if user.is_staff:
            return True
        groups = set(user.groups.values_list('name', flat=True))
        return bool(groups & self._roles_permitidos)

    def get(self, request):
        tenant = request.tenant
        if not tenant:
            return Response({"detail": "Sin establecimiento."}, status=status.HTTP_404_NOT_FOUND)
        config = tenant.get_configuracion()
        return Response(ConfiguracionTenantSerializer(config).data)

    def patch(self, request):
        tenant = request.tenant
        if not tenant:
            return Response({"detail": "Sin establecimiento."}, status=status.HTTP_404_NOT_FOUND)
        if not self._check_perms(request.user):
            return Response({"detail": "Solo Director o Administrativo pueden editar la configuración."}, status=status.HTTP_403_FORBIDDEN)

        config = tenant.get_configuracion()
        ser    = ConfiguracionTenantSerializer(config, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)
