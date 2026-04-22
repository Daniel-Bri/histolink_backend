from django.urls import path
from .views import TenantListCreateView, TenantDetailView, MiTenantView

urlpatterns = [
    path('', TenantListCreateView.as_view(), name='tenant-list'),
    path('mi-tenant/', MiTenantView.as_view(), name='mi-tenant'),
    path('<int:pk>/', TenantDetailView.as_view(), name='tenant-detail'),
]
