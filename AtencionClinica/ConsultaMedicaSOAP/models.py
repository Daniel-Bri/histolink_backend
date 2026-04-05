# CU8 - Consulta Médica SOAP

from django.conf import settings
from django.db import models
from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente
from AtencionClinica.RegistroDeTriaje.models import Triaje


class Consulta(models.Model):
    ESTADO_CHOICES = [
        ("BORRADOR",   "Borrador"),
        ("COMPLETADA", "Completada"),
        ("FIRMADA",    "Firmada"),
    ]

    # TODO: cuando AperturaFichaYColaDeAtencion implemente Ficha,
    # paciente se reemplaza por ficha (OneToOneField → Ficha).
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="consultas",
    )
    # FK a PersonalSalud — usa AUTH_USER_MODEL como placeholder
    medico = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="consultas_realizadas",
        db_index=True,
    )
    triaje = models.OneToOneField(
        Triaje,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="consulta",
    )
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default="BORRADOR")

    # SOAP — S: Subjetivo
    motivo_consulta           = models.TextField(verbose_name="Motivo de consulta")
    historia_enfermedad_actual = models.TextField(verbose_name="Historia de la enfermedad actual")

    # SOAP — O: Objetivo
    examen_fisico = models.TextField(blank=True, default="", verbose_name="Examen físico")

    # SOAP — A: Análisis/Diagnóstico
    impresion_diagnostica    = models.TextField(verbose_name="Impresión diagnóstica")
    codigo_cie10_principal   = models.CharField(max_length=10, db_index=True,
                                                verbose_name="Código CIE-10 principal")  # Obligatorio para SNIS Bolivia
    codigo_cie10_secundario  = models.CharField(max_length=10, blank=True, default="")
    descripcion_cie10        = models.CharField(max_length=300, blank=True, default="")

    # SOAP — P: Plan
    plan_tratamiento  = models.TextField(blank=True, default="", verbose_name="Plan de tratamiento")
    indicaciones_alta = models.TextField(blank=True, default="", verbose_name="Indicaciones al alta")

    # Derivación
    requiere_derivacion = models.BooleanField(default=False)
    derivacion_destino  = models.CharField(max_length=200, blank=True, default="")
    derivacion_motivo   = models.TextField(blank=True, default="")

    # Firma digital
    hash_documento  = models.CharField(max_length=64, blank=True, default="", db_index=True)
    firmada_por     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="consultas_firmadas",
    )
    firmada_en = models.DateTimeField(null=True, blank=True)

    creado_en      = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Consulta"
        verbose_name_plural = "Consultas"
        ordering            = ["-creado_en"]
        indexes = [
            models.Index(fields=["medico", "creado_en"], name="idx_consulta_medico_fecha"),
        ]

    def __str__(self):
        return f"Consulta {self.id} - {self.paciente} ({self.creado_en.date()})"
