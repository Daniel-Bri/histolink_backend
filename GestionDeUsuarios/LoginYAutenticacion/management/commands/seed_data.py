"""
GestionDeUsuarios/LoginYAutenticacion/management/commands/seed_data.py

Carga datos de prueba multitenant para Histolink.
Crea 3 establecimientos de salud independientes, cada uno con su propio
personal y pacientes con expediente clínico completo.

Uso:
    python manage.py seed_data
    python manage.py seed_data --limpiar   # Elimina datos del seed antes de recrear
"""

from datetime import date

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from AtencionClinica.ConsultaMedicaSOAP.models import Consulta
from AtencionClinica.RegistroDeTriaje.models import Triaje
from GestionDeUsuarios.EdicionDeAntecedentesMedicos.models import Antecedente
from GestionDeUsuarios.GestionDePersonalDeSalud.models import Especialidad, PersonalSalud
from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente
from Tenants.models import Tenant


# ═══════════════════════════════════════════════════════════════════════════
# DATOS DE LOS 3 ESTABLECIMIENTOS
# ═══════════════════════════════════════════════════════════════════════════

CLINICAS = [

    # ── Clínica 1: Hospital Universitario San Pablo ──────────────────────
    {
        "tenant": {
            "nombre": "Hospital Universitario San Pablo",
            "slug":   "hospital-san-pablo",
            "nit":    "1001234567",
            "direccion": "Av. Montes 1500, La Paz",
            "telefono":  "2-2901234",
        },
        "especialidades": [
            "Cardiología",
            "Medicina Interna",
            "Urgencias y Emergencias",
            "Neurología",
            "Cirugía General",
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
                "especialidad": "Cardiología",
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
                    "alergias": "Ibuprofeno (úlcera péptica previa)",
                    "ant_patologicos": "Dislipidemia mixta desde 2018\nEx-tabaquismo (dejó en 2020)",
                    "ant_no_patologicos": "Ex tabaquista: 20 cig/dia por 25 años. No alcohol.",
                    "ant_quirurgicos": "Herniorrafia inguinal derecha (2008)",
                    "ant_familiares": "Padre: IAM, fallecido a los 58 años. Hermano: bypass coronario.",
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
                        "historia_enfermedad_actual": "Paciente masculino de 65 años con dislipidemia y antecedente familiar de IAM precoz. Dolor precordial opresivo 8/10 de inicio brusco, irradiado a brazo izquierdo y mandibula, acompañado de diaforesis y nauseas. Toma AAS 100mg como medicacion habitual.",
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
                    "ant_gineco_obstetricos": "G3P3A0C0. Menopausia a los 52 años.",
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
                        "historia_enfermedad_actual": "Paciente de 68 años con ICC cronica, HTA y FA acude por disnea de esfuerzo que progreso a reposo en 3 dias, con ortopnea (necesita 3 almohadas), edema bimaleolar que asciende hasta rodillas y ganancia de 4kg en 7 dias. Refiere no haber tomado furosemida los ultimos 2 dias por olvido.",
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
                    "alergias": "Penicilina (eruption cutanea)",
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
                        "historia_enfermedad_actual": "Paciente de 51 años con HTA estadio 2 y DM2 acude por control mensual y cefalea occipital 3/10 desde ayer. Reconoce tabaquismo activo y dieta hipercalorica. PA en casa entre 160-170/100. Glucemias matutinas 180-220 mg/dL.",
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
        ],
    },

    # ── Clínica 2: Centro de Salud Norte ────────────────────────────────
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
            "Pediatría",
            "Ginecología y Obstetricia",
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
                    "ant_gineco_obstetricos": "G2P1A0C1. Menarquia a los 13 años. Ciclos regulares.",
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
                        "historia_enfermedad_actual": "Paciente de 48 años con DM2 acude a control mensual. Refiere glucemias en casa entre 130-160 mg/dL en ayunas. Buena adherencia a medicacion. Niega hipoglicemias. Sin cambios en vision ni parestesias.",
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
                        "historia_enfermedad_actual": "Paciente de 36 años previamente sano consulta por fiebre 38.4C de inicio hace 48h, acompañada de odinofagia intensa, congestion nasal, tos seca y malestar general. Niega dificultad para respirar, dolor de oido o erupcion cutanea.",
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
                        "historia_enfermedad_actual": "Paciente de 41 años con lumbalgia mecanica cronica de 4 años de evolucion acude por agudizacion hace 3 dias tras cargar objetos pesados en mudanza. Dolor lumbar 6/10 en reposo, 9/10 al moverse. No irradia a miembros inferiores. Sin parestesias ni alteracion de esfinteres.",
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
        ],
    },

    # ── Clínica 3: Policlinica Santa Rosa ───────────────────────────────
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
            "Ginecología y Obstetricia",
            "Dermatología",
            "Endocrinología",
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
                "username": "lab_srosa", "password": "12345678",
                "first_name": "Miguel", "last_name": "Barba Justiniano",
                "email": "laboratorio@srosa.test",
                "rol_grupo": "Laboratorio",
                "item_min_salud": "LAB-001", "rol": PersonalSalud.ROL_ADMIN,
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
                        "historia_enfermedad_actual": "Paciente de 38 años con asma bronquial alergica acude por disnea de 3h de evolucion desencadenada por limpieza de habitacion polvorienta. Uso de 6 puffs de salbutamol sin mejoria suficiente. Sibilancias audibles por el propio paciente.",
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
                        "observaciones": "FC 60 lpm. Paciente refiere mucho frio y estreñimiento. TSH pendiente de revision.",
                    },
                ],
                "consultas": [
                    {
                        "estado": "COMPLETADA",
                        "motivo_consulta": "Control de hipotiroidismo. Sintomas de hipofuncion tiroidea a pesar de tratamiento.",
                        "historia_enfermedad_actual": "Paciente de 44 años con hipotiroidismo en tratamiento con levotiroxina 75mcg acude por control trimestral. Refiere aumento de peso 4kg en 2 meses, cansancio extremo, intolerancia al frio, constipacion y cabello fragil. Cumple con medicacion en ayunas.",
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
                        "historia_enfermedad_actual": "Paciente de 30 años sin antecedentes ginecologicos previos acude por flujo vaginal grisaceo abundante con olor a pescado desde hace 5 dias, acompañado de prurito vulvar moderado. Niega fiebre, dolor abdominal o dispareunia. No tiene pareja estable. Ultima relacion sexual hace 3 semanas.",
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
        ],
    },
]


