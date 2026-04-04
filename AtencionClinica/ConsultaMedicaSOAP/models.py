# CU8 - Consulta Médica SOAP

from django.contrib.auth.models import User
from django.db import models
from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente
from AtencionClinica.RegistroDeTriaje.models import Triaje


class ConsultaSOAP(models.Model):
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="consultas",
    )
    medico = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="consultas_realizadas",
    )
    triaje = models.OneToOneField(
        Triaje,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="consulta",
    )

    fecha = models.DateTimeField(auto_now_add=True)

    # Formato SOAP
    subjetivo = models.TextField(verbose_name="Subjetivo (síntomas referidos por el paciente)")
    objetivo = models.TextField(verbose_name="Objetivo (hallazgos del examen físico)")
    analisis = models.TextField(verbose_name="Análisis / Diagnóstico")
    plan = models.TextField(verbose_name="Plan de tratamiento")

    diagnostico_cie10 = models.CharField(max_length=10, blank=True, default="", verbose_name="Código CIE-10")
    diagnostico_descripcion = models.CharField(max_length=255, blank=True, default="")

    firmado = models.BooleanField(default=False)
    fecha_firma = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Consulta SOAP"
        verbose_name_plural = "Consultas SOAP"
        ordering = ["-fecha"]

    def __str__(self):
        return f"Consulta {self.id} - {self.paciente} ({self.fecha.date()})"
