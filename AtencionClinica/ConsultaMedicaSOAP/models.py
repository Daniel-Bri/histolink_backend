# CU8 - Consulta Médica SOAP

from django.conf import settings
from django.db import models
from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente
from AtencionClinica.RegistroDeTriaje.models import Triaje
from Tenants.managers import TenantManager


class Consulta(models.Model):
    """
    El acto médico — tabla más importante del sistema.
    Estructura SOAP: Subjetivo, Objetivo, Análisis, Plan.
    codigo_cie10_principal es OBLIGATORIO para reportes al SNIS Bolivia.
    hash_documento se calcula al firmar y se ancla en blockchain vía Celery.
    Estado: BORRADOR → COMPLETADA → FIRMADA (flujo unidireccional).
    TODO: cuando se implemente Ficha, el campo 'paciente' se reemplaza por 'ficha' (OneToOne).
    """

    ESTADO_CHOICES = [
        ("BORRADOR",   "Borrador"),
        ("COMPLETADA", "Completada"),
        ("FIRMADA",    "Firmada"),
    ]

    tenant = models.ForeignKey(
        'Tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='consultas',
        verbose_name='Establecimiento',
    )
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="consultas",
        verbose_name="Paciente",
        help_text="Paciente atendido en esta consulta.",
    )
    medico = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="consultas_realizadas",
        db_index=True,
        verbose_name="Médico",
        help_text="Médico que realizó la consulta.",
    )
    triaje = models.OneToOneField(
        Triaje,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="consulta",
        verbose_name="Triaje",
        help_text="Triaje previo asociado a esta consulta. Opcional si no pasó por triaje.",
    )
    estado = models.CharField(
        max_length=15,
        choices=ESTADO_CHOICES,
        default="BORRADOR",
        verbose_name="Estado",
        help_text="Ciclo de vida: BORRADOR (en edición) → COMPLETADA (lista) → FIRMADA (con firma digital).",
    )

    # SOAP — S: Subjetivo (lo que refiere el paciente)
    motivo_consulta = models.TextField(
        verbose_name="Motivo de consulta",
        help_text="SOAP-S: Por qué viene el paciente. En sus propias palabras. Ej: 'Dolor abdominal de 3 días'.",
    )
    historia_enfermedad_actual = models.TextField(
        verbose_name="Historia de la enfermedad actual",
        help_text="SOAP-S: Relato cronológico de inicio, evolución, síntomas asociados y factores modificadores.",
    )

    # SOAP — O: Objetivo (hallazgos del médico)
    examen_fisico = models.TextField(
        blank=True, default="",
        verbose_name="Examen físico",
        help_text="SOAP-O: Hallazgos del examen físico por sistemas. Ej: Abdomen: dolor en FID a la palpación.",
    )

    # SOAP — A: Análisis / Diagnóstico
    impresion_diagnostica = models.TextField(
        verbose_name="Impresión diagnóstica",
        help_text="SOAP-A: Diagnóstico presuntivo o definitivo del médico.",
    )
    codigo_cie10_principal = models.CharField(
        max_length=10,
        db_index=True,
        verbose_name="Código CIE-10 principal",
        help_text="OBLIGATORIO para estadísticas SNIS Bolivia. Ej: J18.9 (Neumonía), E11 (Diabetes tipo 2).",
    )
    codigo_cie10_secundario = models.CharField(
        max_length=10,
        blank=True, default="",
        verbose_name="Código CIE-10 secundario",
        help_text="Diagnóstico secundario: complicación o comorbilidad relevante. Opcional.",
    )
    descripcion_cie10 = models.CharField(
        max_length=300,
        blank=True, default="",
        verbose_name="Descripción del diagnóstico CIE-10",
        help_text="Descripción textual del código CIE-10 principal para lectura rápida.",
    )

    # SOAP — P: Plan
    plan_tratamiento = models.TextField(
        blank=True, default="",
        verbose_name="Plan de tratamiento",
        help_text="SOAP-P: Indicaciones, tratamiento no farmacológico, seguimiento y controles.",
    )
    indicaciones_alta = models.TextField(
        blank=True, default="",
        verbose_name="Indicaciones al alta",
        help_text="Instrucciones entregadas al paciente al momento de salir del establecimiento.",
    )

    # Derivación
    requiere_derivacion = models.BooleanField(
        default=False,
        verbose_name="Requiere derivación",
        help_text="True si el paciente necesita ser atendido en otro nivel de atención.",
    )
    derivacion_destino = models.CharField(
        max_length=200,
        blank=True, default="",
        verbose_name="Destino de derivación",
        help_text="Establecimiento o especialidad a donde se deriva. Ej: Hospital de 2do nivel, Cardiología.",
    )
    derivacion_motivo = models.TextField(
        blank=True, default="",
        verbose_name="Motivo de derivación",
        help_text="Justificación clínica de por qué se deriva al paciente.",
    )

    # Firma digital
    hash_documento = models.CharField(
        max_length=64,
        blank=True, default="",
        db_index=True,
        verbose_name="Hash del documento",
        help_text="SHA-256 del contenido de la consulta. Vacío hasta que el médico firma. Se ancla en blockchain.",
    )
    firmada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="consultas_firmadas",
        verbose_name="Firmada por",
        help_text="Médico que firmó digitalmente la consulta. Nulo hasta que se firme.",
    )
    firmada_en = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Firmada en",
        help_text="Timestamp de cuándo se realizó la firma digital.",
    )
    creado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Creado en",
        help_text="Timestamp automático de creación de la consulta.",
    )
    actualizado_en = models.DateTimeField(
        auto_now=True,
        verbose_name="Actualizado en",
        help_text="Timestamp automático de la última modificación.",
    )

    objects = TenantManager()

    class Meta:
        verbose_name        = "Consulta"
        verbose_name_plural = "Consultas"
        ordering            = ["-creado_en"]
        indexes = [
            models.Index(fields=["medico", "creado_en"], name="idx_consulta_medico_fecha"),
        ]

    def __str__(self):
        return f"Consulta {self.id} - {self.paciente} ({self.creado_en.date()})"
