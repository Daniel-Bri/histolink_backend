# CU10 - Solicitud de Estudios y Carga de Resultados

from django.conf import settings
from django.db import models
from AtencionClinica.ConsultaMedicaSOAP.models import Consulta


class OrdenEstudio(models.Model):
    TIPO_CHOICES = [
        ("LAB", "Laboratorio"),
        ("RX",  "Radiografía"),
        ("ECO", "Ecografía"),
        ("TAC", "Tomografía"),
        ("RMN", "Resonancia Magnética"),
        ("ECG", "Electrocardiograma"),
        ("END", "Endoscopía"),
        ("BIO", "Biopsia"),
        ("OTR", "Otro"),
    ]
    ESTADO_CHOICES = [
        ("PENDIENTE",   "Pendiente"),
        ("EN_PROCESO",  "En proceso"),
        ("DISPONIBLE",  "Disponible"),
        ("ENTREGADO",   "Entregado"),
        ("CANCELADO",   "Cancelado"),
    ]

    consulta = models.ForeignKey(
        Consulta,
        on_delete=models.CASCADE,
        related_name="ordenes",
    )
    # FK a PersonalSalud — usa AUTH_USER_MODEL como placeholder
    medico_solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="ordenes_solicitadas",
    )

    tipo_estudio        = models.CharField(max_length=5, choices=TIPO_CHOICES, db_index=True)
    descripcion_estudio = models.CharField(max_length=300)
    indicacion_clinica  = models.TextField()
    observaciones       = models.TextField(blank=True, default="")

    estado        = models.CharField(max_length=15, choices=ESTADO_CHOICES, default="PENDIENTE", db_index=True)
    urgente       = models.BooleanField(default=False)
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_limite  = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name        = "Orden de Estudio"
        verbose_name_plural = "Órdenes de Estudio"
        ordering            = ["-fecha_solicitud"]
        indexes = [
            models.Index(fields=["estado", "urgente"], name="idx_orden_estado_urgente"),
        ]

    def __str__(self):
        return f"{self.get_tipo_estudio_display()} — {self.descripcion_estudio}"


class ResultadoEstudio(models.Model):
    """
    Resultado de una OrdenEstudio. OneToOne con la orden.
    hash_archivo se ancla en blockchain para garantizar integridad forense.
    """
    orden = models.OneToOneField(
        OrdenEstudio,
        on_delete=models.CASCADE,
        related_name="resultado",
    )
    # FK a PersonalSalud — usa AUTH_USER_MODEL como placeholder
    ingresado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="resultados_ingresados",
    )

    fecha_resultado   = models.DateTimeField()
    archivo_adjunto   = models.CharField(max_length=512, blank=True, default="")
    nombre_archivo    = models.CharField(max_length=255, blank=True, default="")
    valores_resultado = models.TextField(blank=True, default="")

    interpretacion_medica = models.TextField(blank=True, default="")
    interpretado_por      = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="resultados_interpretados",
    )
    fecha_interpretacion = models.DateTimeField(null=True, blank=True)

    # SHA-256 del archivo — se ancla en blockchain
    hash_archivo = models.CharField(max_length=64, blank=True, default="", db_index=True)

    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Resultado de Estudio"
        verbose_name_plural = "Resultados de Estudios"

    def __str__(self):
        return f"Resultado de {self.orden}"
