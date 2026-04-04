# CU10 - Solicitud de Estudios y Carga de Resultados

from django.contrib.auth.models import User
from django.db import models
from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente
from AtencionClinica.ConsultaMedicaSOAP.models import ConsultaSOAP


class SolicitudEstudio(models.Model):
    TIPO_CHOICES = [
        ("laboratorio", "Laboratorio"),
        ("imagen", "Imagen"),
        ("otro", "Otro"),
    ]
    ESTADO_CHOICES = [
        ("pendiente", "Pendiente"),
        ("en_proceso", "En proceso"),
        ("completado", "Completado"),
        ("cancelado", "Cancelado"),
    ]

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="estudios",
    )
    solicitante = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="estudios_solicitados",
    )
    consulta = models.ForeignKey(
        ConsultaSOAP,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="estudios",
    )

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    descripcion = models.CharField(max_length=255)
    indicaciones = models.TextField(blank=True, default="")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="pendiente")

    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_resultado = models.DateTimeField(null=True, blank=True)
    resultado = models.TextField(blank=True, default="")
    archivo_resultado = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        verbose_name = "Solicitud de Estudio"
        verbose_name_plural = "Solicitudes de Estudios"
        ordering = ["-fecha_solicitud"]

    def __str__(self):
        return f"{self.tipo} - {self.descripcion} ({self.paciente})"
