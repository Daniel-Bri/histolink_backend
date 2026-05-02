from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecetaViewSet

app_name = "EmisionDeRecetaMedica"

router = DefaultRouter()
router.register(r'recetas', RecetaViewSet, basename='receta')

urlpatterns = [
    path('', include(router.urls)),
]