from django.db import models


class Tenant(models.Model):
    nombre = models.CharField(
        max_length=200,
        verbose_name="Nombre del establecimiento",
        help_text="Nombre oficial del establecimiento de salud. Ej: Hospital San Juan de Dios",
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name="Identificador único",
        help_text="Identificador URL-friendly del establecimiento. Ej: hospital-san-juan. Se usa internamente.",
    )
    nit = models.CharField(
        max_length=20,
        blank=True,
        default="",
        verbose_name="NIT",
        help_text="Número de Identificación Tributaria del establecimiento.",
    )
    direccion = models.TextField(
        blank=True,
        default="",
        verbose_name="Dirección",
    )
    telefono = models.CharField(
        max_length=30,
        blank=True,
        default="",
        verbose_name="Teléfono",
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Desactivar para suspender acceso al establecimiento sin eliminar sus datos.",
    )
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")
    actualizado_en = models.DateTimeField(auto_now=True, verbose_name="Actualizado en")

    class Meta:
        verbose_name = "Establecimiento"
        verbose_name_plural = "Establecimientos"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre
