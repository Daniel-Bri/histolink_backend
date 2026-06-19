from django.urls import path
from .views import RegistrarTokenFCMView, EliminarTokenFCMView

app_name = "Notificaciones"

urlpatterns = [
    path("token/", RegistrarTokenFCMView.as_view(),  name="registrar-token"),
    path("token/eliminar/", EliminarTokenFCMView.as_view(), name="eliminar-token"),
]
