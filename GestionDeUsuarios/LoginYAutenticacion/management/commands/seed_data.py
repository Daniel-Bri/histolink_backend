"""
GestionDeUsuarios/LoginYAutenticacion/management/commands/seed_data.py

Carga datos de prueba multitenant para Histolink.
Crea 3 establecimientos de salud independientes, cada uno con su propio
personal completo (Director, Medico, Enfermera, Administrativo, Laboratorio,
Farmacia, Auditor) y 6 pacientes con expediente clinico completo.

Uso:
    python manage.py seed_data
    python manage.py seed_data --limpiar   # Elimina datos del seed antes de recrear
"""

from datetime import date

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from AtencionClinica.AperturaFichaYColaDeAtencion.models import Ficha
from AtencionClinica.ConsultaMedicaSOAP.models import Consulta
from AtencionClinica.RegistroDeTriaje.models import Triaje
from GestionDeUsuarios.EdicionDeAntecedentesMedicos.models import Antecedente
from GestionDeUsuarios.GestionDePersonalDeSalud.models import Especialidad, PersonalSalud
from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente
from Tenants.models import Tenant


# ---------------------------------------------------------------------------
# DATOS DE LOS 3 ESTABLECIMIENTOS
# ---------------------------------------------------------------------------

CLINICAS = [

    # -- Clinica 1: Hospital Universitario San Pablo -------------------------
    {
        "tenant": {
            "nombre": "Hospital Universitario San Pablo",
            "slug":   "hospital-san-pablo",
            "nit":    "1001234567",
            "direccion": "Av. Montes 1500, La Paz",
            "telefono":  "2-2901234",
        },
        "especialidades": [
            "Cardiologia",
            "Medicina Interna",
            "Urgencias y Emergencias",
            "Neurologia",
            "Cirugia General",
        ],
        "personal": [
            {
                "username": "dir_sanpablo", "password": "12345678",
                "first_name": "Santiago", "last_name": "Aparicio Rojas",
                "email": "dir@sanpablo.test",
                "rol_grupo": "Director",
                "item_min_salud": "DIR-001", "rol": PersonalSalud.ROL_ADMIN,
                "especialidad": None,
            },
            {
                "username": "med_sanpablo", "password": "12345678",
                "first_name": "Carlos", "last_name": "Vidal Torrez",
                "email": "medico@sanpablo.test",
                "rol_grupo": "Médico",
                "item_min_salud": "MED-001", "rol": PersonalSalud.ROL_MEDICO,
                "especialidad": "Cardiologia",
            },
            {
                "username": "enf_sanpablo", "password": "12345678",
                "first_name": "Rosa", "last_name": "Quispe Mamani",
                "email": "enfermera@sanpablo.test",
                "rol_grupo": "Enfermera",
                "item_min_salud": "ENF-001", "rol": PersonalSalud.ROL_ENFERMERA,
                "especialidad": None,
            },
            {
                "username": "adm_sanpablo", "password": "12345678",
                "first_name": "Jorge", "last_name": "Mamani Flores",
                "email": "admin@sanpablo.test",
                "rol_grupo": "Administrativo",
                "item_min_salud": "ADM-001", "rol": PersonalSalud.ROL_ADMIN,
                "especialidad": None,
            },
            {
                "username": "lab_sanpablo", "password": "12345678",
                "first_name": "Natalia", "last_name": "Cespedes Huanca",
                "email": "laboratorio@sanpablo.test",
                "rol_grupo": "Laboratorio",
                "item_min_salud": "LAB-001", "rol": PersonalSalud.ROL_ADMIN,
                "especialidad": None,
            },
            {
                "username": "farm_sanpablo", "password": "12345678",
                "first_name": "Rodrigo", "last_name": "Aliaga Poma",
                "email": "farmacia@sanpablo.test",
                "rol_grupo": "Farmacia",
                "item_min_salud": "FAR-001", "rol": PersonalSalud.ROL_ADMIN,
                "especialidad": None,
            },
            {
                "username": "aud_sanpablo", "password": "12345678",
                "first_name": "Lorena", "last_name": "Vargas Ibañez",
                "email": "auditor@sanpablo.test",
                "rol_grupo": "Auditor",
                "item_min_salud": "AUD-001", "rol": PersonalSalud.ROL_ADMIN,
                "especialidad": None,
            },
        ],
        "pacientes": [
            {
                "ci": "3001001", "ci_complemento": "",
                "nombres": "Juan Carlos", "apellido_paterno": "Perez", "apellido_materno": "Soria",
                "fecha_nacimiento": date(1961, 4, 12), "sexo": "M",
                "autoidentificacion": "MESTIZO", "telefono": "71234001",
                "direccion": "Calle Murillo 234, La Paz",
                "tipo_seguro": "CNS", "numero_asegurado": "CNS-SP-001",
                "antecedentes": {
                    "grupo_sanguineo": "B+",
                    "alergias": "Ibuprofeno (ulcera peptica previa)",
                    "ant_patologicos": "Dislipidemia mixta desde 2018\nEx-tabaquismo (dejo en 2020)",
                    "ant_no_patologicos": "Ex tabaquista: 20 cig/dia por 25 anos. No alcohol.",
                    "ant_quirurgicos": "Herniorrafia inguinal derecha (2008)",
                    "ant_familiares": "Padre: IAM, fallecido a los 58 anos. Hermano: bypass coronario.",
                    "ant_gineco_obstetricos": "",
                    "medicacion_actual": "AAS 100mg/dia\nAtorvastina 40mg noche\nOmeprazol 20mg en ayunas",
                    "esquema_vacunacion": "Hepatitis B completo. Influenza anual. Neumococo (2023).",
                },
                "triajes": [
                    {
                        "peso_kg": "88.5", "talla_cm": "175.0",
                        "frecuencia_cardiaca": 104, "frecuencia_respiratoria": 22,
                        "presion_sistolica": 162, "presion_diastolica": 100,
                        "temperatura_celsius": "36.7", "saturacion_oxigeno": 95,
                        "escala_dolor": 8, "nivel_urgencia": "ROJO",
                        "motivo_consulta_triaje": "Dolor opresivo en pecho irradiado a brazo izquierdo con sudoracion fria. Inicio hace 1 hora.",
                        "observaciones": "Signos de alarma cardiovascular. ECG solicitado de inmediato. Notificado cardiologo de guardia.",
                    },
                ],
                "consultas": [
                    {
                        "estado": "FIRMADA",
                        "motivo_consulta": "Dolor toracico opresivo irradiado a brazo izquierdo con sudoracion fria de 1 hora de evolucion.",
                        "historia_enfermedad_actual": "Paciente masculino de 65 anos con dislipidemia y antecedente familiar de IAM precoz. Dolor precordial opresivo 8/10 de inicio brusco, irradiado a brazo izquierdo y mandibula, acompanado de diaforesis y nauseas. Toma AAS 100mg como medicacion habitual.",
                        "examen_fisico": "FC: 104 lpm. PA: 162/100 mmHg. FR: 22 rpm. SpO2: 95%. Paciente sudoroso, ansioso. Tonos cardiacos ritmicos sin soplos. ECG: elevacion del ST en V2-V5.",
                        "impresion_diagnostica": "Sindrome coronario agudo con elevacion del ST (SCACEST). IAM anterior.",
                        "codigo_cie10_principal": "I21.0",
                        "descripcion_cie10": "Infarto agudo de miocardio transmural de la pared anterior",
                        "plan_tratamiento": "1. AAS 300mg masticable STAT\n2. Clopidogrel 600mg VO STAT\n3. Heparina sodica IV segun peso\n4. Morfina 2-4mg IV SOS dolor\n5. Activacion de codigo infarto — cateterismo urgente",
                        "indicaciones_alta": "Derivado a UCI cardiologica para cateterismo urgente.",
                        "requiere_derivacion": True,
                        "derivacion_destino": "UCI Cardiologica — Piso 4",
                        "derivacion_motivo": "SCACEST confirmado por ECG. ICP primaria en 90 minutos.",
                    },
                ],
            },
            {
                "ci": "3001002", "ci_complemento": "",
                "nombres": "Maria Elena", "apellido_paterno": "Torres", "apellido_materno": "Vargas",
                "fecha_nacimiento": date(1958, 9, 3), "sexo": "F",
                "autoidentificacion": "AYMARA", "telefono": "71234002",
                "direccion": "Av. 6 de Agosto 567, La Paz",
                "tipo_seguro": "COSSMIL", "numero_asegurado": "COS-SP-002",
                "antecedentes": {
                    "grupo_sanguineo": "A+",
                    "alergias": "Sin alergias conocidas",
                    "ant_patologicos": "Insuficiencia cardiaca cronica (diagnosticada 2021)\nHipertension arterial desde 2015\nFibrilacion auricular desde 2022",
                    "ant_no_patologicos": "No fuma. No alcohol. Dieta hiposodica.",
                    "ant_quirurgicos": "Reemplazo valvular mitral (2021)",
                    "ant_familiares": "Madre con valvulopatia mitral. Hermana con HTA.",
                    "ant_gineco_obstetricos": "G3P3A0C0. Menopausia a los 52 anos.",
                    "medicacion_actual": "Enalapril 10mg c/12h\nFurosemida 40mg en ayunas\nWarfarina 5mg segun INR\nBisoprolol 5mg c/dia\nEspironolactona 25mg c/dia",
                    "esquema_vacunacion": "Influenza anual. Neumococo (2022). COVID-19 completo.",
                },
                "triajes": [
                    {
                        "peso_kg": "72.0", "talla_cm": "155.0",
                        "frecuencia_cardiaca": 96, "frecuencia_respiratoria": 24,
                        "presion_sistolica": 148, "presion_diastolica": 88,
                        "temperatura_celsius": "36.5", "saturacion_oxigeno": 92,
                        "escala_dolor": 5, "nivel_urgencia": "NARANJA",
                        "motivo_consulta_triaje": "Disnea progresiva de 3 dias. Edema en piernas. Refiere aumento de peso de 4kg en una semana.",
                        "observaciones": "SpO2 92%. Signos de descompensacion cardiaca. Posicion semisentada.",
                    },
                ],
                "consultas": [
                    {
                        "estado": "COMPLETADA",
                        "motivo_consulta": "Descompensacion de insuficiencia cardiaca cronica. Disnea y edema progresivos.",
                        "historia_enfermedad_actual": "Paciente de 68 anos con ICC cronica, HTA y FA acude por disnea de esfuerzo que progreso a reposo en 3 dias, con ortopnea (necesita 3 almohadas), edema bimaleolar que asciende hasta rodillas y ganancia de 4kg en 7 dias. Refiere no haber tomado furosemida los ultimos 2 dias por olvido.",
                        "examen_fisico": "FC: 96 lpm irregular (FA). PA: 148/88 mmHg. FR: 24 rpm. SpO2: 92%. Ingurgitacion yugular ++. Crepitantes bibasales. Edema con godete hasta rodilla bilateral.",
                        "impresion_diagnostica": "Insuficiencia cardiaca descompensada aguda por abandono de diuretico",
                        "codigo_cie10_principal": "I50.9",
                        "descripcion_cie10": "Insuficiencia cardiaca no especificada",
                        "plan_tratamiento": "1. Furosemida 80mg IV STAT\n2. O2 suplementario 2L/min por mascarilla\n3. Restriccion hidrica 1.5L/dia\n4. Pesaje diario\n5. Educacion sobre adherencia al tratamiento",
                        "indicaciones_alta": "Tomar furosemida sin omitir dosis. Pesar cada manana. Dieta hiposodica estricta. Acudir si aumenta mas de 2kg en 2 dias.",
                        "requiere_derivacion": False,
                    },
                ],
            },
            {
                "ci": "3001003", "ci_complemento": "",
                "nombres": "Roberto", "apellido_paterno": "Chavez", "apellido_materno": "Inca",
                "fecha_nacimiento": date(1975, 7, 19), "sexo": "M",
                "autoidentificacion": "QUECHUA", "telefono": "71234003",
                "direccion": "Calle Potosi 890, La Paz",
                "tipo_seguro": "SUS", "numero_asegurado": "",
                "antecedentes": {
                    "grupo_sanguineo": "O+",
                    "alergias": "Penicilina (erupcion cutanea)",
                    "ant_patologicos": "Hipertension arterial estadio 2 (diagnosticada 2020)\nDiabetes tipo 2 (2022)",
                    "ant_no_patologicos": "Tabaquismo activo: 15 cig/dia. Alcohol fin de semana.",
                    "ant_quirurgicos": "Ninguno",
                    "ant_familiares": "Padre con HTA. Madre con diabetes tipo 2.",
                    "ant_gineco_obstetricos": "",
                    "medicacion_actual": "Amlodipino 10mg c/dia\nLosartan 100mg c/dia\nMetformina 1000mg c/12h",
                    "esquema_vacunacion": "Influenza (2024). COVID-19 completo (2022).",
                },
                "triajes": [
                    {
                        "peso_kg": "95.0", "talla_cm": "170.0",
                        "frecuencia_cardiaca": 82, "frecuencia_respiratoria": 18,
                        "presion_sistolica": 178, "presion_diastolica": 108,
                        "temperatura_celsius": "36.4", "saturacion_oxigeno": 97,
                        "escala_dolor": 3, "nivel_urgencia": "AMARILLO",
                        "motivo_consulta_triaje": "Control de HTA y diabetes. Refiere cefalea occipital desde ayer. No ha tomado medicacion hoy.",
                        "observaciones": "PA muy elevada al ingreso. Pendiente revision de adherencia a tratamiento.",
                    },
                ],
                "consultas": [
                    {
                        "estado": "COMPLETADA",
                        "motivo_consulta": "HTA no controlada con cefalea occipital. Diabetes tipo 2 en control mensual.",
                        "historia_enfermedad_actual": "Paciente de 51 anos con HTA estadio 2 y DM2 acude por control mensual y cefalea occipital 3/10 desde ayer. Reconoce tabaquismo activo y dieta hipercalorica. PA en casa entre 160-170/100. Glucemias matutinas 180-220 mg/dL.",
                        "examen_fisico": "PA: 178/108 mmHg. FC: 82 lpm. Peso: 95kg. IMC: 32.9. Glucemia capilar: 198 mg/dL. Sin deficit neurologico focal.",
                        "impresion_diagnostica": "HTA estadio 2 no controlada. Diabetes tipo 2 con mal control glucemico. Obesidad grado 1.",
                        "codigo_cie10_principal": "I10",
                        "descripcion_cie10": "Hipertension esencial (primaria)",
                        "plan_tratamiento": "1. Intensificar Losartan a 100mg c/12h\n2. Agregar Hidroclorotiazida 25mg/dia\n3. Intensificar Metformina: agregar Glibenclamida 5mg c/12h\n4. Consejeria antitabaquica\n5. Control en 2 semanas con perfil lipidico y HbA1c",
                        "indicaciones_alta": "No omitir medicacion. Reducir sal y azucar. Urgente dejar de fumar. Dieta hipocalorica e hiposodica.",
                        "requiere_derivacion": False,
                    },
                ],
            },
            {
                "ci": "3001004", "ci_complemento": "",
                "nombres": "Andres", "apellido_paterno": "Salinas", "apellido_materno": "Paredes",
                "fecha_nacimiento": date(2016, 8, 5), "sexo": "M",
                "autoidentificacion": "MESTIZO", "telefono": "71234010",
                "direccion": "Av. Saavedra 345, La Paz",
                "tipo_seguro": "SUS", "numero_asegurado": "",
                "antecedentes": {
                    "grupo_sanguineo": "A+",
                    "alergias": "Sin alergias conocidas",
                    "ant_patologicos": "Sin antecedentes patologicos previos",
                    "ant_no_patologicos": "Escolares. Juega futbol.",
                    "ant_quirurgicos": "Ninguno",
                    "ant_familiares": "Sin antecedentes relevantes",
                    "ant_gineco_obstetricos": "",
                    "medicacion_actual": "Ninguna",
                    "esquema_vacunacion": "Esquema PAI completo para la edad.",
                },
                "triajes": [
                    {
                        "peso_kg": "28.0", "talla_cm": "122.0",
                        "frecuencia_cardiaca": 118, "frecuencia_respiratoria": 26,
                        "presion_sistolica": 98, "presion_diastolica": 60,
                        "temperatura_celsius": "39.2", "saturacion_oxigeno": 96,
                        "escala_dolor": 4, "nivel_urgencia": "AMARILLO",
                        "motivo_consulta_triaje": "Fiebre alta de 39.2 grados, tos productiva y dificultad para respirar desde hace 2 dias.",
                        "observaciones": "Nino febril con polipnea. Posible cuadro respiratorio bajo.",
                    },
                ],
                "consultas": [
                    {
                        "estado": "COMPLETADA",
                        "motivo_consulta": "Fiebre alta, tos productiva y taquipnea de 2 dias de evolucion en paciente pediatrico.",
                        "historia_enfermedad_actual": "Nino de 9 anos sin antecedentes patologicos acude por fiebre 39.2C de 2 dias de evolucion acompanada de tos productiva con expectoracion amarillenta, polipnea y malestar general. Inicio con rinorrea y estornudos hace 4 dias. Niega vomitos ni diarrea.",
                        "examen_fisico": "T: 39.2C. FC: 118 lpm. FR: 26 rpm. SpO2: 96%. Faringe moderadamente eritematosa. Auscultacion: crepitantes en base pulmonar derecha. Sin tiraje.",
                        "impresion_diagnostica": "Neumonia adquirida en la comunidad (NAC) de gravedad leve. Posible etiologia bacteriana.",
                        "codigo_cie10_principal": "J18.9",
                        "descripcion_cie10": "Neumonia no especificada",
                        "plan_tratamiento": "1. Amoxicilina-Clavulanato 40mg/kg/dia VO c/8h por 7 dias\n2. Ibuprofeno 10mg/kg c/6h SOS fiebre\n3. Nebulizacion con suero fisiologico c/8h\n4. Hidratacion oral abundante\n5. Rx torax de control en 48h si no mejora",
                        "indicaciones_alta": "Completar antibiotico 7 dias. Reposo escolar. Acudir de urgencia si aumenta dificultad respiratoria, cianosis o fiebre que no cede.",
                        "requiere_derivacion": False,
                    },
                ],
            },
            {
                "ci": "3001005", "ci_complemento": "",
                "nombres": "Beatriz", "apellido_paterno": "Huanca", "apellido_materno": "Rios",
                "fecha_nacimiento": date(1993, 3, 15), "sexo": "F",
                "autoidentificacion": "AYMARA", "telefono": "71234011",
                "direccion": "Calle Illampu 678, La Paz",
                "tipo_seguro": "CNS", "numero_asegurado": "CNS-SP-005",
                "antecedentes": {
                    "grupo_sanguineo": "O-",
                    "alergias": "Sin alergias conocidas",
                    "ant_patologicos": "Migranas cronicas desde 2015. Ansiedad generalizada.",
                    "ant_no_patologicos": "No fuma. No alcohol. Trabajo administrativo.",
                    "ant_quirurgicos": "Apendectomia (2012)",
                    "ant_familiares": "Madre con migranas. Padre con HTA.",
                    "ant_gineco_obstetricos": "G1P1A0C0. FUM: hace 3 semanas. MAC: anticonceptivos orales.",
                    "medicacion_actual": "Sumatriptan 50mg SOS migrana\nFluoxetina 20mg c/dia",
                    "esquema_vacunacion": "Esquema completo. Influenza (2024).",
                },
                "triajes": [
                    {
                        "peso_kg": "62.0", "talla_cm": "162.0",
                        "frecuencia_cardiaca": 88, "frecuencia_respiratoria": 18,
                        "presion_sistolica": 130, "presion_diastolica": 84,
                        "temperatura_celsius": "36.6", "saturacion_oxigeno": 98,
                        "escala_dolor": 7, "nivel_urgencia": "AMARILLO",
                        "motivo_consulta_triaje": "Cefalea pulsatil intensa unilateral con nauseas y fotofobia. No cede con sumatriptan habitual.",
                        "observaciones": "Crisis de migrana sin aura. Paciente con fotofobia marcada.",
                    },
                ],
                "consultas": [
                    {
                        "estado": "COMPLETADA",
                        "motivo_consulta": "Crisis de migrana sin aura refractaria a tratamiento habitual.",
                        "historia_enfermedad_actual": "Paciente de 33 anos con migranas cronicas acude por crisis de 6h de evolucion, cefalea pulsatil hemicraneal izquierda 7/10, con nauseas, fotofobia y fonofobia. Tomo sumatriptan 50mg hace 2h sin mejoria. Identifica el estres laboral como desencadenante.",
                        "examen_fisico": "Paciente en decubito, fotofobica. PA: 130/84 mmHg. FC: 88 lpm. Fondo de ojo: normal. Sin rigidez de nuca. Sin deficit neurologico focal.",
                        "impresion_diagnostica": "Migrana sin aura en crisis. Refractaria a triptanes.",
                        "codigo_cie10_principal": "G43.009",
                        "descripcion_cie10": "Migrana sin aura, no intratable",
                        "plan_tratamiento": "1. Ketorolaco 30mg IV dosis unica\n2. Metoclopramida 10mg IV antiemetico\n3. Dimmer de luz y ambiente tranquilo\n4. Si no mejora en 1h: Dexametasona 8mg IV\n5. Revisar profilaxis: considerar Amitriptilina 25mg noche",
                        "indicaciones_alta": "Reposo en lugar oscuro y tranquilo. Evitar estres. Profilaxis con neurologo. Acudir si cefalea en estallido o fiebre.",
                        "requiere_derivacion": True,
                        "derivacion_destino": "Neurologia — Hospital San Pablo",
                        "derivacion_motivo": "Migranas refractarias frecuentes. Requiere ajuste de profilaxis por especialista.",
                    },
                ],
            },
            {
                "ci": "3001006", "ci_complemento": "",
                "nombres": "Alfredo", "apellido_paterno": "Mendoza", "apellido_materno": "Aguilar",
                "fecha_nacimiento": date(1945, 11, 30), "sexo": "M",
                "autoidentificacion": "MESTIZO", "telefono": "71234012",
                "direccion": "Av. Arce 1100, La Paz",
                "tipo_seguro": "COSSMIL", "numero_asegurado": "COS-SP-006",
                "antecedentes": {
                    "grupo_sanguineo": "AB-",
                    "alergias": "Contraste yodado (urticaria)",
                    "ant_patologicos": "ACV isquemico (2021) con secuela de hemiparesia derecha leve\nFibrilacion auricular cronica\nHipertension arterial desde 2010",
                    "ant_no_patologicos": "Ex-fumador (dejo 2010). No alcohol.",
                    "ant_quirurgicos": "Ninguno",
                    "ant_familiares": "Hermano con ACV a los 70 anos.",
                    "ant_gineco_obstetricos": "",
                    "medicacion_actual": "Warfarina 3mg segun INR\nAmlodipino 10mg c/dia\nAtorvastina 40mg noche\nRivaroxaban 20mg con la cena",
                    "esquema_vacunacion": "Influenza anual. Neumococo (2022). COVID-19 completo.",
                },
                "triajes": [
                    {
                        "peso_kg": "78.0", "talla_cm": "168.0",
                        "frecuencia_cardiaca": 72, "frecuencia_respiratoria": 17,
                        "presion_sistolica": 144, "presion_diastolica": 86,
                        "temperatura_celsius": "36.4", "saturacion_oxigeno": 97,
                        "escala_dolor": 1, "nivel_urgencia": "VERDE",
                        "motivo_consulta_triaje": "Control de anticoagulacion. Trae INR de control: 1.6 (subterapeutico).",
                        "observaciones": "INR fuera de rango terapeutico. Riesgo trombotico aumentado. Requiere ajuste de warfarina.",
                    },
                ],
                "consultas": [
                    {
                        "estado": "COMPLETADA",
                        "motivo_consulta": "Control de anticoagulacion. INR 1.6, subterapeutico. Paciente post-ACV con FA cronica.",
                        "historia_enfermedad_actual": "Paciente de 81 anos con ACV isquemico previo y FA cronica en anticoagulacion con warfarina. Trae INR 1.6 (objetivo 2.0-3.0). Niega sangrados. Refiere que no cambio dieta ni medicamentos. Cumple tratamiento segun su relato.",
                        "examen_fisico": "PA: 144/86 mmHg. FC: 72 lpm irregular (FA). Peso: 78kg. Hemiparesia derecha residual leve estable. Sin signos de sangrado activo.",
                        "impresion_diagnostica": "Anticoagulacion subterapeutica. FA cronica con ACV previo. Control de dosis de warfarina.",
                        "codigo_cie10_principal": "I48.91",
                        "descripcion_cie10": "Fibrilacion auricular no especificada, cronica",
                        "plan_tratamiento": "1. Aumentar Warfarina a 4mg/dia por 5 dias\n2. Control de INR en 7 dias\n3. Mantener Amlodipino y Atorvastina\n4. Educar sobre dieta con vitamina K estable\n5. Coordinar con hematologia si INR persiste fuera de rango",
                        "indicaciones_alta": "No cambiar dieta bruscamente. No omitir warfarina. INR en 7 dias. Acudir de urgencia si cefalea intensa, debilidad unilateral o sangrado.",
                        "requiere_derivacion": False,
                    },
                ],
            },
        ],
    },

    # -- Clinica 2: Centro de Salud Norte ------------------------------------
    {
        "tenant": {
            "nombre": "Centro de Salud Norte",
            "slug":   "centro-salud-norte",
            "nit":    "1009876543",
            "direccion": "Av. Villazon 450, Cochabamba",
            "telefono":  "4-4567890",
        },
        "especialidades": [
            "Medicina General",
            "Pediatria",
            "Ginecologia y Obstetricia",
        ],
        "personal": [
            {
                "username": "dir_cnorte", "password": "12345678",
                "first_name": "Elena", "last_name": "Vargas Ponce",
                "email": "directora@cnorte.test",
                "rol_grupo": "Director",
                "item_min_salud": "DIR-001", "rol": PersonalSalud.ROL_ADMIN,
                "especialidad": None,
            },
            {
                "username": "med_cnorte", "password": "12345678",
                "first_name": "Luis", "last_name": "Rojas Heredia",
                "email": "medico@cnorte.test",
                "rol_grupo": "Médico",
                "item_min_salud": "MED-001", "rol": PersonalSalud.ROL_MEDICO,
                "especialidad": "Medicina General",
            },
            {
                "username": "enf_cnorte", "password": "12345678",
                "first_name": "Carmen", "last_name": "Flores Huanca",
                "email": "enfermera@cnorte.test",
                "rol_grupo": "Enfermera",
                "item_min_salud": "ENF-001", "rol": PersonalSalud.ROL_ENFERMERA,
                "especialidad": None,
            },
            {
                "username": "adm_cnorte", "password": "12345678",
                "first_name": "Wilfredo", "last_name": "Cabrera Torrez",
                "email": "admin@cnorte.test",
                "rol_grupo": "Administrativo",
                "item_min_salud": "ADM-001", "rol": PersonalSalud.ROL_ADMIN,
                "especialidad": None,
            },
            {
                "username": "lab_cnorte", "password": "12345678",
                "first_name": "Daniela", "last_name": "Quispe Soria",
                "email": "laboratorio@cnorte.test",
                "rol_grupo": "Laboratorio",
                "item_min_salud": "LAB-001", "rol": PersonalSalud.ROL_ADMIN,
                "especialidad": None,
            },
            {
                "username": "farm_cnorte", "password": "12345678",
                "first_name": "Ivan", "last_name": "Mamani Copa",
                "email": "farmacia@cnorte.test",
                "rol_grupo": "Farmacia",
                "item_min_salud": "FAR-001", "rol": PersonalSalud.ROL_ADMIN,
                "especialidad": None,
            },
            {
                "username": "aud_cnorte", "password": "12345678",
                "first_name": "Miriam", "last_name": "Zenteno Paz",
                "email": "auditor@cnorte.test",
                "rol_grupo": "Auditor",
                "item_min_salud": "AUD-001", "rol": PersonalSalud.ROL_ADMIN,
                "especialidad": None,
            },
        ],
        "pacientes": [
            {
                "ci": "3002001", "ci_complemento": "",
                "nombres": "Sandra Patricia", "apellido_paterno": "Quispe", "apellido_materno": "Condori",
                "fecha_nacimiento": date(1978, 2, 14), "sexo": "F",
                "autoidentificacion": "AYMARA", "telefono": "71234004",
                "direccion": "Calle Sucre 123, Cochabamba",
                "tipo_seguro": "SUS", "numero_asegurado": "",
                "antecedentes": {
                    "grupo_sanguineo": "A-",
                    "alergias": "Sin alergias conocidas",
                    "ant_patologicos": "Diabetes mellitus tipo 2 diagnosticada en 2019\nSobrepeso desde 2015",
                    "ant_no_patologicos": "No fuma. No alcohol. Sedentaria.",
                    "ant_quirurgicos": "Cesarea (2005)",
                    "ant_familiares": "Madre con diabetes tipo 2. Abuela con misma condicion.",
                    "ant_gineco_obstetricos": "G2P1A0C1. Menarquia a los 13 anos. Ciclos regulares.",
                    "medicacion_actual": "Metformina 850mg c/12h\nGlibenclamida 5mg en desayuno",
                    "esquema_vacunacion": "Esquema completo. Influenza (2024). COVID-19 completo.",
                },
                "triajes": [
                    {
                        "peso_kg": "82.0", "talla_cm": "158.0",
                        "frecuencia_cardiaca": 78, "frecuencia_respiratoria": 16,
                        "presion_sistolica": 128, "presion_diastolica": 82,
                        "temperatura_celsius": "36.6", "saturacion_oxigeno": 98,
                        "escala_dolor": 1, "nivel_urgencia": "VERDE",
                        "motivo_consulta_triaje": "Control mensual de diabetes. Trae resultados de glucosa en ayunas.",
                        "observaciones": "Paciente estable. Glicemia en ayunas: 142 mg/dL segun resultado.",
                    },
                ],
                "consultas": [
                    {
                        "estado": "COMPLETADA",
                        "motivo_consulta": "Control mensual de diabetes tipo 2. Trae HbA1c y perfil lipidico.",
                        "historia_enfermedad_actual": "Paciente de 48 anos con DM2 acude a control mensual. Refiere glucemias en casa entre 130-160 mg/dL en ayunas. Buena adherencia a medicacion. Niega hipoglicemias. Sin cambios en vision ni parestesias.",
                        "examen_fisico": "PA: 128/82 mmHg. FC: 78 lpm. Peso: 82kg. IMC: 32.8. Glucemia capilar: 142 mg/dL. Examen de pies: sin lesiones, pulsos presentes.",
                        "impresion_diagnostica": "Diabetes mellitus tipo 2 con control glicemico parcial. Sobrepeso.",
                        "codigo_cie10_principal": "E11.9",
                        "descripcion_cie10": "Diabetes mellitus tipo 2 sin complicaciones",
                        "plan_tratamiento": "1. Mantener Metformina 850mg c/12h\n2. Ajustar Glibenclamida a 5mg c/12h\n3. Derivar a nutricion para plan alimentario\n4. Solicitar microalbuminuria y creatinina\n5. Control en 30 dias con nueva HbA1c",
                        "indicaciones_alta": "Continuar medicacion sin omitir dosis. Dieta hipocalorica. Caminar 30 minutos al dia. Cuidado de pies.",
                        "requiere_derivacion": True,
                        "derivacion_destino": "Nutricion — Centro de Salud Norte",
                        "derivacion_motivo": "Sobrepeso grado 1 que dificulta control glucemico. Plan nutricional personalizado.",
                    },
                ],
            },
            {
                "ci": "3002002", "ci_complemento": "",
                "nombres": "Marco Antonio", "apellido_paterno": "Choque", "apellido_materno": "Lima",
                "fecha_nacimiento": date(1990, 11, 5), "sexo": "M",
                "autoidentificacion": "MESTIZO", "telefono": "71234005",
                "direccion": "Av. Blanco Galindo 78, Cochabamba",
                "tipo_seguro": "PARTICULAR", "numero_asegurado": "",
                "antecedentes": {
                    "grupo_sanguineo": "O+",
                    "alergias": "Sin alergias conocidas",
                    "ant_patologicos": "Sin antecedentes patologicos de importancia",
                    "ant_no_patologicos": "Fumador ocasional (fines de semana). No alcohol.",
                    "ant_quirurgicos": "Ninguno",
                    "ant_familiares": "Sin antecedentes familiares relevantes",
                    "ant_gineco_obstetricos": "",
                    "medicacion_actual": "Ninguna",
                    "esquema_vacunacion": "Esquema completo de la infancia. COVID-19 completo.",
                },
                "triajes": [
                    {
                        "peso_kg": "74.0", "talla_cm": "172.0",
                        "frecuencia_cardiaca": 90, "frecuencia_respiratoria": 20,
                        "presion_sistolica": 118, "presion_diastolica": 74,
                        "temperatura_celsius": "38.4", "saturacion_oxigeno": 97,
                        "escala_dolor": 4, "nivel_urgencia": "VERDE",
                        "motivo_consulta_triaje": "Fiebre de 38.4 C, dolor de garganta y congestion nasal desde hace 2 dias. Tos seca.",
                        "observaciones": "Febril al ingreso. Sin dificultad respiratoria evidente.",
                    },
                ],
                "consultas": [
                    {
                        "estado": "COMPLETADA",
                        "motivo_consulta": "Cuadro febril con odinofagia y congestion nasal de 2 dias de evolucion.",
                        "historia_enfermedad_actual": "Paciente de 36 anos previamente sano consulta por fiebre 38.4C de inicio hace 48h, acompanada de odinofagia intensa, congestion nasal, tos seca y malestar general. Niega dificultad para respirar, dolor de oido o erupcion cutanea.",
                        "examen_fisico": "T: 38.4C. FC: 90 lpm. FR: 20 rpm. SpO2: 97%. Faringe: eritematosa con exudado blanquecino bilateral. Amigdalas hipertroficas. Adenopatias cervicales anteriores dolorosas. Otoscopia normal.",
                        "impresion_diagnostica": "Faringoamigdalitis bacteriana aguda (probable Streptococcus pyogenes)",
                        "codigo_cie10_principal": "J02.0",
                        "descripcion_cie10": "Faringitis estreptococica",
                        "plan_tratamiento": "1. Amoxicilina 500mg c/8h por 10 dias\n2. Ibuprofeno 400mg c/8h SOS fiebre y dolor\n3. Gargara con agua tibia con sal\n4. Abundante hidratacion\n5. Reposo relativo 48-72h",
                        "indicaciones_alta": "Completar los 10 dias de antibiotico aunque mejore antes. Acudir si: dificultad para respirar, incapacidad de tragar liquidos o fiebre que no cede.",
                        "requiere_derivacion": False,
                    },
                ],
            },
            {
                "ci": "3002003", "ci_complemento": "",
                "nombres": "Patricia Rosario", "apellido_paterno": "Lima", "apellido_materno": "Vega",
                "fecha_nacimiento": date(1985, 6, 28), "sexo": "F",
                "autoidentificacion": "MESTIZO", "telefono": "71234006",
                "direccion": "Calle Baptista 320, Cochabamba",
                "tipo_seguro": "CNS", "numero_asegurado": "CNS-CN-003",
                "antecedentes": {
                    "grupo_sanguineo": "B-",
                    "alergias": "Sin alergias conocidas",
                    "ant_patologicos": "Lumbalgia mecanica cronica desde 2020 (trabajo sedentario)",
                    "ant_no_patologicos": "No fuma. No alcohol. Trabajo de oficina 8h/dia.",
                    "ant_quirurgicos": "Ninguno",
                    "ant_familiares": "Padre con lumboartrosis",
                    "ant_gineco_obstetricos": "G1P1A0C0. MAC: dispositivo intrauterino (DIU).",
                    "medicacion_actual": "Ibuprofeno 400mg SOS lumbalgia",
                    "esquema_vacunacion": "Esquema completo. Influenza (2024).",
                },
                "triajes": [
                    {
                        "peso_kg": "65.0", "talla_cm": "163.0",
                        "frecuencia_cardiaca": 72, "frecuencia_respiratoria": 16,
                        "presion_sistolica": 120, "presion_diastolica": 78,
                        "temperatura_celsius": "36.3", "saturacion_oxigeno": 99,
                        "escala_dolor": 6, "nivel_urgencia": "VERDE",
                        "motivo_consulta_triaje": "Dolor lumbar intensificado desde hace 3 dias. No puede agacharse ni levantarse sin dolor.",
                        "observaciones": "Paciente en posicion antalgica. Refiere que el dolor no mejora con ibuprofeno habitual.",
                    },
                ],
                "consultas": [
                    {
                        "estado": "COMPLETADA",
                        "motivo_consulta": "Lumbalgia aguda sobre cronica. Limitacion funcional importante por 3 dias.",
                        "historia_enfermedad_actual": "Paciente de 41 anos con lumbalgia mecanica cronica de 4 anos de evolucion acude por agudizacion hace 3 dias tras cargar objetos pesados en mudanza. Dolor lumbar 6/10 en reposo, 9/10 al moverse. No irradia a miembros inferiores. Sin parestesias ni alteracion de esfinteres.",
                        "examen_fisico": "Postura antalgica en flexion. Contractura paravertebral L3-S1 bilateral. Lasegue negativo bilateral. Sin deficit sensitivo ni motor. Fuerza conservada en miembros inferiores.",
                        "impresion_diagnostica": "Lumbalgia aguda de tipo mecanico sobre cronica. Sin signos de alarma.",
                        "codigo_cie10_principal": "M54.5",
                        "descripcion_cie10": "Lumbalgia baja",
                        "plan_tratamiento": "1. Naproxeno 500mg c/12h con comida por 7 dias\n2. Ciclobenzaprina 5mg en la noche por 5 dias\n3. Calor local 20 min c/8h\n4. Reposo relativo (evitar carga)\n5. Derivar a fisioterapia para fortalecimiento lumbar",
                        "indicaciones_alta": "Evitar cargas pesadas. Calor local. Si aparece dolor en pierna, parestesias o problemas para orinar, acudir de urgencia.",
                        "requiere_derivacion": True,
                        "derivacion_destino": "Fisioterapia — Centro de Salud Norte",
                        "derivacion_motivo": "Lumbalgia mecanica cronica con agudizaciones frecuentes. Requiere fortalecimiento muscular.",
                    },
                ],
            },
            {
                "ci": "3002004", "ci_complemento": "",
                "nombres": "Gabriela", "apellido_paterno": "Montano", "apellido_materno": "Herrera",
                "fecha_nacimiento": date(1998, 7, 22), "sexo": "F",
                "autoidentificacion": "MESTIZO", "telefono": "71234013",
                "direccion": "Av. America 890, Cochabamba",
                "tipo_seguro": "SUS", "numero_asegurado": "",
                "antecedentes": {
                    "grupo_sanguineo": "A+",
                    "alergias": "Sin alergias conocidas",
                    "ant_patologicos": "Sin antecedentes patologicos previos",
                    "ant_no_patologicos": "No fuma. No alcohol.",
                    "ant_quirurgicos": "Ninguno",
                    "ant_familiares": "Sin antecedentes relevantes",
                    "ant_gineco_obstetricos": "G1P0A0C0. Gesta de 28 semanas. FUM: hace 7 meses. CPN regulares.",
                    "medicacion_actual": "Acido folico 5mg c/dia\nFerro sulfato 300mg c/dia\nCalcio 500mg c/12h",
                    "esquema_vacunacion": "Esquema completo. Vacuna antitetanica (gestacion). Influenza (2024).",
                },
                "triajes": [
                    {
                        "peso_kg": "72.0", "talla_cm": "165.0",
                        "frecuencia_cardiaca": 88, "frecuencia_respiratoria": 18,
                        "presion_sistolica": 136, "presion_diastolica": 88,
                        "temperatura_celsius": "36.5", "saturacion_oxigeno": 98,
                        "escala_dolor": 2, "nivel_urgencia": "AMARILLO",
                        "motivo_consulta_triaje": "Control prenatal de 28 semanas. Refiere edema en pies y PA ligeramente elevada en su casa (140/90).",
                        "observaciones": "Embarazada de 28 semanas. PA 136/88 al ingreso. Revisar signos de preeclampsia.",
                    },
                ],
                "consultas": [
                    {
                        "estado": "COMPLETADA",
                        "motivo_consulta": "Control prenatal 28 semanas. Hipertension gestacional emergente. Edema de miembros inferiores.",
                        "historia_enfermedad_actual": "Paciente primigestante de 28 anos, 28 semanas de gestacion, acude por control prenatal rutinario. Refiere PA en casa 140/90 en 2 ocasiones. Edema en tobillos desde hace 1 semana. Niega cefalea intensa, vision borrosa, epigastralgia o escotomas.",
                        "examen_fisico": "PA: 136/88 mmHg (repetida: 138/90). FC: 88 lpm. Peso: 72kg (+2kg en 2 semanas). Edema grado 1 en miembros inferiores. FCF: 148 lpm regular. Altura uterina: 28cm acorde a EG.",
                        "impresion_diagnostica": "Hipertension gestacional. Descartar preeclampsia. Feto con FCF normal.",
                        "codigo_cie10_principal": "O13",
                        "descripcion_cie10": "Hipertension gestacional sin proteinuria significativa",
                        "plan_tratamiento": "1. Solicitar orina completa y proteinuria en 24h\n2. Solicitar hemograma, creatinina, acido urico, transaminasas\n3. Reposo relativo en decubito lateral izquierdo\n4. Control de PA cada 6h\n5. Si PA > 150/100: iniciar Metildopa 500mg c/8h",
                        "indicaciones_alta": "Reposo. Control PA en casa 2 veces al dia. Acudir de urgencia si cefalea intensa, vision borrosa o dolor en epigastrio. Control en 3 dias.",
                        "requiere_derivacion": True,
                        "derivacion_destino": "Alto Riesgo Obstetrico — Centro de Salud Norte",
                        "derivacion_motivo": "Hipertension gestacional en semana 28 con riesgo de preeclampsia.",
                    },
                ],
            },
            {
                "ci": "3002005", "ci_complemento": "",
                "nombres": "Kevin Daniel", "apellido_paterno": "Aguilera", "apellido_materno": "Solis",
                "fecha_nacimiento": date(2020, 4, 10), "sexo": "M",
                "autoidentificacion": "MESTIZO", "telefono": "71234014",
                "direccion": "Calle Lanza 456, Cochabamba",
                "tipo_seguro": "SUS", "numero_asegurado": "",
                "antecedentes": {
                    "grupo_sanguineo": "B+",
                    "alergias": "Sin alergias conocidas",
                    "ant_patologicos": "Sin antecedentes patologicos previos",
                    "ant_no_patologicos": "Lactante mayor. Alimentacion mixta.",
                    "ant_quirurgicos": "Ninguno",
                    "ant_familiares": "Sin antecedentes relevantes",
                    "ant_gineco_obstetricos": "",
                    "medicacion_actual": "Ninguna",
                    "esquema_vacunacion": "Esquema PAI incompleto: pendiente 4ta dosis pentavalente.",
                },
                "triajes": [
                    {
                        "peso_kg": "11.5", "talla_cm": "80.0",
                        "frecuencia_cardiaca": 140, "frecuencia_respiratoria": 48,
                        "presion_sistolica": 90, "presion_diastolica": 60,
                        "temperatura_celsius": "38.1", "saturacion_oxigeno": 93,
                        "escala_dolor": 3, "nivel_urgencia": "NARANJA",
                        "motivo_consulta_triaje": "Lactante de 5 anos con dificultad respiratoria, sibilancias y fiebre de 38.1C desde hace 12 horas. Primer episodio.",
                        "observaciones": "SpO2 93% en lactante. Polipnea 48 rpm. Sibilancias audibles. Probable bronquiolitis.",
                    },
                ],
                "consultas": [
                    {
                        "estado": "COMPLETADA",
                        "motivo_consulta": "Bronquiolitis aguda en lactante mayor de 5 anos. Primer episodio sibilante.",
                        "historia_enfermedad_actual": "Lactante de 5 anos de edad, peso 11.5kg, con cuadro de 12h de rinorrea, fiebre 38.1C y dificultad respiratoria progresiva con sibilancias. Sin antecedente de episodios previos ni historia familiar de asma. Contacto con familiar con IRA en casa hace 5 dias.",
                        "examen_fisico": "T: 38.1C. FC: 140 lpm. FR: 48 rpm. SpO2: 93%. Tiraje subcostal leve. Sibilancias espiratorias difusas bilaterales. Crepitantes en base izquierda. Sin cianosis.",
                        "impresion_diagnostica": "Bronquiolitis aguda moderada. Primer episodio sibilante. Posible etiologia por VRS.",
                        "codigo_cie10_principal": "J21.9",
                        "descripcion_cie10": "Bronquiolitis aguda no especificada",
                        "plan_tratamiento": "1. Nebulizacion con suero hipertonico 3% c/4h\n2. Oxigenoterapia si SpO2 < 92%\n3. Posicion semiincorporada\n4. Hidratacion oral frecuente a tolerancia\n5. Monitoreo SpO2 continuo\n6. Alta si SpO2 > 94% sostenida",
                        "indicaciones_alta": "Posicion semisentada. Evitar humo de cigarrillo. Consulta inmediata si SpO2 < 92%, aleteo nasal o cianosis. Control en 24h.",
                        "requiere_derivacion": False,
                    },
                ],
            },
            {
                "ci": "3002006", "ci_complemento": "",
                "nombres": "Hugo Rene", "apellido_paterno": "Balderrama", "apellido_materno": "Cuellar",
                "fecha_nacimiento": date(1967, 1, 18), "sexo": "M",
                "autoidentificacion": "MESTIZO", "telefono": "71234015",
                "direccion": "Calle Aroma 234, Cochabamba",
                "tipo_seguro": "CNS", "numero_asegurado": "CNS-CN-006",
                "antecedentes": {
                    "grupo_sanguineo": "O+",
                    "alergias": "Sulfas (eritema cutaneo)",
                    "ant_patologicos": "Gota articular desde 2018\nHipertension arterial desde 2019",
                    "ant_no_patologicos": "Consumo moderado de alcohol (fines de semana). No fuma.",
                    "ant_quirurgicos": "Ninguno",
                    "ant_familiares": "Padre con gota. Hermano con hiperuricemia.",
                    "ant_gineco_obstetricos": "",
                    "medicacion_actual": "Alopurinol 300mg c/dia\nLosartan 50mg c/dia\nColchicina 0.5mg SOS crisis",
                    "esquema_vacunacion": "Influenza (2024). COVID-19 completo.",
                },
                "triajes": [
                    {
                        "peso_kg": "88.0", "talla_cm": "173.0",
                        "frecuencia_cardiaca": 80, "frecuencia_respiratoria": 17,
                        "presion_sistolica": 150, "presion_diastolica": 94,
                        "temperatura_celsius": "36.8", "saturacion_oxigeno": 98,
                        "escala_dolor": 8, "nivel_urgencia": "AMARILLO",
                        "motivo_consulta_triaje": "Dolor intenso en articulacion del tobillo derecho desde esta manana. Inflamacion, eritema y calor local. Sospecha de crisis de gota.",
                        "observaciones": "Artritis aguda de tobillo derecho. Hiperuricemia conocida. Evaluar crisis de gota.",
                    },
                ],
                "consultas": [
                    {
                        "estado": "COMPLETADA",
                        "motivo_consulta": "Crisis aguda de gota en tobillo derecho. Dolor 8/10 de inicio brusco esta manana.",
                        "historia_enfermedad_actual": "Paciente de 59 anos con gota articular conocida acude por dolor agudo 8/10 en tobillo derecho desde las 4am, con inflamacion, eritema y calor local. Refiere haber consumido alcohol y comida rica en purinas el fin de semana. No tomo colchicina oportunamente.",
                        "examen_fisico": "Tobillo derecho: eritema intenso, edema, calor local marcado. Dolor exquisito a la palpacion y con el movimiento. PA: 150/94 mmHg. Uricemia en espera.",
                        "impresion_diagnostica": "Crisis aguda de gota en articulacion tibiotarsiana derecha. HTA no controlada.",
                        "codigo_cie10_principal": "M10.07",
                        "descripcion_cie10": "Gota idiopatica, tobillo y pie",
                        "plan_tratamiento": "1. Indometacina 50mg c/8h por 5 dias con comida\n2. Colchicina 0.5mg c/12h por 3 dias\n3. Reposo del tobillo afectado\n4. Hielo local 20 min c/6h\n5. Ajustar Losartan a 100mg y agregar Amlodipino 5mg para HTA",
                        "indicaciones_alta": "Evitar alcohol y alimentos ricos en purinas (carnes rojas, mariscos, visceras). Aumentar hidratacion. Continuar alopurinol. Control en 7 dias con uricemia.",
                        "requiere_derivacion": False,
                    },
                ],
            },
        ],
    },

    # -- Clinica 3: Policlinica Santa Rosa -----------------------------------
    {
        "tenant": {
            "nombre": "Policlinica Santa Rosa",
            "slug":   "policlinica-santa-rosa",
            "nit":    "1005551234",
            "direccion": "Calle Junin 789, Santa Cruz",
            "telefono":  "3-3334567",
        },
        "especialidades": [
            "Medicina General",
            "Ginecologia y Obstetricia",
            "Dermatologia",
            "Endocrinologia",
        ],
        "personal": [
            {
                "username": "dir_srosa", "password": "12345678",
                "first_name": "Ana", "last_name": "Mendez Suarez",
                "email": "directora@srosa.test",
                "rol_grupo": "Director",
                "item_min_salud": "DIR-001", "rol": PersonalSalud.ROL_ADMIN,
                "especialidad": None,
            },
            {
                "username": "med_srosa", "password": "12345678",
                "first_name": "Fernando", "last_name": "Castro Vaca",
                "email": "medico@srosa.test",
                "rol_grupo": "Médico",
                "item_min_salud": "MED-001", "rol": PersonalSalud.ROL_MEDICO,
                "especialidad": "Medicina General",
            },
            {
                "username": "enf_srosa", "password": "12345678",
                "first_name": "Lucia", "last_name": "Torrez Antelo",
                "email": "enfermera@srosa.test",
                "rol_grupo": "Enfermera",
                "item_min_salud": "ENF-001", "rol": PersonalSalud.ROL_ENFERMERA,
                "especialidad": None,
            },
            {
                "username": "adm_srosa", "password": "12345678",
                "first_name": "Carolina", "last_name": "Pedraza Gutierrez",
                "email": "admin@srosa.test",
                "rol_grupo": "Administrativo",
                "item_min_salud": "ADM-001", "rol": PersonalSalud.ROL_ADMIN,
                "especialidad": None,
            },
            {
                "username": "lab_srosa", "password": "12345678",
                "first_name": "Miguel", "last_name": "Barba Justiniano",
                "email": "laboratorio@srosa.test",
                "rol_grupo": "Laboratorio",
                "item_min_salud": "LAB-001", "rol": PersonalSalud.ROL_ADMIN,
                "especialidad": None,
            },
            {
                "username": "farm_srosa", "password": "12345678",
                "first_name": "Paola", "last_name": "Suarez Nava",
                "email": "farmacia@srosa.test",
                "rol_grupo": "Farmacia",
                "item_min_salud": "FAR-001", "rol": PersonalSalud.ROL_ADMIN,
                "especialidad": None,
            },
            {
                "username": "aud_srosa", "password": "12345678",
                "first_name": "Marcos", "last_name": "Rocha Cabrera",
                "email": "auditor@srosa.test",
                "rol_grupo": "Auditor",
                "item_min_salud": "AUD-001", "rol": PersonalSalud.ROL_ADMIN,
                "especialidad": None,
            },
        ],
        "pacientes": [
            {
                "ci": "3003001", "ci_complemento": "",
                "nombres": "Diego Alejandro", "apellido_paterno": "Ramos", "apellido_materno": "Ortiz",
                "fecha_nacimiento": date(1988, 3, 22), "sexo": "M",
                "autoidentificacion": "MESTIZO", "telefono": "71234007",
                "direccion": "Av. Busch 1200, Santa Cruz",
                "tipo_seguro": "PARTICULAR", "numero_asegurado": "",
                "antecedentes": {
                    "grupo_sanguineo": "AB+",
                    "alergias": "Polvo y acaro del polvo (asma alergica)",
                    "ant_patologicos": "Asma bronquial alergica persistente leve desde la infancia",
                    "ant_no_patologicos": "No fuma. No alcohol. Actividad fisica regular.",
                    "ant_quirurgicos": "Ninguno",
                    "ant_familiares": "Madre con asma bronquial. Padre con rinitis alergica.",
                    "ant_gineco_obstetricos": "",
                    "medicacion_actual": "Salbutamol inhalador SOS\nFluticasona inhalada 250mcg c/12h (controlador)",
                    "esquema_vacunacion": "Esquema completo. Influenza anual. COVID-19 completo.",
                },
                "triajes": [
                    {
                        "peso_kg": "76.0", "talla_cm": "174.0",
                        "frecuencia_cardiaca": 98, "frecuencia_respiratoria": 24,
                        "presion_sistolica": 122, "presion_diastolica": 78,
                        "temperatura_celsius": "36.8", "saturacion_oxigeno": 93,
                        "escala_dolor": 5, "nivel_urgencia": "NARANJA",
                        "motivo_consulta_triaje": "Crisis asmatica moderada. Uso de inhalador sin mejoria suficiente. Sibilancias audibles.",
                        "observaciones": "SpO2 93%. Se inicia nebulizacion con salbutamol en triaje.",
                    },
                ],
                "consultas": [
                    {
                        "estado": "COMPLETADA",
                        "motivo_consulta": "Crisis asmatica moderada que no cede con broncodilatador de rescate habitual.",
                        "historia_enfermedad_actual": "Paciente de 38 anos con asma bronquial alergica acude por disnea de 3h de evolucion desencadenada por limpieza de habitacion polvorienta. Uso de 6 puffs de salbutamol sin mejoria suficiente. Sibilancias audibles por el propio paciente.",
                        "examen_fisico": "FR: 24 rpm. SpO2: 93%. Torax: sibilancias espiratorias difusas bilaterales. Leve uso de musculatura accesoria. Sin cianosis.",
                        "impresion_diagnostica": "Crisis asmatica moderada",
                        "codigo_cie10_principal": "J45.1",
                        "descripcion_cie10": "Asma predominantemente alergica moderada",
                        "plan_tratamiento": "1. Salbutamol nebulizado 2.5mg c/20min x3 dosis\n2. Prednisona 40mg VO dosis unica\n3. Control SpO2 c/30 min\n4. Alta con Beclometasona 250mcg c/12h por 7 dias\n5. Evitar desencadenantes",
                        "indicaciones_alta": "Evitar polvo y alergenos. Continuar fluticasona diaria. Si SpO2 baja de 92% o disnea en reposo, urgencias de inmediato.",
                        "requiere_derivacion": False,
                    },
                ],
            },
            {
                "ci": "3003002", "ci_complemento": "",
                "nombres": "Valeria", "apellido_paterno": "Condori", "apellido_materno": "Paco",
                "fecha_nacimiento": date(1982, 8, 10), "sexo": "F",
                "autoidentificacion": "AYMARA", "telefono": "71234008",
                "direccion": "Calle Florida 456, Santa Cruz",
                "tipo_seguro": "CNS", "numero_asegurado": "CNS-SR-002",
                "antecedentes": {
                    "grupo_sanguineo": "O-",
                    "alergias": "Sin alergias conocidas",
                    "ant_patologicos": "Hipotiroidismo primario diagnosticado 2020",
                    "ant_no_patologicos": "No fuma. No alcohol. Actividad fisica ocasional.",
                    "ant_quirurgicos": "Ninguno",
                    "ant_familiares": "Madre con hipotiroidismo. Hermana con tiroiditis de Hashimoto.",
                    "ant_gineco_obstetricos": "G2P2A0C1. FUM: hace 15 dias. Ciclos irregulares.",
                    "medicacion_actual": "Levotiroxina 75mcg en ayunas",
                    "esquema_vacunacion": "Esquema completo. Influenza (2024). COVID-19 completo.",
                },
                "triajes": [
                    {
                        "peso_kg": "68.0", "talla_cm": "160.0",
                        "frecuencia_cardiaca": 60, "frecuencia_respiratoria": 15,
                        "presion_sistolica": 110, "presion_diastolica": 70,
                        "temperatura_celsius": "36.1", "saturacion_oxigeno": 98,
                        "escala_dolor": 2, "nivel_urgencia": "VERDE",
                        "motivo_consulta_triaje": "Control de hipotiroidismo. Refiere cansancio y aumento de peso de 4kg en 2 meses a pesar de no cambiar dieta.",
                        "observaciones": "FC 60 lpm. Paciente refiere mucho frio y estrenimiento. TSH pendiente de revision.",
                    },
                ],
                "consultas": [
                    {
                        "estado": "COMPLETADA",
                        "motivo_consulta": "Control de hipotiroidismo. Sintomas de hipofuncion tiroidea a pesar de tratamiento.",
                        "historia_enfermedad_actual": "Paciente de 44 anos con hipotiroidismo en tratamiento con levotiroxina 75mcg acude por control trimestral. Refiere aumento de peso 4kg en 2 meses, cansancio extremo, intolerancia al frio, constipacion y cabello fragil. Cumple con medicacion en ayunas.",
                        "examen_fisico": "PA: 110/70 mmHg. FC: 60 lpm. Peso: 68kg. Piel seca y palida. Cabello opaco. Reflejos osteotendinosos levemente enlentecidos. Tiroides: no palpable, sin nodulos.",
                        "impresion_diagnostica": "Hipotiroidismo primario insuficientemente controlado (probable dosis insuficiente de levotiroxina)",
                        "codigo_cie10_principal": "E03.9",
                        "descripcion_cie10": "Hipotiroidismo no especificado",
                        "plan_tratamiento": "1. Aumentar Levotiroxina a 100mcg en ayunas\n2. Solicitar TSH, T4 libre y anti-TPO de control\n3. Control en 6 semanas con resultado de TSH\n4. Consejeria sobre dieta y actividad fisica\n5. Evaluar suplemento de hierro si ferritina baja",
                        "indicaciones_alta": "Tomar levotiroxina siempre en ayunas, 30 min antes del desayuno. No tomar con calcio ni hierro. Control en 6 semanas.",
                        "requiere_derivacion": False,
                    },
                ],
            },
            {
                "ci": "3003003", "ci_complemento": "",
                "nombres": "Claudia Beatriz", "apellido_paterno": "Mamani", "apellido_materno": "Cruz",
                "fecha_nacimiento": date(1996, 12, 1), "sexo": "F",
                "autoidentificacion": "QUECHUA", "telefono": "71234009",
                "direccion": "Av. Ejercito 567, Santa Cruz",
                "tipo_seguro": "SUS", "numero_asegurado": "",
                "antecedentes": {
                    "grupo_sanguineo": "A+",
                    "alergias": "Sin alergias conocidas",
                    "ant_patologicos": "Sin antecedentes patologicos de importancia",
                    "ant_no_patologicos": "No fuma. No alcohol.",
                    "ant_quirurgicos": "Ninguno",
                    "ant_familiares": "Sin antecedentes relevantes",
                    "ant_gineco_obstetricos": "G0P0A0C0. FUM: hace 10 dias. Ciclos regulares c/28 dias. Sin MAC.",
                    "medicacion_actual": "Ninguna",
                    "esquema_vacunacion": "Esquema completo. VPH (2 dosis 2012). COVID-19 completo.",
                },
                "triajes": [
                    {
                        "peso_kg": "55.0", "talla_cm": "158.0",
                        "frecuencia_cardiaca": 84, "frecuencia_respiratoria": 17,
                        "presion_sistolica": 112, "presion_diastolica": 72,
                        "temperatura_celsius": "37.0", "saturacion_oxigeno": 99,
                        "escala_dolor": 5, "nivel_urgencia": "VERDE",
                        "motivo_consulta_triaje": "Flujo vaginal abundante con mal olor desde hace 5 dias. Picazon intensa.",
                        "observaciones": "Paciente estable. Derivada a consulta ginecologica.",
                    },
                ],
                "consultas": [
                    {
                        "estado": "COMPLETADA",
                        "motivo_consulta": "Flujo vaginal abundante, con mal olor y prurito intenso de 5 dias de evolucion.",
                        "historia_enfermedad_actual": "Paciente de 30 anos sin antecedentes ginecologicos previos acude por flujo vaginal grisaceo abundante con olor a pescado desde hace 5 dias, acompanado de prurito vulvar moderado. Niega fiebre, dolor abdominal o dispareunia. No tiene pareja estable. Ultima relacion sexual hace 3 semanas.",
                        "examen_fisico": "Genitales externos con eritema moderado. Flujo vaginal grisaceo homogeneo con olor caracteristico. pH vaginal: 5.5. Test de aminas positivo. Cuello uterino sin lesiones visibles.",
                        "impresion_diagnostica": "Vaginosis bacteriana",
                        "codigo_cie10_principal": "N76.0",
                        "descripcion_cie10": "Vaginitis aguda",
                        "plan_tratamiento": "1. Metronidazol 500mg c/12h por 7 dias\n2. Metronidazol gel vaginal 0.75% c/noche por 5 dias\n3. Higiene intima con pH neutro\n4. Abstinencia sexual durante tratamiento\n5. Control en 2 semanas",
                        "indicaciones_alta": "Completar tratamiento aunque mejore antes. No alcohol durante metronidazol. Usar ropa interior de algodon. Control obligatorio en 2 semanas.",
                        "requiere_derivacion": False,
                    },
                ],
            },
            {
                "ci": "3003004", "ci_complemento": "",
                "nombres": "Renata", "apellido_paterno": "Flores", "apellido_materno": "Vidal",
                "fecha_nacimiento": date(2001, 5, 19), "sexo": "F",
                "autoidentificacion": "MESTIZO", "telefono": "71234016",
                "direccion": "Av. Cristo Redentor 890, Santa Cruz",
                "tipo_seguro": "PARTICULAR", "numero_asegurado": "",
                "antecedentes": {
                    "grupo_sanguineo": "A-",
                    "alergias": "Nickel (dermatitis de contacto)",
                    "ant_patologicos": "Dermatitis atopica desde la infancia. Rinitis alergica.",
                    "ant_no_patologicos": "No fuma. No alcohol.",
                    "ant_quirurgicos": "Ninguno",
                    "ant_familiares": "Madre con dermatitis atopica. Padre con psoriasis.",
                    "ant_gineco_obstetricos": "G0P0A0C0. FUM: hace 2 semanas. Ciclos regulares. MAC: ACO.",
                    "medicacion_actual": "Loratadina 10mg c/dia\nEmoliente corporal c/12h",
                    "esquema_vacunacion": "Esquema completo. Influenza (2024).",
                },
                "triajes": [
                    {
                        "peso_kg": "58.0", "talla_cm": "165.0",
                        "frecuencia_cardiaca": 76, "frecuencia_respiratoria": 16,
                        "presion_sistolica": 110, "presion_diastolica": 68,
                        "temperatura_celsius": "36.5", "saturacion_oxigeno": 99,
                        "escala_dolor": 3, "nivel_urgencia": "VERDE",
                        "motivo_consulta_triaje": "Brote de eczema en cara y codo derecho desde hace 1 semana. Prurito intenso que no mejora con loratadina.",
                        "observaciones": "Lesiones eczematosas activas en cara y fosa antecubital derecha. Paciente con rascado.",
                    },
                ],
                "consultas": [
                    {
                        "estado": "COMPLETADA",
                        "motivo_consulta": "Brote de dermatitis atopica en cara y codo derecho. Prurito intenso refractario a antihistaminico oral.",
                        "historia_enfermedad_actual": "Paciente de 25 anos con dermatitis atopica cronica acude por brote de 1 semana de evolucion en region malar bilateral y fosa antecubital derecha. Prurito intenso que altera el sueno. Loratadina sin efecto suficiente. Relaciona brote con cambio de detergente hace 2 semanas.",
                        "examen_fisico": "Placas eritematosas con descamacion fina en mejillas y fosa antecubital derecha. Liquenificacion leve. Lesiones de rascado. Sin infeccion sobreagregada visible.",
                        "impresion_diagnostica": "Dermatitis atopica en brote moderado. Sin infeccion bacteriana sobreagregada.",
                        "codigo_cie10_principal": "L20.9",
                        "descripcion_cie10": "Dermatitis atopica no especificada",
                        "plan_tratamiento": "1. Betametasona 0.05% crema c/12h por 7 dias en zonas activas\n2. Tacrolimus 0.1% unguento mantenimiento en cara\n3. Cetirizina 10mg en la noche\n4. Emoliente sin fragancia c/8h en todo el cuerpo\n5. Evitar detergente nuevo y tejidos sinteticos",
                        "indicaciones_alta": "No usar jabon con fragancia. Ducha tibia corta. Hidratar piel inmediatamente despues del bano. Evitar rascado. Control en 2 semanas.",
                        "requiere_derivacion": False,
                    },
                ],
            },
            {
                "ci": "3003005", "ci_complemento": "",
                "nombres": "Ernesto", "apellido_paterno": "Antezana", "apellido_materno": "Quiroga",
                "fecha_nacimiento": date(1970, 9, 7), "sexo": "M",
                "autoidentificacion": "MESTIZO", "telefono": "71234017",
                "direccion": "Calle Warnes 345, Santa Cruz",
                "tipo_seguro": "SUS", "numero_asegurado": "",
                "antecedentes": {
                    "grupo_sanguineo": "B+",
                    "alergias": "Sin alergias conocidas",
                    "ant_patologicos": "Obesidad grado 2 desde 2015\nHigado graso no alcoholico (HGNA) diagnosticado 2022\nSindrome metabolico",
                    "ant_no_patologicos": "No fuma. Consumo ocasional de alcohol. Trabajo sedentario.",
                    "ant_quirurgicos": "Ninguno",
                    "ant_familiares": "Padre con diabetes tipo 2. Madre con obesidad.",
                    "ant_gineco_obstetricos": "",
                    "medicacion_actual": "Metformina 500mg c/12h (inicio reciente)\nOmegasol 1g c/dia",
                    "esquema_vacunacion": "Influenza (2024). COVID-19 completo.",
                },
                "triajes": [
                    {
                        "peso_kg": "112.0", "talla_cm": "172.0",
                        "frecuencia_cardiaca": 84, "frecuencia_respiratoria": 18,
                        "presion_sistolica": 142, "presion_diastolica": 90,
                        "temperatura_celsius": "36.6", "saturacion_oxigeno": 97,
                        "escala_dolor": 1, "nivel_urgencia": "VERDE",
                        "motivo_consulta_triaje": "Control de obesidad y sindrome metabolico. Trae laboratorios con glucemia en ayunas 118 mg/dL y trigliceridos 280 mg/dL.",
                        "observaciones": "Paciente con obesidad grado 2. Sindrome metabolico con multiples factores. Requiere evaluacion endocrinologica.",
                    },
                ],
                "consultas": [
                    {
                        "estado": "COMPLETADA",
                        "motivo_consulta": "Control de sindrome metabolico. Laboratorios con prediabetes y dislipidemia mixta. Obesidad grado 2.",
                        "historia_enfermedad_actual": "Paciente de 56 anos con obesidad grado 2 y HGNA acude a control mensual de endocrinologia. Trae laboratorios: glucemia 118 mg/dL (prediabetes), TG 280 mg/dL, HDL 36 mg/dL, LDL 145 mg/dL. PA en casa 140-145/90. Niega poliuria, polidipsia o dificultad para bajar de peso con el plan actual.",
                        "examen_fisico": "Peso: 112kg. Talla: 172cm. IMC: 37.9 (obesidad grado 2). Circunferencia abdominal: 112cm. PA: 142/90 mmHg. Higado palpable 2cm bajo reborde costal. Sin edemas.",
                        "impresion_diagnostica": "Sindrome metabolico con prediabetes, dislipidemia mixta, HTA estadio 1 y obesidad grado 2. HGNA.",
                        "codigo_cie10_principal": "E88.81",
                        "descripcion_cie10": "Sindrome metabolico",
                        "plan_tratamiento": "1. Intensificar Metformina a 850mg c/12h\n2. Iniciar Atorvastina 20mg en la noche\n3. Iniciar Losartan 50mg c/dia para HTA\n4. Plan nutricional hipocalorico e hiposodico con nutricionista\n5. Actividad fisica aerobica 150 min/semana\n6. Control en 30 dias con laboratorios completos",
                        "indicaciones_alta": "Dieta hipocalorica estricta. Caminar 30 min al dia. Evitar alcohol. Monitorear PA diariamente. Control en 1 mes.",
                        "requiere_derivacion": True,
                        "derivacion_destino": "Nutricion — Policlinica Santa Rosa",
                        "derivacion_motivo": "Obesidad grado 2 con sindrome metabolico. Plan nutricional estructurado urgente.",
                    },
                ],
            },
            {
                "ci": "3003006", "ci_complemento": "",
                "nombres": "Silvia", "apellido_paterno": "Gutierrez", "apellido_materno": "Pena",
                "fecha_nacimiento": date(1955, 2, 14), "sexo": "F",
                "autoidentificacion": "MESTIZO", "telefono": "71234018",
                "direccion": "Av. Paurito 123, Santa Cruz",
                "tipo_seguro": "CNS", "numero_asegurado": "CNS-SR-006",
                "antecedentes": {
                    "grupo_sanguineo": "A+",
                    "alergias": "Metamizol (anafilaxia leve)",
                    "ant_patologicos": "Osteoporosis diagnosticada 2020\nHipertension arterial desde 2016\nArtritis reumatoide desde 2018",
                    "ant_no_patologicos": "No fuma. No alcohol. Jubilada.",
                    "ant_quirurgicos": "Protesis de cadera derecha (2023)",
                    "ant_familiares": "Madre con osteoporosis. Hermana con artritis reumatoide.",
                    "ant_gineco_obstetricos": "G3P3A0C0. Menopausia a los 48 anos.",
                    "medicacion_actual": "Metrotexato 7.5mg semanal\nAcido folico 5mg (dia siguiente al MTX)\nCalcio 1000mg c/dia\nVitamina D 800UI c/dia\nAmlodipino 10mg c/dia",
                    "esquema_vacunacion": "Influenza anual. Neumococo (2023). COVID-19 completo. Zoster (2022).",
                },
                "triajes": [
                    {
                        "peso_kg": "60.0", "talla_cm": "155.0",
                        "frecuencia_cardiaca": 76, "frecuencia_respiratoria": 16,
                        "presion_sistolica": 138, "presion_diastolica": 84,
                        "temperatura_celsius": "36.4", "saturacion_oxigeno": 98,
                        "escala_dolor": 5, "nivel_urgencia": "VERDE",
                        "motivo_consulta_triaje": "Control de artritis reumatoide. Refiere rigidez matutina de 2 horas y dolor en munecas bilaterales desde hace 2 semanas.",
                        "observaciones": "Paciente con AR conocida. Posible brote articular. Revisar adherencia a MTX.",
                    },
                ],
                "consultas": [
                    {
                        "estado": "COMPLETADA",
                        "motivo_consulta": "Control de artritis reumatoide. Posible brote con rigidez matutina prolongada y artritis de munecas.",
                        "historia_enfermedad_actual": "Paciente de 71 anos con AR en tratamiento con metotrexato acude por rigidez matutina de 2h de duracion y dolor en munecas bilaterales con leve inflamacion desde hace 2 semanas. Refiere haber omitido 2 dosis de MTX por nauseas. Sin fiebre ni otros sintomas sistemicos.",
                        "examen_fisico": "Munecas: inflamacion leve bilateral, dolor a la palpacion y limitacion de flexo-extension. Sin tenosinovitis visible. Articulaciones MCP y IFP sin cambios activos. PA: 138/84 mmHg. Sin fiebre.",
                        "impresion_diagnostica": "Brote leve de artritis reumatoide en munecas por probable omision de metotrexato.",
                        "codigo_cie10_principal": "M05.9",
                        "descripcion_cie10": "Artritis reumatoide seropositiva, no especificada",
                        "plan_tratamiento": "1. Retomar Metotrexato 7.5mg semanal con antiemedico previo\n2. Prednisona 10mg/dia por 7 dias (puente)\n3. Continuar Calcio y Vitamina D\n4. Control en 4 semanas con laboratorios (hemograma, hepatico)\n5. Si persiste actividad: considerar escalar a MTX 10mg",
                        "indicaciones_alta": "No omitir MTX. Tomar con comida para reducir nauseas. Si hay fiebre o sintomas sistemicos, consultar de inmediato. Control en 1 mes.",
                        "requiere_derivacion": False,
                    },
                ],
            },
        ],
    },
]


