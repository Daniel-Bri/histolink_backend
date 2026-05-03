# CU6 - Apertura de Ficha y Cola de Atención

from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.utils import timezone


class Ficha(models.Model):
    """
    Ficha de atención: une un paciente con el flujo clínico (triaje → consulta).
    Correlativo FICHA-AAAA-XXXXX único por año; transiciones de estado validadas en save().
    """

    class Estado(models.TextChoices):
        ABIERTA = "ABIERTA", "Abierta"
        EN_TRIAJE = "EN_TRIAJE", "En Triaje"
        EN_ATENCION = "EN_ATENCION", "En Atención"
        CERRADA = "CERRADA", "Cerrada"
        CANCELADA = "CANCELADA", "Cancelada"

    paciente = models.ForeignKey(
        "RegistroYBusquedaDePacientes.Paciente",
        on_delete=models.PROTECT,
        related_name="fichas",
        verbose_name="Paciente",
    )
    profesional_apertura = models.ForeignKey(
        "GestionDePersonalDeSalud.PersonalSalud",
        on_delete=models.PROTECT,
        related_name="fichas_aperturadas",
        verbose_name="Profesional que abre la ficha",
    )
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.ABIERTA,
        verbose_name="Estado",
        db_index=True,
    )
    correlativo = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        blank=True,
        verbose_name="Correlativo",
    )
    fecha_apertura = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de apertura",
    )
    fecha_inicio_atencion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Inicio de atención médica",
    )
    fecha_cierre = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de cierre",
    )
    esta_activa = models.BooleanField(
        default=True,
        verbose_name="Activa (no eliminada lógicamente)",
    )
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")
    actualizado_en = models.DateTimeField(auto_now=True, verbose_name="Actualizado en")

    class Meta:
        ordering = ["-fecha_apertura"]
        verbose_name = "Ficha"
        verbose_name_plural = "Fichas"
        indexes = [
            models.Index(fields=["estado", "fecha_apertura"]),
            models.Index(fields=["paciente", "estado"]),
        ]

    def __str__(self):
        return f"{self.correlativo or 'sin-correlativo'} — {self.paciente}"

    VALID_NEXT = {
        Estado.ABIERTA: frozenset({Estado.EN_TRIAJE, Estado.CANCELADA}),
        Estado.EN_TRIAJE: frozenset({Estado.EN_ATENCION, Estado.CANCELADA}),
        Estado.EN_ATENCION: frozenset({Estado.CERRADA, Estado.CANCELADA}),
        Estado.CERRADA: frozenset(),
        Estado.CANCELADA: frozenset(),
    }

    def clean(self):
        super().clean()
        if self.pk:
            prev = (
                type(self).objects.only("estado").get(pk=self.pk).estado
            )
            if prev != self.estado:
                self._validar_transicion(prev, self.estado)

    def _validar_transicion(self, prev: str, nuevo: str) -> None:
        """Reglas RF: flujo lineal, CERRADA terminal, cualquiera puede ir a CANCELADA salvo desde CERRADA."""
        if prev == nuevo:
            return
        if prev == self.Estado.CERRADA:
            raise ValidationError(
                {"estado": "No se pueden modificar fichas cerradas."}
            )
        if prev == self.Estado.CANCELADA:
            raise ValidationError(
                {"estado": "No se pueden modificar fichas canceladas."}
            )
        if nuevo == self.Estado.CANCELADA:
            return
        allowed = self.VALID_NEXT.get(prev, frozenset())
        if nuevo not in allowed:
            raise ValidationError(
                {
                    "estado": f"Transición no permitida: {prev} → {nuevo}.",
                }
            )

    def _marcar_timestamps_estado(self, prev: str, nuevo: str) -> None:
        if nuevo == self.Estado.EN_ATENCION and prev != self.Estado.EN_ATENCION:
            if self.fecha_inicio_atencion is None:
                self.fecha_inicio_atencion = timezone.now()
        if nuevo in (self.Estado.CERRADA, self.Estado.CANCELADA):
            if self.fecha_cierre is None:
                self.fecha_cierre = timezone.now()

    @classmethod
    def _siguiente_numero(cls, year: int) -> int:
        """Siguiente secuencial anual (llamar dentro de transaction.atomic)."""
        prefix = f"FICHA-{year}-"
        última = (
            cls.objects.select_for_update()
            .filter(correlativo__startswith=prefix)
            .order_by("-correlativo")
            .first()
        )
        if not última:
            return 1
        try:
            sufijo = última.correlativo.rsplit("-", 1)[-1]
            return int(sufijo, 10) + 1
        except (ValueError, IndexError):
            return 1

    def save(self, *args, omitir_correlativo_en_lote=False, **kwargs):
        """
        Genera correlativo dentro de una transacción atómica con bloqueo.
        omitir_correlativo_en_lote: migraciones; el correlativo debe venir poblado.
        """
        is_new = self._state.adding

        if not is_new:
            prev_estado = (
                type(self).objects.only("estado").get(pk=self.pk).estado
            )
            self._validar_transicion(prev_estado, self.estado)
            self._marcar_timestamps_estado(prev_estado, self.estado)

        if self.correlativo or omitir_correlativo_en_lote:
            return super().save(*args, **kwargs)

        year = timezone.now().year

        for intento in range(8):
            with transaction.atomic():
                nuevo = type(self)._siguiente_numero(year)
                self.correlativo = f"FICHA-{year}-{nuevo:05d}"
                try:
                    super().save(*args, **kwargs)
                    return
                except IntegrityError as exc:
                    err = str(exc).lower()
                    if intento == 7 or ("unique" not in err and "duplicate" not in err):
                        raise
