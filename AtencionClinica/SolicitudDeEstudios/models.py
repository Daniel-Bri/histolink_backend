# CU10 - Solicitud de Estudios y Carga de Resultados

from django.conf import settings
from django.db import models
from AtencionClinica.ConsultaMedicaSOAP.models import Consulta


class OrdenEstudio(models.Model):
    """
    Solicitud de estudio complementario emitida por un médico en una consulta.
    Una consulta puede tener N órdenes de distinto tipo.
    El campo 'urgente' activa una cola prioritaria en el laboratorio.
    El resultado se almacena en ResultadoEstudio (OneToOne).
    """

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
        ("PENDIENTE",  "Pendiente"),
        ("EN_PROCESO", "En proceso"),
        ("DISPONIBLE", "Disponible"),
        ("ENTREGADO",  "Entregado"),
        ("CANCELADO",  "Cancelado"),
    ]

    consulta = models.ForeignKey(
        Consulta,
        on_delete=models.CASCADE,
        related_name="ordenes",
        verbose_name="Consulta",
        help_text="Consulta médica en la que se solicitó este estudio.",
    )
    medico_solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="ordenes_solicitadas",
        verbose_name="Médico solicitante",
        help_text="Médico que solicitó el estudio.",
    )
    tipo_estudio = models.CharField(
        max_length=5,
        choices=TIPO_CHOICES,
        db_index=True,
        verbose_name="Tipo de estudio",
        help_text="Categoría del estudio: LAB=Laboratorio, RX=Radiografía, ECO=Ecografía, TAC, RMN, etc.",
    )
    descripcion_estudio = models.CharField(
        max_length=300,
        verbose_name="Descripción del estudio",
        help_text="Nombre específico del estudio. Ej: Hemograma completo, Rx tórax PA, Ecografía abdominal.",
    )
    indicacion_clinica = models.TextField(
        verbose_name="Indicación clínica",
        help_text="Justificación clínica del estudio. Obligatorio para el laboratorio/imagen. Ej: Sospecha de neumonía.",
    )
    observaciones = models.TextField(
        blank=True, default="",
        verbose_name="Observaciones",
        help_text="Instrucciones especiales para el técnico. Ej: paciente en ayunas, preparación especial.",
    )
    estado = models.CharField(
        max_length=15,
        choices=ESTADO_CHOICES,
        default="PENDIENTE",
        db_index=True,
        verbose_name="Estado",
        help_text="Flujo: PENDIENTE → EN_PROCESO → DISPONIBLE → ENTREGADO. O CANCELADO si no se realiza.",
    )
    urgente = models.BooleanField(
        default=False,
        verbose_name="Urgente",
        help_text="True = resultado necesario el mismo día. Activa cola prioritaria en laboratorio.",
    )
    fecha_solicitud = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de solicitud",
        help_text="Timestamp automático de cuándo se realizó la orden.",
    )
    fecha_limite = models.DateField(
        null=True, blank=True,
        verbose_name="Fecha límite",
        help_text="Fecha máxima para que el resultado esté disponible. Opcional.",
    )

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
    Resultado de una OrdenEstudio. Relación OneToOne: una orden tiene un resultado.
    hash_archivo es el SHA-256 del PDF/imagen — se ancla en blockchain para
    garantizar que el archivo no fue alterado después de ser emitido.
    """

    orden = models.OneToOneField(
        OrdenEstudio,
        on_delete=models.CASCADE,
        related_name="resultado",
        verbose_name="Orden de estudio",
        help_text="Orden de estudio a la que corresponde este resultado.",
    )
    ingresado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="resultados_ingresados",
        verbose_name="Ingresado por",
        help_text="Laboratorista o técnico que cargó el resultado al sistema.",
    )
    fecha_resultado = models.DateTimeField(
        verbose_name="Fecha del resultado",
        help_text="Cuándo estuvo listo el resultado del estudio.",
    )
    archivo_adjunto = models.CharField(
        max_length=512,
        blank=True, default="",
        verbose_name="Archivo adjunto",
        help_text="Ruta relativa del archivo en el servidor o clave en S3/MinIO. Ej: resultados/2026/hemograma_42.pdf.",
    )
    nombre_archivo = models.CharField(
        max_length=255,
        blank=True, default="",
        verbose_name="Nombre del archivo",
        help_text="Nombre original del archivo para mostrar al usuario. Ej: Hemograma_Juan_Perez.pdf.",
    )
    valores_resultado = models.TextField(
        blank=True, default="",
        verbose_name="Valores del resultado",
        help_text="Valores en texto libre para resultados de laboratorio. Ej: Hemoglobina: 12.5 g/dL, Hematocrito: 38%.",
    )
    interpretacion_medica = models.TextField(
        blank=True, default="",
        verbose_name="Interpretación médica",
        help_text="Interpretación del médico tratante al revisar el resultado. Se llena después de la entrega.",
    )
    interpretado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="resultados_interpretados",
        verbose_name="Interpretado por",
        help_text="Médico que interpretó el resultado. Nulo hasta que el médico lo revise.",
    )
    fecha_interpretacion = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Fecha de interpretación",
        help_text="Cuándo interpretó el médico el resultado.",
    )
    hash_archivo = models.CharField(
        max_length=64,
        blank=True, default="",
        db_index=True,
        verbose_name="Hash del archivo",
        help_text="SHA-256 del archivo adjunto. Se ancla en blockchain para verificación de integridad forense.",
    )
    creado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Creado en",
        help_text="Timestamp automático de cuándo se cargó el resultado.",
    )

    class Meta:
        verbose_name        = "Resultado de Estudio"
        verbose_name_plural = "Resultados de Estudios"

    def __str__(self):
        return f"Resultado de {self.orden}"
