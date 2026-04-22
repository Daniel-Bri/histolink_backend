from rest_framework import generics, status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Tenant
from .serializers import TenantSerializer


class TenantListCreateView(generics.ListCreateAPIView):
    """GET /api/tenants/ — lista todos los establecimientos (solo superadmin)."""
    serializer_class = TenantSerializer
    permission_classes = (IsAdminUser,)
    queryset = Tenant.objects.all()


class TenantDetailView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/tenants/<pk>/ — detalle y edición (solo superadmin)."""
    serializer_class = TenantSerializer
    permission_classes = (IsAdminUser,)
    queryset = Tenant.objects.all()


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
        serializer = TenantSerializer(tenant)
        return Response(serializer.data)
