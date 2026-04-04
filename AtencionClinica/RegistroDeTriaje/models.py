# CU7 - Registro de Triaje

from django.contrib.auth.models import User
from django.db import models
from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente


class Triaje(models.Model):
    PRIORIDAD_CHOICES = [
        (1, "Rojo - Inmediato"),
        (2, "Naranja - Muy urgente"),
        (3, "Amarillo - Urgente"),
        (4, "Verde - Poco urgente"),
        (5, "Azul - No urgente"),
    ]

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="triajes",
    )
    enfermera = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="triajes_registrados",
    )

    fecha = models.DateTimeField(auto_now_add=True)

    # Síntomas
    motivo_consulta = models.TextField()
    sintomas = models.TextField(blank=True, default="")

    # Signos vitales
    temperatura = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    presion_sistolica = models.IntegerField(null=True, blank=True)
    presion_diastolica = models.IntegerField(null=True, blank=True)
    frecuencia_cardiaca = models.IntegerField(null=True, blank=True)
    frecuencia_respiratoria = models.IntegerField(null=True, blank=True)
    saturacion_oxigeno = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    glasgow = models.IntegerField(null=True, blank=True)
    dolor_eva = models.IntegerField(null=True, blank=True)

    prioridad = models.IntegerField(choices=PRIORIDAD_CHOICES, default=3)
    clasificacion_ia = models.CharField(max_length=20, blank=True, default="")
    observaciones = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "Triaje"
        verbose_name_plural = "Triajes"
        ordering = ["-fecha"]

    def __str__(self):
        return f"Triaje {self.id} - {self.paciente} ({self.fecha.date()})"