# ═══════════════════════════════════════════════════════════════════════════
# COMMAND
# ═══════════════════════════════════════════════════════════════════════════

class Command(BaseCommand):
    help = "Carga datos de prueba multitenant: 3 clinicas con personal y pacientes completos."

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
        self.stdout.write("Credenciales de acceso (password: Test1234!):\n")
        for clinica in CLINICAS:
            self.stdout.write(f"\n  [{clinica['tenant']['nombre']}]")
            for p in clinica["personal"]:
                self.stdout.write(f"    {p['username']:20} ({p['rol_grupo']})")

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
            if ucreado:
                user.set_password(datos["password"])
                user.save()
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
            self.stdout.write(f"  {estado} {datos['rol_grupo']}: {user.get_full_name()} ({datos['username']})")
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

            # Triajes
            triajes_creados = []
            for t_data in datos.get("triajes", []):
                triaje, tcreado = Triaje.objects.get_or_create(
                    paciente=paciente,
                    motivo_consulta_triaje=t_data["motivo_consulta_triaje"],
                    defaults={
                        "tenant":    tenant,
                        "enfermera": enfermera or medico,
                        **{k: v for k, v in t_data.items() if k != "motivo_consulta_triaje"},
                    },
                )
                triajes_creados.append(triaje)

            # Consultas
            for i, c_data in enumerate(datos.get("consultas", [])):
                triaje_asoc = triajes_creados[i] if i < len(triajes_creados) else None
                Consulta.objects.get_or_create(
                    paciente=paciente,
                    codigo_cie10_principal=c_data["codigo_cie10_principal"],
                    defaults={
                        "tenant": tenant,
                        "medico": medico,
                        "triaje": triaje_asoc,
                        **{k: v for k, v in c_data.items() if k != "codigo_cie10_principal"},
                    },
                )
