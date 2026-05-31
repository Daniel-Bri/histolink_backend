from django.urls import path
from . import views

app_name = "FirmaDigitalDeConsulta"

urlpatterns = [
    path('consultas/<int:consulta_id>/firmar/', views.firmar_consulta, name='firmar-consulta'),
]
