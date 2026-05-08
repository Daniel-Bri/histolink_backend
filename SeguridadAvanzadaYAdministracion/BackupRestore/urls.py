from django.urls import path
from .views import (
    BackupCompletoView,
    ExportarTenantView,
    GestionAnualViewSet,
    RestoreView,
)

_gestiones = GestionAnualViewSet.as_view({
    'get':  'list',
    'post': 'create',
})
_gestion_congelar    = GestionAnualViewSet.as_view({'post': 'congelar'})
_gestion_descongelar = GestionAnualViewSet.as_view({'post': 'descongelar'})

urlpatterns = [
    path('exportar-tenant/', ExportarTenantView.as_view(),  name='backup-exportar-tenant'),
    path('completo/',        BackupCompletoView.as_view(),  name='backup-completo'),
    path('restore/',         RestoreView.as_view(),         name='backup-restore'),
    path('gestiones/',                         _gestiones,             name='gestion-list'),
    path('gestiones/<int:pk>/congelar/',       _gestion_congelar,      name='gestion-congelar'),
    path('gestiones/<int:pk>/descongelar/',    _gestion_descongelar,   name='gestion-descongelar'),
]
