from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TriajeViewSet

app_name = "RegistroDeTriaje"

router = DefaultRouter()
router.register(r"", TriajeViewSet, basename="triaje")

urlpatterns = [
    path("", include(router.urls)),
]
