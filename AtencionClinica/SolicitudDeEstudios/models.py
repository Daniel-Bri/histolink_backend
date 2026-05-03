# CU10 - Solicitud de Estudios y Carga de Resultados (T009 OrdenEstudio)

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.utils import timezone


class OrdenEstudio(models.Model):
    """
    Solicitud de estudio complementario emitida desde una consulta SOAP.
    Correlativo ORD-AAAA-#####; compatibilidad con ResultadoEstudio (T010) vía related_name resultado.
    """

    class Estado(models.TextChoices):
        SOLICITADA = "SOLICITADA", "Solicitada"
        EN_PROCESO = "EN_PROCESO", "En Proceso"
        COMPLETADA = "COMPLETADA", "Completada"
        ANULADA = "ANULADA", "Anulada"

    class TipoEstudio(models.TextChoices):
        LAB = "LAB", "Laboratorio"
        RX = "RX", "Radiografía"
        ECO = "ECO", "Ecografía"
        TC = "TC", "Tomografía Computarizada"
        RMN = "RMN", "Resonancia Magnética"
        ECG = "ECG", "Electrocardiograma"
        END = "END", "Endoscopía"
        OTRO = "OTRO", "Otro"

    consulta = models.ForeignKey(
        "ConsultaMedicaSOAP.Consulta",
        on_delete=models.CASCADE,
        related_name="ordenes_estudio",
        verbose_name="Consulta",
    )
    tipo = models.CharField(max_length=20, choices=TipoEstudio.choices, verbose_name="Tipo")
    descripcion = models.TextField(
        verbose_name="Descripción del estudio",
        help_text="Descripción detallada del estudio solicitado.",
    )
    indicacion_clinica = models.TextField(
        verbose_name="Indicación clínica",
        help_text="Justificación médica del estudio.",
    )
    urgente = models.BooleanField(default=False, verbose_name="Urgente")
    motivo_urgencia = models.TextField(
        blank=True,
        null=True,
        verbose_name="Motivo de urgencia",
        help_text="Obligatorio si urgente=True.",
    )
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.SOLICITADA,
        verbose_name="Estado",
        db_index=True,
    )
    correlativo_orden = models.CharField(
        max_length=24,
        unique=True,
        editable=False,
        blank=True,
        verbose_name="Correlativo",
    )
    fecha_solicitud = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de solicitud")
    fecha_inicio_proceso = models.DateTimeField(null=True, blank=True, verbose_name="Inicio en laboratorio")
    fecha_completada = models.DateTimeField(null=True, blank=True, verbose_name="Completada")
    medico_solicitante = models.ForeignKey(
        "GestionDePersonalDeSalud.PersonalSalud",
        on_delete=models.PROTECT,
        related_name="ordenes_solicitadas",
        verbose_name="Médico solicitante",
    )
    tecnico_responsable = models.ForeignKey(
        "GestionDePersonalDeSalud.PersonalSalud",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ordenes_procesadas",
        verbose_name="Técnico responsable",
    )
    resultado_texto = models.TextField(blank=True, null=True, verbose_name="Resultado (texto)")
    resultado_archivo = models.FileField(
        upload_to="resultados_estudios/%Y/%m/",
        null=True,
        blank=True,
        verbose_name="Resultado (archivo)",
    )
    esta_activa = models.BooleanField(default=True, verbose_name="Activa")
    creado_en = models.DateTimeField(
        default=timezone.now,
        verbose_name="Creado en",
    )
    actualizado_en = models.DateTimeField(auto_now=True, verbose_name="Actualizado en")

    class Meta:
        verbose_name = "Orden de Estudio"
        verbose_name_plural = "Órdenes de Estudio"
        ordering = ["-urgente", "-fecha_solicitud"]
        indexes = [
            # ≤30 chars (Django E034); compuesto estado + urgente (T009)
            models.Index(
                fields=["estado", "urgente"],
                name="ordenestudio_esturg_idx",
            ),
            models.Index(
                fields=["consulta", "estado"],
                name="SolicitudDe_consult_36cc07_idx",
            ),
            models.Index(
                fields=["fecha_solicitud"],
                name="SolicitudDe_fecha_s_0f42a9_idx",
            ),
        ]

    TRANSICIONES = {
        Estado.SOLICITADA: {Estado.EN_PROCESO, Estado.ANULADA},
        Estado.EN_PROCESO: {Estado.COMPLETADA, Estado.ANULADA},
        Estado.COMPLETADA: set(),
        Estado.ANULADA: set(),
    }

    def __str__(self):
        return f"{self.correlativo_orden or self.pk} — {self.get_tipo_display()}"

    def clean(self):
        super().clean()
        orig = getattr(self, "_estado_original", None)
        if self.pk and orig is not None:
            self._validar_transicion(orig, self.estado)
        if self.urgente and not (self.motivo_urgencia and str(self.motivo_urgencia).strip()):
            raise ValidationError(
                {"motivo_urgencia": "Debe especificar el motivo de urgencia."}
            )
        if self.estado == self.Estado.COMPLETADA:
            tiene_txt = bool(self.resultado_texto and str(self.resultado_texto).strip())
            tiene_arch = bool(self.resultado_archivo)
            if not tiene_txt and not tiene_arch:
                raise ValidationError(
                    "Para completar la orden debe informar resultado en texto y/o archivo."
                )

    @classmethod
    def _siguiente_correlativo_num(cls, year: int) -> int:
        prefix = f"ORD-{year}-"
        ultima = (
            cls.objects.select_for_update()
            .filter(correlativo_orden__startswith=prefix)
            .order_by("-correlativo_orden")
            .first()
        )
        if not ultima:
            return 1
        try:
            return int(ultima.correlativo_orden.rsplit("-", 1)[-1], 10) + 1
        except (ValueError, IndexError):
            return 1

    def _validar_transicion(self, prev: str, nuevo: str) -> None:
        if prev == nuevo:
            return
        permitidas = self.TRANSICIONES.get(prev, set())
        if nuevo not in permitidas:
            raise ValidationError(
                {"estado": f"Transición no permitida: {prev} → {nuevo}."}
            )

    def _marcar_fechas_por_estado(self, prev: str, nuevo: str) -> None:
        if nuevo == self.Estado.EN_PROCESO and prev != self.Estado.EN_PROCESO:
            if self.fecha_inicio_proceso is None:
                self.fecha_inicio_proceso = timezone.now()
        if nuevo == self.Estado.COMPLETADA and prev != self.Estado.COMPLETADA:
            if self.fecha_completada is None:
                self.fecha_completada = timezone.now()

    def _limpiar_estado_original_preview(self) -> None:
        """Evita que `_estado_original` de un save() previo contamine `full_clean()` en memoria."""
        self.__dict__.pop("_estado_original", None)

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.full_clean(exclude=["correlativo_orden"])
            year = timezone.now().year
            for intento in range(8):
                with transaction.atomic():
                    n = type(self)._siguiente_correlativo_num(year)
                    self.correlativo_orden = f"ORD-{year}-{n:05d}"
                    try:
                        self.full_clean()
                        super().save(*args, **kwargs)
                        return
                    except IntegrityError as exc:
                        err = str(exc).lower()
                        if intento == 7 or ("unique" not in err and "duplicate" not in err):
                            raise
                self.correlativo_orden = ""
            raise IntegrityError("No se pudo asignar correlativo único ORD.")

        old = type(self).objects.get(pk=self.pk)
        self._estado_original = old.estado

        if old.estado in (self.Estado.COMPLETADA, self.Estado.ANULADA):
            if self.estado != old.estado:
                raise ValidationError("No se puede cambiar el estado de una orden cerrada.")
            for field in self._meta.fields:
                fname = field.name
                if fname in ("pk", "id", "actualizado_en", "esta_activa"):
                    continue
                if getattr(old, fname) != getattr(self, fname):
                    raise ValidationError(
                        f"No se puede modificar la orden en estado {old.estado}."
                    )
            res = super().save(*args, **kwargs)
            self._limpiar_estado_original_preview()
            return res

        if old.estado != self.estado:
            self._marcar_fechas_por_estado(old.estado, self.estado)
        self.full_clean()
        super().save(*args, **kwargs)
        self._limpiar_estado_original_preview()


