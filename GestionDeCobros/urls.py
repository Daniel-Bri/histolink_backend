from django.urls import path
from .views import CrearSesionCobroView

urlpatterns = [
    path("crear-sesion/", CrearSesionCobroView.as_view(), name="crear-sesion-cobro"),
]