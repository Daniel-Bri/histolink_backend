# CU9 - Emisión de Receta Médica

from django.conf import settings
from django.db import models
from AtencionClinica.ConsultaMedicaSOAP.models import Consulta


class Receta(models.Model):
    ESTADO_CHOICES = [
        ("EMITIDA",    "Emitida"),
        ("DISPENSADA", "Dispensada"),
        ("ANULADA",    "Anulada"),
    ]

    consulta = models.ForeignKey(
        Consulta,
        on_delete=models.CASCADE,
        related_name="recetas",
    )
    # FK a PersonalSalud — usa AUTH_USER_MODEL como placeholder
    medico = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="recetas_emitidas",
    )

    numero_receta  = models.CharField(max_length=20, unique=True, db_index=True)  # Ej: REC-2026-00123
    fecha_emision  = models.DateTimeField(auto_now_add=True)
    estado         = models.CharField(max_length=15, choices=ESTADO_CHOICES, default="EMITIDA")

    # Dispensación en farmacia
    dispensada_por    = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="recetas_dispensadas",
    )
    fecha_dispensacion = models.DateTimeField(null=True, blank=True)
    observaciones      = models.TextField(blank=True, default="")

    class Meta:
        verbose_name        = "Receta"
        verbose_name_plural = "Recetas"
        ordering            = ["-fecha_emision"]

    def __str__(self):
        return f"Receta {self.numero_receta} ({self.get_estado_display()})"


class DetalleReceta(models.Model):
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

    receta              = models.ForeignKey(Receta, on_delete=models.CASCADE, related_name="detalles")
    medicamento         = models.CharField(max_length=200)   # Nombre genérico DCI
    concentracion       = models.CharField(max_length=50, blank=True, default="")
    forma_farmaceutica  = models.CharField(max_length=50, blank=True, default="")
    via_administracion  = models.CharField(max_length=5, choices=VIA_CHOICES, default="VO")
    dosis               = models.CharField(max_length=100)
    frecuencia          = models.CharField(max_length=100)
    duracion            = models.CharField(max_length=100)
    cantidad_total      = models.CharField(max_length=50, blank=True, default="")
    instrucciones       = models.TextField(blank=True, default="")
    orden               = models.PositiveSmallIntegerField(default=1)

    class Meta:
        verbose_name        = "Detalle de Receta"
        verbose_name_plural = "Detalles de Receta"
        ordering            = ["orden"]

    def __str__(self):
        return f"{self.medicamento} {self.concentracion} — {self.dosis}"
