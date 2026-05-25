from django.urls import path
from . import views

urlpatterns = [
    path('identidad/', views.obtener_identidad),
    path('identidad/registrar/', views.registrar_identidad),
    path('verificar-cadena/', views.verificar_cadena),
    path('verificar-rol/<int:usuario_id>/', views.verificar_rol),
    path('eventos/', views.listar_eventos),
]