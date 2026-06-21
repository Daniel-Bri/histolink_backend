from django.urls import path

from .views import (
    OtorgarPermisoView,
    PermisoPacienteListView,
    RevocarPermisoView,
)

app_name = "GestionDePermisosPaciente"

urlpatterns = [
    path("", PermisoPacienteListView.as_view(), name="list-permisos"),
    path("otorgar/", OtorgarPermisoView.as_view(), name="otorgar-permiso"),
    path("revocar/", RevocarPermisoView.as_view(), name="revocar-permiso"),
]
