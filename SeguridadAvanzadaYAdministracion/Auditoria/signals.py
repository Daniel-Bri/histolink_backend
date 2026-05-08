from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

# Imports de modelos a auditar
from AtencionClinica.ConsultaMedicaSOAP.models import Consulta
from AtencionClinica.EmisionDeRecetaMedica.models import Receta
from AtencionClinica.RegistroDeTriaje.models import Triaje

from .audit_utils import registrar_evento


@receiver(post_save, sender=Consulta)
def audit_consulta_save(sender, instance, created, **kwargs):
    """Auditoría automática para creación y modificación de Consultas."""
    accion = 'CREATE' if created else 'UPDATE'
    registrar_evento(accion, instance)


@receiver(pre_delete, sender=Consulta)
def audit_consulta_delete(sender, instance, **kwargs):
    """Auditoría automática para eliminación de Consultas."""
    registrar_evento('DELETE', instance)


@receiver(post_save, sender=Triaje)
def audit_triaje_save(sender, instance, created, **kwargs):
    """Auditoría automática para creación y modificación de Triajes."""
    accion = 'CREATE' if created else 'UPDATE'
    registrar_evento(accion, instance)


@receiver(pre_delete, sender=Triaje)
def audit_triaje_delete(sender, instance, **kwargs):
    """Auditoría automática para eliminación de Triajes."""
    registrar_evento('DELETE', instance)


@receiver(post_save, sender=Receta)
def audit_receta_save(sender, instance, created, **kwargs):
    """Auditoría automática para creación y modificación de Recetas."""
    accion = 'CREATE' if created else 'UPDATE'
    registrar_evento(accion, instance)


@receiver(pre_delete, sender=Receta)
def audit_receta_delete(sender, instance, **kwargs):
    """Auditoría automática para eliminación de Recetas."""
    registrar_evento('DELETE', instance)
