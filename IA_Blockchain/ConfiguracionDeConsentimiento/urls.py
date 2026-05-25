from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TipoConsentimientoViewSet, ConsentimientoViewSet

app_name = "ConfiguracionDeConsentimiento"

router = DefaultRouter()
router.register(r'tipos', TipoConsentimientoViewSet, basename='tipo-consentimiento')
router.register(r'', ConsentimientoViewSet, basename='consentimiento')

urlpatterns = [
    path('', include(router.urls)),
]
