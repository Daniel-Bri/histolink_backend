from django.urls import path
from .views import (
    ConfiguracionTenantView,
    MiTenantView,
    TenantConfigAdminView,
    TenantDetailView,
    TenantListCreateView,
    TenantToggleActivoView,
    UsuariosPorClinicaView,
)

urlpatterns = [
    path('',                                  TenantListCreateView.as_view(),  name='tenant-list'),
    path('usuarios/',                         UsuariosPorClinicaView.as_view(), name='usuarios-por-clinica'),
    path('mi-tenant/',                        MiTenantView.as_view(),          name='mi-tenant'),
    path('mi-tenant/configuracion/',          ConfiguracionTenantView.as_view(), name='configuracion-tenant'),
    path('<int:pk>/',                         TenantDetailView.as_view(),      name='tenant-detail'),
    path('<int:pk>/configuracion/',           TenantConfigAdminView.as_view(), name='tenant-config-admin'),
    path('<int:pk>/toggle-activo/',           TenantToggleActivoView.as_view(), name='tenant-toggle-activo'),
]
