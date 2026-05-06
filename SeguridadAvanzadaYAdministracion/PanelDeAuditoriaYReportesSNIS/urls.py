from django.urls import path
from .views import RegistroAuditoriaListView

app_name = "PanelDeAuditoriaYReportesSNIS"

urlpatterns = [
    path('', RegistroAuditoriaListView.as_view(), name='auditoria-list'),
]