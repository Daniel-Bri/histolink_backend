from django.urls import path
from .views import ExpedientePacienteView

app_name = "VisualizacionDelExpediente"

urlpatterns = [
    # T011 — GET /api/pacientes/{id}/expediente/
    path("<int:id>/expediente/", ExpedientePacienteView.as_view(), name="expediente-paciente"),
]
