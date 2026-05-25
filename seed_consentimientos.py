import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kardex.settings')
django.setup()

from Tenants.models import Tenant
from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente
from IA_Blockchain.ConfiguracionDeConsentimiento.models import TipoConsentimiento, Consentimiento
from django.contrib.auth.models import User
from django.utils import timezone

def seed():
    paciente = Paciente.objects.first()
    if not paciente:
        print("Error: No hay pacientes en la base de datos.")
        return

    user = User.objects.filter(is_superuser=True).first() or User.objects.first()
    if not user:
        print("Error: No hay usuarios en la base de datos.")
        return

    for tenant in Tenant.objects.all():
        print(f"Poblando tenant: {tenant.nombre} (ID: {tenant.id})")
        
        # Crear Tipos
        t1, _ = TipoConsentimiento.objects.get_or_create(
            tenant=tenant,
            nombre="Consentimiento Quirúrgico",
            defaults={"descripcion": "Autorización para procedimientos quirúrgicos generales.", "requiere_testigo": True}
        )
        t2, _ = TipoConsentimiento.objects.get_or_create(
            tenant=tenant,
            nombre="Uso de Datos Clínicos",
            defaults={"descripcion": "Permiso para utilizar datos anonimizados en investigación.", "requiere_testigo": False}
        )

        # Crear Consentimientos (solo si no existen)
        if not Consentimiento.objects.filter(tenant=tenant, paciente=paciente, tipo=t1).exists():
            Consentimiento.objects.create(
                tenant=tenant,
                paciente=paciente,
                tipo=t1,
                estado='OTORGADO',
                registrado_por=user,
                testigo_nombre="Dr. Testigo Ejemplo",
                observaciones=f"Paciente firma en {tenant.nombre}."
            )
        
        if not Consentimiento.objects.filter(tenant=tenant, paciente=paciente, tipo=t2).exists():
            Consentimiento.objects.create(
                tenant=tenant,
                paciente=paciente,
                tipo=t2,
                estado='OTORGADO',
                registrado_por=user,
                vigente_hasta=timezone.now() + timezone.timedelta(days=365),
                observaciones="Aceptado durante el registro inicial."
            )

    print(f"Seed completado. Tipos totales: {TipoConsentimiento.objects.count()}, Consentimientos totales: {Consentimiento.objects.count()}")

if __name__ == "__main__":
    seed()
