# CU5 - Edición de Antecedentes Médicos

from django.conf import settings
from django.db import models
from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente


class Antecedente(models.Model):
    """
    Historial médico permanente del paciente. Un único registro por paciente (OneToOne).
    Las alergias, enfermedades crónicas y grupo sanguíneo van AQUÍ — no en Paciente.
    Se actualiza a lo largo de la vida clínica del paciente.
    """

    GRUPO_SANGUINEO_CHOICES = [
        ("A+", "A+"), ("A-", "A-"),
        ("B+", "B+"), ("B-", "B-"),
        ("AB+", "AB+"), ("AB-", "AB-"),
        ("O+", "O+"), ("O-", "O-"),
        ("?",  "Desconocido"),
    ]

    paciente = models.OneToOneField(
        Paciente,
        on_delete=models.CASCADE,
        related_name="antecedentes",
        verbose_name="Paciente",
        help_text="Paciente al que pertenece este historial. Relación uno a uno.",
    )
    grupo_sanguineo = models.CharField(
        max_length=3,
        choices=GRUPO_SANGUINEO_CHOICES,
        default="?",
        verbose_name="Grupo sanguíneo",
        help_text="Grupo sanguíneo del paciente. Usar '?' si se desconoce.",
    )
    alergias = models.TextField(
        blank=True,
        default="",
        verbose_name="Alergias",
        help_text="Lista de alergias conocidas. Ej: Penicilina, látex, maní. Una por línea.",
    )
    ant_patologicos = models.TextField(
        blank=True,
        default="",
        verbose_name="Antecedentes patológicos",
        help_text="Enfermedades crónicas actuales del paciente. Ej: Diabetes tipo 2, HTA.",
    )
    ant_no_patologicos = models.TextField(
        blank=True,
        default="",
        verbose_name="Antecedentes no patológicos",
        help_text="Hábitos y estilo de vida. Ej: tabaquismo 10 cig/día, consumo ocasional de alcohol.",
    )
    ant_quirurgicos = models.TextField(
        blank=True,
        default="",
        verbose_name="Antecedentes quirúrgicos",
        help_text="Cirugías previas con fecha aproximada. Ej: Apendicectomía 2018.",
    )
    ant_familiares = models.TextField(
        blank=True,
        default="",
        verbose_name="Antecedentes familiares",
        help_text="Enfermedades hereditarias o de alta incidencia familiar. Ej: Diabetes en padre y abuelo.",
    )
    ant_gineco_obstetricos = models.TextField(
        blank=True,
        default="",
        verbose_name="Antecedentes gineco-obstétricos",
        help_text="Solo para pacientes femeninas. Formato G:P:A:C (Gestas:Partos:Abortos:Cesáreas). Ej: G3P2A1C0.",
    )
    medicacion_actual = models.TextField(
        blank=True,
        default="",
        verbose_name="Medicación actual",
        help_text="Medicamentos crónicos permanentes que toma el paciente. No incluir los de cada consulta.",
    )
    esquema_vacunacion = models.TextField(
        blank=True,
        default="",
        verbose_name="Esquema de vacunación",
        help_text="Vacunas aplicadas y fechas. Ej: Hepatitis B (2020), Influenza (2024).",
    )
    ultima_actualizacion_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="antecedentes_actualizados",
        verbose_name="Última actualización por",
        help_text="Personal de salud que realizó la última modificación de este historial.",
    )
    creado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Creado en",
        help_text="Timestamp automático de creación.",
    )
    actualizado_en = models.DateTimeField(
        auto_now=True,
        verbose_name="Actualizado en",
        help_text="Timestamp automático de la última modificación.",
    )

    class Meta:
        verbose_name        = "Antecedente"
        verbose_name_plural = "Antecedentes"

    def __str__(self):
        return f"Antecedentes de {self.paciente}"
