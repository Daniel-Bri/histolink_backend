from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import EspecialidadViewSet, PersonalSaludViewSet

app_name = "GestionDePersonalDeSalud"

router = DefaultRouter()
router.register(r"", PersonalSaludViewSet, basename="personal-salud")

especialidad_router = DefaultRouter()
especialidad_router.register(r"", EspecialidadViewSet, basename="especialidad")

urlpatterns = [
    path("", include(router.urls)),
]

especialidades_urlpatterns = [
    path("", include(especialidad_router.urls)),
]
