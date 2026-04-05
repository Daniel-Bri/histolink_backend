# CU9 - Emisión de Receta Médica

from django.conf import settings
from django.db import models
from AtencionClinica.ConsultaMedicaSOAP.models import Consulta


class Receta(models.Model):
    """
    Cabecera de la receta médica emitida en una consulta.
    Separada de DetalleReceta para soportar N medicamentos sin duplicar datos de cabecera.
    El flujo es: EMITIDA (por el médico) → DISPENSADA (en farmacia) → ANULADA (si corresponde).
    """

    ESTADO_CHOICES = [
        ("EMITIDA",    "Emitida"),
        ("DISPENSADA", "Dispensada"),
        ("ANULADA",    "Anulada"),
    ]

    consulta = models.ForeignKey(
        Consulta,
        on_delete=models.CASCADE,
        related_name="recetas",
        verbose_name="Consulta",
        help_text="Consulta médica en la que se emitió esta receta.",
    )
    medico = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="recetas_emitidas",
        verbose_name="Médico",
        help_text="Médico que emitió la receta.",
    )
    numero_receta = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        verbose_name="Número de receta",
        help_text="Correlativo único generado automáticamente. Ej: REC-2026-00123.",
    )
    fecha_emision = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de emisión",
        help_text="Timestamp automático de cuándo fue emitida la receta.",
    )
    estado = models.CharField(
        max_length=15,
        choices=ESTADO_CHOICES,
        default="EMITIDA",
        verbose_name="Estado",
        help_text="Estado de la receta: EMITIDA (pendiente de dispensar), DISPENSADA (entregada en farmacia), ANULADA.",
    )
    dispensada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="recetas_dispensadas",
        verbose_name="Dispensada por",
        help_text="Personal de farmacia que dispensó la receta. Nulo hasta que se dispense.",
    )
    fecha_dispensacion = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Fecha de dispensación",
        help_text="Timestamp de cuándo fue dispensada en farmacia.",
    )
    observaciones = models.TextField(
        blank=True, default="",
        verbose_name="Observaciones",
        help_text="Notas adicionales del médico sobre la receta.",
    )

    class Meta:
        verbose_name        = "Receta"
        verbose_name_plural = "Recetas"
        ordering            = ["-fecha_emision"]

    def __str__(self):
        return f"Receta {self.numero_receta} ({self.get_estado_display()})"


class DetalleReceta(models.Model):
    """
    Cada medicamento de una receta (línea de receta).
    Se usa nombre genérico DCI (Denominación Común Internacional), no marcas comerciales.
    Una receta tiene N detalles — el campo 'orden' define el orden de impresión.
    """

    VIA_CHOICES = [
        ("VO",  "Vía oral"),
        ("IV",  "Intravenosa"),
        ("IM",  "Intramuscular"),
        ("SC",  "Subcutánea"),
        ("TOP", "Tópica"),
        ("INH", "Inhalatoria"),
        ("SL",  "Sublingual"),
        ("REC", "Rectal"),
        ("OFT", "Oftálmica"),
        ("OTR", "Otra"),
    ]

    receta = models.ForeignKey(
        Receta,
        on_delete=models.CASCADE,
        related_name="detalles",
        verbose_name="Receta",
        help_text="Receta a la que pertenece este medicamento.",
    )
    medicamento = models.CharField(
        max_length=200,
        verbose_name="Medicamento",
        help_text="Nombre genérico DCI del medicamento. Ej: Amoxicilina, Ibuprofeno. No usar marcas comerciales.",
    )
    concentracion = models.CharField(
        max_length=50,
        blank=True, default="",
        verbose_name="Concentración",
        help_text="Concentración del medicamento. Ej: 500mg, 250mg/5ml, 10mg/ml.",
    )
    forma_farmaceutica = models.CharField(
        max_length=50,
        blank=True, default="",
        verbose_name="Forma farmacéutica",
        help_text="Presentación del medicamento. Ej: tableta, jarabe, ampolla, crema, parche.",
    )
    via_administracion = models.CharField(
        max_length=5,
        choices=VIA_CHOICES,
        default="VO",
        verbose_name="Vía de administración",
        help_text="Ruta por la que se administra el medicamento. VO = vía oral (más común).",
    )
    dosis = models.CharField(
        max_length=100,
        verbose_name="Dosis",
        help_text="Cantidad a administrar por toma. Ej: 1 tableta, 5ml, 500mg.",
    )
    frecuencia = models.CharField(
        max_length=100,
        verbose_name="Frecuencia",
        help_text="Cada cuánto se toma. Ej: cada 8 horas, 3 veces al día, una vez al día.",
    )
    duracion = models.CharField(
        max_length=100,
        verbose_name="Duración",
        help_text="Por cuánto tiempo. Ej: 7 días, 1 mes, hasta terminar.",
    )
    cantidad_total = models.CharField(
        max_length=50,
        blank=True, default="",
        verbose_name="Cantidad total a dispensar",
        help_text="Total que debe entregar farmacia. Ej: 21 tabletas, 1 frasco de 120ml.",
    )
    instrucciones = models.TextField(
        blank=True, default="",
        verbose_name="Instrucciones especiales",
        help_text="Indicaciones adicionales para el paciente. Ej: tomar con alimentos, evitar el sol.",
    )
    orden = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Orden",
        help_text="Posición del medicamento en la receta impresa. 1 = primero, 2 = segundo, etc.",
    )

    class Meta:
        verbose_name        = "Detalle de Receta"
        verbose_name_plural = "Detalles de Receta"
        ordering            = ["orden"]

    def __str__(self):
        return f"{self.medicamento} {self.concentracion} — {self.dosis}"