class ResultadoEstudio(models.Model):
    """
    Resultado detallado asociado a una orden (T010). Relación 1:1 con OrdenEstudio.
    """

    orden = models.OneToOneField(
        OrdenEstudio,
        on_delete=models.CASCADE,
        related_name="resultado",
        verbose_name="Orden de estudio",
    )
    ingresado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="resultados_ingresados",
        verbose_name="Ingresado por",
    )
    fecha_resultado = models.DateTimeField(verbose_name="Fecha del resultado")
    archivo_adjunto = models.CharField(max_length=512, blank=True, default="", verbose_name="Archivo adjunto")
    nombre_archivo = models.CharField(max_length=255, blank=True, default="", verbose_name="Nombre del archivo")
    valores_resultado = models.TextField(blank=True, default="", verbose_name="Valores del resultado")
    interpretacion_medica = models.TextField(blank=True, default="", verbose_name="Interpretación médica")
    interpretado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="resultados_interpretados",
        verbose_name="Interpretado por",
    )
    fecha_interpretacion = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de interpretación")
    hash_archivo = models.CharField(max_length=64, blank=True, default="", db_index=True, verbose_name="Hash del archivo")
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")

    class Meta:
        verbose_name = "Resultado de Estudio"
        verbose_name_plural = "Resultados de Estudios"

    def __str__(self):
        return f"Resultado de {self.orden}"
