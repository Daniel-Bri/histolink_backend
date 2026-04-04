# CU5 - Edición de Antecedentes Médicos

from django.db import models
from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente


class AntecedentesMedicos(models.Model):
    paciente = models.OneToOneField(
        Paciente,
        on_delete=models.CASCADE,
        related_name="antecedentes",
    )

    # Antecedentes personales
    enfermedades_cronicas = models.TextField(blank=True, default="")
    cirugias_previas = models.TextField(blank=True, default="")
    hospitalizaciones = models.TextField(blank=True, default="")
    alergias = models.TextField(blank=True, default="")
    medicacion_actual = models.TextField(blank=True, default="")
    vacunas = models.TextField(blank=True, default="")

    # Antecedentes familiares
    antecedentes_familiares = models.TextField(blank=True, default="")

    # Hábitos
    fuma = models.BooleanField(default=False)
    consume_alcohol = models.BooleanField(default=False)
    actividad_fisica = models.CharField(max_length=50, blank=True, default="")

    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Antecedentes Médicos"
        verbose_name_plural = "Antecedentes Médicos"

    def __str__(self):
        return f"Antecedentes de {self.paciente}"
