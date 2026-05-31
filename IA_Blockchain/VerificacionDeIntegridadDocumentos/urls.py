from django.urls import path
from . import views

app_name = "VerificacionDeIntegridadDocumentos"

urlpatterns = [
    path('documento/<int:documento_id>/verificar/', views.verificar_documento, name='verificar-documento'),
]
