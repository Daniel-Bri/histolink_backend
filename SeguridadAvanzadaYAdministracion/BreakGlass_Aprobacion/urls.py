from django.urls import path

from .views import BreakGlassAprobarView, BreakGlassRechazarView

app_name = "BreakGlass_Aprobacion"

urlpatterns = [
    path("<int:pk>/aprobar/", BreakGlassAprobarView.as_view(), name="breakglass-aprobar"),
    path("<int:pk>/rechazar/", BreakGlassRechazarView.as_view(), name="breakglass-rechazar"),
]
