from django.urls import path
from .views import PrediccionRiesgosView

app_name = "PrediccionDeRiesgosClinicos"

urlpatterns = [
    # T004: Endpoint para consulta de riesgos por paciente (vía Query Params)
    # Ejemplo: /api/ia/riesgo/?paciente_id=1&tipo=diabetes_tipo2
    path('riesgo/', PrediccionRiesgosView.as_view(), name='paciente-riesgo'),
]
