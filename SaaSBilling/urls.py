from django.urls import path
from .views import (
    ListarSuscripcionesView,
    DetalleSuscripcionView,
    CrearPagoSaaSView,
    webhook_saas,
    MiSuscripcionView,
)

urlpatterns = [
    path('suscripciones/',                              ListarSuscripcionesView.as_view(), name='saas-lista'),
    path('suscripciones/<int:tenant_id>/',              DetalleSuscripcionView.as_view(),  name='saas-detalle'),
    path('suscripciones/<int:tenant_id>/crear-pago/',   CrearPagoSaaSView.as_view(),       name='saas-crear-pago'),
    path('webhook/',                                    webhook_saas,                       name='saas-webhook'),
    path('mi-suscripcion/',                             MiSuscripcionView.as_view(),        name='saas-mi-suscripcion'),
]