# ---------------------------------------------------------------------------
# COMMAND
# ---------------------------------------------------------------------------

class Command(BaseCommand):
    help = "Carga datos de prueba multitenant: 3 clinicas con personal completo y 6 pacientes cada una."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limpiar",
            action="store_true",
            help="Elimina los datos del seed antes de recrearlos.",
        )

    def handle(self, *args, **options):
        if options["limpiar"]:
            self._limpiar()

        self.stdout.write("\n=== Seed multitenant Histolink — 3 clinicas ===\n")

        for clinica in CLINICAS:
            tenant = self._crear_tenant(clinica["tenant"])
            self.stdout.write(f"\n--- {tenant.nombre} ---")

            especialidades = self._crear_especialidades(tenant, clinica["especialidades"])
            usuarios       = self._crear_personal(tenant, clinica["personal"], especialidades)
            medico         = next((u for k, u in usuarios.items() if "med_" in k), None)
            enfermera      = next((u for k, u in usuarios.items() if "enf_" in k), None)
            self._crear_pacientes(tenant, clinica["pacientes"], medico, enfermera)

        self.stdout.write("\n=== Seed completado ===\n")
        self.stdout.write("Credenciales de acceso (password: 12345678):\n")
        for clinica in CLINICAS:
            self.stdout.write(f"\n  [{clinica['tenant']['nombre']}]")
            for p in clinica["personal"]:
                self.stdout.write(f"    {p['username']:22} ({p['rol_grupo']})")

    # ------------------------------------------------------------------
    def _limpiar(self):
        self.stdout.write("Limpiando datos previos del seed...")
        todos_usernames = [p["username"] for c in CLINICAS for p in c["personal"]]
        todos_slugs     = [c["tenant"]["slug"] for c in CLINICAS]
        todos_cis       = [p["ci"] for c in CLINICAS for p in c["pacientes"]]

        eliminados_p, _ = Paciente.objects.filter(ci__in=todos_cis).delete()
        eliminados_u, _ = User.objects.filter(username__in=todos_usernames).delete()
        eliminados_t, _ = Tenant.objects.filter(slug__in=todos_slugs).delete()
        self.stdout.write(f"  Pacientes: {eliminados_p} | Usuarios: {eliminados_u} | Tenants: {eliminados_t}")

    # ------------------------------------------------------------------
    def _crear_tenant(self, datos):
        tenant, created = Tenant.objects.get_or_create(
            slug=datos["slug"],
            defaults={
                "nombre":    datos["nombre"],
                "nit":       datos.get("nit", ""),
                "direccion": datos.get("direccion", ""),
                "telefono":  datos.get("telefono", ""),
                "activo":    True,
            },
        )
        estado = "[OK] Creado" if created else "[--] Ya existe"
        self.stdout.write(f"  {estado}: Tenant '{tenant.nombre}'")
        return tenant

    # ------------------------------------------------------------------
    def _crear_especialidades(self, tenant, nombres):
        resultado = {}
        for nombre in nombres:
            esp, created = Especialidad.objects.get_or_create(
                nombre=nombre, tenant=tenant
            )
            resultado[nombre] = esp
            if created:
                self.stdout.write(f"  [OK] Especialidad: {nombre}")
        return resultado

    # ------------------------------------------------------------------
    def _crear_personal(self, tenant, personal_data, especialidades):
        resultado = {}
        for datos in personal_data:
            grupo, _ = Group.objects.get_or_create(name=datos["rol_grupo"])

            user, ucreado = User.objects.get_or_create(
                username=datos["username"],
                defaults={
                    "first_name": datos["first_name"],
                    "last_name":  datos["last_name"],
                    "email":      datos["email"],
                    "is_active":  True,
                },
            )
            user.set_password(datos["password"])
            user.is_active = True
            user.save(update_fields=["password", "is_active"])
            user.groups.add(grupo)

            especialidad = especialidades.get(datos["especialidad"]) if datos["especialidad"] else None

            perfil, pcreado = PersonalSalud.objects.get_or_create(
                user=user,
                defaults={
                    "tenant":         tenant,
                    "item_min_salud": datos["item_min_salud"],
                    "rol":            datos["rol"],
                    "especialidad":   especialidad,
                },
            )
            estado = "[OK]" if ucreado else "[--]"
            self.stdout.write(f"  {estado} {datos['rol_grupo']:15} {user.get_full_name()} ({datos['username']})")
            resultado[datos["username"]] = user

        return resultado

    # ------------------------------------------------------------------
    def _crear_pacientes(self, tenant, pacientes_data, medico, enfermera):
        for datos in pacientes_data:
            paciente, created = Paciente.objects.get_or_create(
                ci=datos["ci"],
                ci_complemento=datos.get("ci_complemento", ""),
                tenant=tenant,
                defaults={
                    "nombres":            datos["nombres"],
                    "apellido_paterno":   datos["apellido_paterno"],
                    "apellido_materno":   datos["apellido_materno"],
                    "fecha_nacimiento":   datos["fecha_nacimiento"],
                    "sexo":               datos["sexo"],
                    "autoidentificacion": datos["autoidentificacion"],
                    "telefono":           datos.get("telefono", ""),
                    "direccion":          datos.get("direccion", ""),
                    "tipo_seguro":        datos["tipo_seguro"],
                    "numero_asegurado":   datos.get("numero_asegurado", ""),
                    "creado_por":         medico,
                },
            )
            nombre_completo = f"{datos['nombres']} {datos['apellido_paterno']}"
            estado = "[OK]" if created else "[--]"
            self.stdout.write(f"  {estado} Paciente: {nombre_completo} (CI: {datos['ci']})")

            # Antecedentes
            ant_data = datos.get("antecedentes", {})
            if ant_data:
                ant, _ = Antecedente.objects.get_or_create(paciente=paciente)
                for campo, valor in ant_data.items():
                    setattr(ant, campo, valor)
                ant.ultima_actualizacion_por = medico
                ant.save()

            if not created:
                continue

            # PersonalSalud del medico para apertura de fichas
            try:
                ps_apertura = medico.perfil_personal_salud
            except Exception:
                ps_apertura = PersonalSalud.objects.filter(user=medico).first()

            # Triajes — cada triaje necesita su propia Ficha (OneToOne)
            triajes_creados = []
            fichas_creadas = []
            for t_data in datos.get("triajes", []):
                ficha = Ficha.objects.create(
                    paciente=paciente,
                    profesional_apertura=ps_apertura,
                    estado=Ficha.Estado.CERRADA,
                )
                fichas_creadas.append(ficha)
                triaje, _ = Triaje.objects.get_or_create(
                    ficha=ficha,
                    defaults={
                        "tenant":    tenant,
                        "enfermera": enfermera or medico,
                        **t_data,
                    },
                )
                triajes_creados.append(triaje)

            # Consultas — vinculadas a la Ficha del triaje correspondiente
            for i, c_data in enumerate(datos.get("consultas", [])):
                triaje_asoc = triajes_creados[i] if i < len(triajes_creados) else None
                if i < len(fichas_creadas):
                    ficha_asoc = fichas_creadas[i]
                else:
                    ficha_asoc = Ficha.objects.create(
                        paciente=paciente,
                        profesional_apertura=ps_apertura,
                        estado=Ficha.Estado.CERRADA,
                    )
                Consulta.objects.get_or_create(
                    ficha=ficha_asoc,
                    codigo_cie10_principal=c_data["codigo_cie10_principal"],
                    defaults={
                        "tenant": tenant,
                        "medico": medico,
                        "triaje": triaje_asoc,
                        **{k: v for k, v in c_data.items() if k != "codigo_cie10_principal"},
                    },
                )
