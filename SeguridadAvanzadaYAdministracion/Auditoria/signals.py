"""
signals.py — Auditoría automática vía Django signals.

Modelos auditados:
  Clínico:      Consulta, Triaje, Receta, Ficha, OrdenEstudio, ResultadoEstudio
  Pacientes:    Paciente, Antecedente
  Personal:     PersonalSalud
"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

# ── Modelos clínicos ya existentes ───────────────────────────────────────
from AtencionClinica.ConsultaMedicaSOAP.models import Consulta
from AtencionClinica.EmisionDeRecetaMedica.models import Receta
from AtencionClinica.RegistroDeTriaje.models import Triaje

# ── Modelos nuevos ───────────────────────────────────────────────────────
from AtencionClinica.AperturaFichaYColaDeAtencion.models import Ficha
from AtencionClinica.SolicitudDeEstudios.models import OrdenEstudio, ResultadoEstudio
from GestionDeUsuarios.EdicionDeAntecedentesMedicos.models import Antecedente
from GestionDeUsuarios.GestionDePersonalDeSalud.models import PersonalSalud
from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente

from .audit_utils import registrar_evento


# ── Helpers: resumen de campos clave por modelo ──────────────────────────

def _resumen_paciente(p):
    return {
        'ci': p.ci,
        'nombre': f'{p.nombres} {p.apellido_paterno} {p.apellido_materno}'.strip(),
        'sexo': p.sexo,
        'fecha_nacimiento': str(p.fecha_nacimiento) if p.fecha_nacimiento else None,
    }

def _resumen_ficha(f):
    return {
        'correlativo': f.correlativo,
        'estado': f.estado,
        'paciente_ci': f.paciente.ci if f.paciente_id else None,
    }

def _resumen_orden(o):
    return {
        'correlativo': o.correlativo_orden,
        'tipo': o.tipo,
        'estado': o.estado,
        'urgente': o.urgente,
    }

def _resumen_resultado(r):
    return {
        'orden_id': r.orden_id,
        'tiene_archivo': bool(r.archivo_adjunto),
        'fecha_resultado': str(r.fecha_resultado) if r.fecha_resultado else None,
    }

def _resumen_antecedente(a):
    return {
        'paciente_id': a.paciente_id,
        'grupo_sanguineo': a.grupo_sanguineo or '',
        'tiene_alergias': bool(a.alergias),
    }

def _resumen_personal(ps):
    return {
        'username': ps.user.username if ps.user_id else '',
        'rol': ps.rol,
        'item_min_salud': ps.item_min_salud,
        'is_active': ps.is_active,
    }

def _resumen_consulta(c):
    return {
        'estado': c.estado,
        'codigo_cie10': c.codigo_cie10_principal or '',
    }

def _resumen_triaje(t):
    return {
        'nivel': getattr(t, 'nivel', ''),
        'ficha_id': getattr(t, 'ficha_id', None),
    }

def _resumen_receta(r):
    return {
        'estado': getattr(r, 'estado', ''),
        'consulta_id': getattr(r, 'consulta_id', None),
    }


# ═══════════════════════════════════════════════════════════════════════════
# PACIENTE
# ═══════════════════════════════════════════════════════════════════════════

@receiver(post_save, sender=Paciente)
def audit_paciente_save(sender, instance, created, **kwargs):
    registrar_evento(
        'CREATE' if created else 'UPDATE',
        instance,
        cambios=_resumen_paciente(instance),
    )

@receiver(pre_delete, sender=Paciente)
def audit_paciente_delete(sender, instance, **kwargs):
    registrar_evento('DELETE', instance, cambios=_resumen_paciente(instance))


# ═══════════════════════════════════════════════════════════════════════════
# FICHA DE ATENCIÓN
# ═══════════════════════════════════════════════════════════════════════════

@receiver(post_save, sender=Ficha)
def audit_ficha_save(sender, instance, created, **kwargs):
    registrar_evento(
        'CREATE' if created else 'UPDATE',
        instance,
        cambios=_resumen_ficha(instance),
    )

@receiver(pre_delete, sender=Ficha)
def audit_ficha_delete(sender, instance, **kwargs):
    registrar_evento('DELETE', instance, cambios=_resumen_ficha(instance))


# ═══════════════════════════════════════════════════════════════════════════
# ORDEN DE ESTUDIO
# ═══════════════════════════════════════════════════════════════════════════

@receiver(post_save, sender=OrdenEstudio)
def audit_orden_save(sender, instance, created, **kwargs):
    registrar_evento(
        'CREATE' if created else 'UPDATE',
        instance,
        cambios=_resumen_orden(instance),
    )

@receiver(pre_delete, sender=OrdenEstudio)
def audit_orden_delete(sender, instance, **kwargs):
    registrar_evento('DELETE', instance, cambios=_resumen_orden(instance))


# ═══════════════════════════════════════════════════════════════════════════
# RESULTADO DE ESTUDIO
# ═══════════════════════════════════════════════════════════════════════════

@receiver(post_save, sender=ResultadoEstudio)
def audit_resultado_save(sender, instance, created, **kwargs):
    registrar_evento(
        'CREATE' if created else 'UPDATE',
        instance,
        cambios=_resumen_resultado(instance),
    )


# ═══════════════════════════════════════════════════════════════════════════
# ANTECEDENTE MÉDICO
# ═══════════════════════════════════════════════════════════════════════════

@receiver(post_save, sender=Antecedente)
def audit_antecedente_save(sender, instance, created, **kwargs):
    # Los antecedentes se auto-crean vacíos al registrar un paciente.
    # Solo auditamos UPDATE (cuando el médico los edita realmente).
    if not created:
        registrar_evento('UPDATE', instance, cambios=_resumen_antecedente(instance))


# ═══════════════════════════════════════════════════════════════════════════
# PERSONAL DE SALUD
# ═══════════════════════════════════════════════════════════════════════════

@receiver(post_save, sender=PersonalSalud)
def audit_personal_save(sender, instance, created, **kwargs):
    registrar_evento(
        'CREATE' if created else 'UPDATE',
        instance,
        cambios=_resumen_personal(instance),
    )

@receiver(pre_delete, sender=PersonalSalud)
def audit_personal_delete(sender, instance, **kwargs):
    registrar_evento('DELETE', instance, cambios=_resumen_personal(instance))


# ═══════════════════════════════════════════════════════════════════════════
# CONSULTA MÉDICA SOAP (ya existía, mejoro con cambios)
# ═══════════════════════════════════════════════════════════════════════════

@receiver(post_save, sender=Consulta)
def audit_consulta_save(sender, instance, created, **kwargs):
    registrar_evento(
        'CREATE' if created else 'UPDATE',
        instance,
        cambios=_resumen_consulta(instance),
    )

@receiver(pre_delete, sender=Consulta)
def audit_consulta_delete(sender, instance, **kwargs):
    registrar_evento('DELETE', instance, cambios=_resumen_consulta(instance))


# ═══════════════════════════════════════════════════════════════════════════
# TRIAJE (ya existía)
# ═══════════════════════════════════════════════════════════════════════════

@receiver(post_save, sender=Triaje)
def audit_triaje_save(sender, instance, created, **kwargs):
    registrar_evento(
        'CREATE' if created else 'UPDATE',
        instance,
        cambios=_resumen_triaje(instance),
    )

@receiver(pre_delete, sender=Triaje)
def audit_triaje_delete(sender, instance, **kwargs):
    registrar_evento('DELETE', instance, cambios=_resumen_triaje(instance))


# ═══════════════════════════════════════════════════════════════════════════
# RECETA (ya existía)
# ═══════════════════════════════════════════════════════════════════════════

@receiver(post_save, sender=Receta)
def audit_receta_save(sender, instance, created, **kwargs):
    registrar_evento(
        'CREATE' if created else 'UPDATE',
        instance,
        cambios=_resumen_receta(instance),
    )

@receiver(pre_delete, sender=Receta)
def audit_receta_delete(sender, instance, **kwargs):
    registrar_evento('DELETE', instance, cambios=_resumen_receta(instance))
