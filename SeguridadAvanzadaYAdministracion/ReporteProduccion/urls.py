from django.urls import path
from .views import ReporteProduccionView

app_name = "ReporteProduccion"

urlpatterns = [
    path("produccion/", ReporteProduccionView.as_view(), name="produccion"),
]
