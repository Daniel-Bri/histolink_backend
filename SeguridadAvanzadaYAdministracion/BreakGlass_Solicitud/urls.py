from django.urls import path

from .views import (
    BreakGlassMisSolicitudesView,
    BreakGlassPendientesView,
    BreakGlassSolicitarView,
)

app_name = "BreakGlass_Solicitud"

urlpatterns = [
    path("solicitar/", BreakGlassSolicitarView.as_view(), name="breakglass-solicitar"),
    path("mis-solicitudes/", BreakGlassMisSolicitudesView.as_view(), name="breakglass-mis-solicitudes"),
    path("pendientes/", BreakGlassPendientesView.as_view(), name="breakglass-pendientes"),
]
