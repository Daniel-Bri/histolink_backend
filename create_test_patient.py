import os
import django
import sys

# Configurar entorno Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kardex.settings')
django.setup()

from django.contrib.auth import get_user_model
from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente
from AtencionClinica.AperturaFichaYColaDeAtencion.models import Ficha
from AtencionClinica.RegistroDeTriaje.models import Triaje
from Tenants.models import Establecimiento

User = get_user_model()

def create_test_data():
    print("Iniciando creación de datos reales para prueba...")
    
    # 1. Obtener Tenant (Establecimiento)
    tenant = Establecimiento.objects.first()
    if not tenant:
        print("Error: No hay establecimientos creados.")
        return

    # 2. Obtener Médico
    medico = User.objects.filter(groups__name='Médico').first()
    if not medico:
        print("Error: No hay usuarios en el grupo 'Médico'.")
        return

    # Datos de pacientes a crear
    pacientes_data = [
        {"ci": "1234567", "nombres": "Juan", "apellidos": "Pérez Test", "sexo": "M", "motivo": "Dolor abdominal fuerte"},
        {"ci": "8888888", "nombres": "María", "apellidos": "García López", "sexo": "F", "motivo": "Fiebre persistente y tos"},
        {"ci": "9999999", "nombres": "Ricardo", "apellidos": "Suárez", "sexo": "M", "motivo": "Control post-operatorio"},
    ]

    for p_data in pacientes_data:
        # 3. Crear Paciente
        paciente, _ = Paciente.objects.get_or_create(
            ci=p_data["ci"],
            tenant=tenant,
            defaults={
                "nombres": p_data["nombres"],
                "apellidos": p_data["apellidos"],
                "fecha_nacimiento": "1990-05-15",
                "sexo": p_data["sexo"],
                "celular": "77788899",
                "direccion": "Av. Principal #123"
            }
        )
        print(f"Paciente: {paciente.nombre_completo}")

        # 4. Crear Ficha
        ficha = Ficha.objects.create(
            paciente=paciente,
            profesional_apertura=medico,
            tenant=tenant,
            estado=Ficha.Estado.EN_TRIAJE,
            motivo_consulta_inicial=p_data["motivo"]
        )
        print(f"Ficha creada: {ficha.correlativo}")

        # 5. Crear Triaje
        Triaje.objects.create(
            ficha=ficha,
            tenant=tenant,
            profesional=medico,
            frecuencia_cardiaca=75 + (int(p_data["ci"]) % 10),
            frecuencia_respiratoria=16 + (int(p_data["ci"]) % 4),
            presion_arterial_sistolica=110 + (int(p_data["ci"]) % 20),
            presion_arterial_diastolica=70 + (int(p_data["ci"]) % 15),
            temperatura=36.5 + (int(p_data["ci"]) % 2),
            saturacion_oxigeno=95 + (int(p_data["ci"]) % 4),
            escala_dolor=int(p_data["ci"]) % 10,
            glasgow=15,
            nivel_urgencia="VERDE" if int(p_data["ci"]) % 2 == 0 else "AMARILLO"
        )
    
    print("\n✅ Se han generado 3 pacientes reales en la cola de espera.")

if __name__ == "__main__":
    create_test_data()
