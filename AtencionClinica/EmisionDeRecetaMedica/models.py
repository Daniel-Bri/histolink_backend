# CU9 - Emisión de Receta Médica

from django.contrib.auth.models import User
from django.db import models
from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente
from AtencionClinica.ConsultaMedicaSOAP.models import ConsultaSOAP


class Receta(models.Model):
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="recetas",
    )
    medico = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="recetas_emitidas",
    )
    consulta = models.ForeignKey(
        ConsultaSOAP,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recetas",
    )

    fecha = models.DateTimeField(auto_now_add=True)
    observaciones = models.TextField(blank=True, default="")
    firmada = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Receta"
        verbose_name_plural = "Recetas"
        ordering = ["-fecha"]

    def __str__(self):
        return f"Receta {self.id} - {self.paciente} ({self.fecha.date()})"


class ItemReceta(models.Model):
    receta = models.ForeignKey(
        Receta,
        on_delete=models.CASCADE,
        related_name="items",
    )
    medicamento = models.CharField(max_length=200)
    dosis = models.CharField(max_length=100)
    frecuencia = models.CharField(max_length=100)
    duracion = models.CharField(max_length=100)
    indicaciones = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "Ítem de Receta"
        verbose_name_plural = "Ítems de Receta"

    def __str__(self):
        return f"{self.medicamento} - {self.dosis}"
