from django.urls import path
from .views import ReporteProduccionView, ReporteSNISView

app_name = "ReporteProduccion"

urlpatterns = [
    path("produccion/", ReporteProduccionView.as_view(), name="produccion"),
    path("snis/",       ReporteSNISView.as_view(),       name="snis"),
]
