from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FichaViewSet

app_name = "AperturaFichaYColaDeAtencion"

router = DefaultRouter()
router.register("fichas", FichaViewSet, basename="ficha")

urlpatterns = [
    path("", include(router.urls)),
]
