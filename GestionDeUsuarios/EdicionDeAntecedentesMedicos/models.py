# CU5 - Edición de Antecedentes Médicos

from django.conf import settings
from django.db import models
from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente


class Antecedente(models.Model):
    GRUPO_SANGUINEO_CHOICES = [
        ("A+", "A+"), ("A-", "A-"),
        ("B+", "B+"), ("B-", "B-"),
        ("AB+", "AB+"), ("AB-", "AB-"),
        ("O+", "O+"), ("O-", "O-"),
        ("?",  "Desconocido"),
    ]

    # Un registro por paciente
    paciente = models.OneToOneField(
        Paciente,
        on_delete=models.CASCADE,
        related_name="antecedentes",
    )

    # Grupo sanguíneo va aquí — no en Paciente
    grupo_sanguineo = models.CharField(max_length=3, choices=GRUPO_SANGUINEO_CHOICES, default="?")

    # Antecedentes personales
    alergias              = models.TextField(blank=True, default="")
    ant_patologicos       = models.TextField(blank=True, default="", verbose_name="Antecedentes patológicos")
    ant_no_patologicos    = models.TextField(blank=True, default="", verbose_name="Antecedentes no patológicos")
    ant_quirurgicos       = models.TextField(blank=True, default="", verbose_name="Antecedentes quirúrgicos")
    ant_familiares        = models.TextField(blank=True, default="", verbose_name="Antecedentes familiares")
    # Solo para pacientes femeninas — formato G:P:A:C
    ant_gineco_obstetricos = models.TextField(blank=True, default="", verbose_name="Antecedentes gineco-obstétricos")

    medicacion_actual   = models.TextField(blank=True, default="")
    esquema_vacunacion  = models.TextField(blank=True, default="")

    # FK a PersonalSalud — usa AUTH_USER_MODEL como placeholder
    ultima_actualizacion_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="antecedentes_actualizados",
    )
    creado_en      = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Antecedente"
        verbose_name_plural = "Antecedentes"

    def __str__(self):
        return f"Antecedentes de {self.paciente}"
