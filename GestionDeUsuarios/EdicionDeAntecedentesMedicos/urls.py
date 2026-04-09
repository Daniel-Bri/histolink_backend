from django.urls import path
from .views import AntecedenteView

app_name = "EdicionDeAntecedentesMedicos"

urlpatterns = [
    # T008 — GET/PATCH /api/pacientes/{paciente_id}/antecedentes/
    path("<int:paciente_id>/antecedentes/", AntecedenteView.as_view(), name="antecedente-paciente"),
]
