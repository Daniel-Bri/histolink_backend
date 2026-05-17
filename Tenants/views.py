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


class UsuariosPorClinicaView(APIView):
    """
    GET /api/tenants/usuarios/
    Retorna todos los usuarios (PersonalSalud) agrupados por clínica/tenant.
    Solo superadmin (is_staff).
    """
    permission_classes = (IsAdminUser,)

    def get(self, request):
        from GestionDeUsuarios.GestionDePersonalDeSalud.models import PersonalSalud

        personal_qs = (
            PersonalSalud.objects
            .select_related('user', 'especialidad', 'tenant')
            .order_by('tenant__nombre', 'rol', 'user__last_name')
        )

        # Agrupar por tenant
        clinicas: dict = {}
        sin_clinica = []

        for ps in personal_qs:
            entrada = {
                'id':           ps.id,
                'user_id':      ps.user.id,
                'username':     ps.user.username,
                'nombre':       f"{ps.user.first_name} {ps.user.last_name}".strip() or ps.user.username,
                'email':        ps.user.email,
                'rol':          ps.rol,
                'especialidad': ps.especialidad.nombre if ps.especialidad else None,
                'item_min_salud': ps.item_min_salud,
                'activo':       ps.is_active,
            }
            if ps.tenant:
                tid = ps.tenant.id
                if tid not in clinicas:
                    clinicas[tid] = {
                        'tenant_id':     ps.tenant.id,
                        'tenant_nombre': ps.tenant.nombre,
                        'tenant_activo': ps.tenant.activo,
                        'usuarios':      [],
                    }
                clinicas[tid]['usuarios'].append(entrada)
            else:
                sin_clinica.append(entrada)

        resultado = list(clinicas.values())
        if sin_clinica:
            resultado.append({
                'tenant_id':     None,
                'tenant_nombre': 'Sin clínica asignada',
                'tenant_activo': None,
                'usuarios':      sin_clinica,
            })

        return Response(resultado)


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
