from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ConsultaViewSet

app_name = "ConsultaMedicaSOAP"

router = DefaultRouter()
router.register(r'consultas', ConsultaViewSet, basename='consulta')

urlpatterns = [
    path('', include(router.urls)),
]
