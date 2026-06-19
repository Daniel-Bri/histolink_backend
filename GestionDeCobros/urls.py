from django.urls import path
from .views import CrearSesionCobroView, AnularCobroView, webhook_cobro, ListarCobrosView

urlpatterns = [
    path("", ListarCobrosView.as_view(), name="listar-cobros"),
    path("crear-sesion/", CrearSesionCobroView.as_view(), name="crear-sesion-cobro"),
    path("<int:pk>/anular/", AnularCobroView.as_view(), name="anular-cobro"),
    path("webhook/", webhook_cobro, name="webhook-cobro"),
]