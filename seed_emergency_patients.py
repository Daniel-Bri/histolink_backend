import os
import django
import sys
from datetime import date

# Configurar entorno Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kardex.settings')
django.setup()

from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente
from Tenants.models import Tenant

from IA_Blockchain.ConfiguracionDeConsentimiento.models import TipoConsentimiento, Consentimiento

def seed_emergency_patients():
    print("Iniciando seed de pacientes y tipos para consentimiento de emergencia...")
    
    # Obtener el primer tenant disponible
    tenant = Tenant.objects.first()
    if not tenant:
        print("Error: No se encontró ningún Establecimiento (Tenant) en la base de datos.")
        return

    # Crear Tipo de Consentimiento de Emergencia si no existe
    tipo_emergencia, created_tipo = TipoConsentimiento.objects.get_or_create(
        tenant=tenant,
        nombre="Consentimiento de Emergencia",
        defaults={
            "descripcion": "Utilizado en casos de urgencia vital donde el paciente no puede expresar su voluntad.",
            "requiere_testigo": True,
            "activo": True
        }
    )
    if created_tipo:
        print("Tipo 'Consentimiento de Emergencia' creado.")

    patients_to_create = [
        {
            "ci": "49593002",
            "nombres": "Lorena",
            "apellido_paterno": "García",
            "apellido_materno": "Rocha",
            "fecha_nacimiento": date(2000, 5, 15), # 26 años aprox en 2026
            "sexo": "F"
        },
        {
            "ci": "3001003",
            "nombres": "Roberto",
            "apellido_paterno": "Chavez",
            "apellido_materno": "Inca",
            "fecha_nacimiento": date(1976, 8, 20), # 50 años en 2026
            "sexo": "M"
        },
        {
            "ci": "3001002",
            "nombres": "Maria Elena",
            "apellido_paterno": "Torres",
            "apellido_materno": "Vargas",
            "fecha_nacimiento": date(1959, 3, 10), # 67 años en 2026
            "sexo": "F"
        },
        {
            "ci": "3001001",
            "nombres": "Juan Carlos",
            "apellido_paterno": "Perez",
            "apellido_materno": "Soria",
            "fecha_nacimiento": date(1961, 11, 5), # 65 años en 2026
            "sexo": "M"
        }
    ]

    for p_data in patients_to_create:
        paciente, created = Paciente.objects.update_or_create(
            ci=p_data["ci"],
            tenant=tenant,
            defaults={
                "nombres": p_data["nombres"],
                "apellido_paterno": p_data["apellido_paterno"],
                "apellido_materno": p_data["apellido_materno"],
                "fecha_nacimiento": p_data["fecha_nacimiento"],
                "sexo": p_data["sexo"],
                "direccion": "Dirección registrada para emergencias",
                "tipo_seguro": "SUS"
            }
        )
        status = "creado" if created else "actualizado"
        print(f"Paciente {paciente.nombres} {paciente.apellido_paterno} (CI: {paciente.ci}) {status}.")

    print("\n✅ Seed completado con éxito.")

if __name__ == "__main__":
    seed_emergency_patients()
