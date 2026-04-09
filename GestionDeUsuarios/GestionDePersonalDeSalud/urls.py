from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PersonalSaludViewSet

app_name = "GestionDePersonalDeSalud"

router = DefaultRouter()
router.register(r"", PersonalSaludViewSet, basename="personal-salud")

urlpatterns = [
    path("", include(router.urls)),
]
