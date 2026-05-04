from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import OrdenEstudioViewSet, ResultadoEstudioViewSet

app_name = "SolicitudDeEstudios"

router = DefaultRouter()
router.register(r"ordenes-estudio", OrdenEstudioViewSet, basename="orden-estudio")
router.register(r"resultados-estudio", ResultadoEstudioViewSet, basename="resultado-estudio")

urlpatterns = [
    path("", include(router.urls)),
]
