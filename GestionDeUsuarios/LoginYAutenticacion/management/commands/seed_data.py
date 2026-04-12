"""
GestionDeUsuarios/LoginYAutenticacion/management/commands/seed_data.py

Management command para cargar datos de prueba en Histolink.
Crea usuarios de prueba con cada rol, pacientes con antecedentes,
triajes y consultas médicas de ejemplo.

Uso:
    python manage.py seed_data
    python manage.py seed_data --limpiar   # Elimina datos previos del seed antes de crear
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.utils import timezone
from datetime import date, timedelta

from GestionDeUsuarios.RegistroYBusquedaDePacientes.models import Paciente
from GestionDeUsuarios.EdicionDeAntecedentesMedicos.models import Antecedente
from GestionDeUsuarios.GestionDePersonalDeSalud.models import Especialidad, PersonalSalud
from AtencionClinica.RegistroDeTriaje.models import Triaje
from AtencionClinica.ConsultaMedicaSOAP.models import Consulta


# ---------------------------------------------------------------------------
# Datos de prueba
# ---------------------------------------------------------------------------

ESPECIALIDADES_SEED = [
    "Medicina General",
    "Medicina Interna",
    "Cardiología",
    "Pediatría",
    "Ginecología y Obstetricia",
    "Cirugía General",
    "Neurología",
    "Traumatología y Ortopedia",
    "Oftalmología",
    "Dermatología",
    "Psiquiatría",
    "Radiología e Imagen",
    "Anestesiología",
    "Urgencias y Emergencias",
    "Oncología",
    "Nefrología",
    "Neumología",
    "Endocrinología",
    "Gastroenterología",
    "Reumatología",
]

USUARIOS_SEED = [
    {"username": "medico_test",    "password": "12345678", "first_name": "Carlos",   "last_name": "Mamani",   "email": "medico@gmail.test",    "rol": "Médico"},
    {"username": "enfermera_test", "password": "12345678", "first_name": "Ana",      "last_name": "Flores",   "email": "enfermera@gmail.test", "rol": "Enfermera"},
    {"username": "admin_test",     "password": "12345678", "first_name": "Roberto",  "last_name": "Vargas",   "email": "admin@gmail.test",     "rol": "Administrativo"},
]

PERSONAL_SEED = [
    {
        "username": "medico_test",
        "item_min_salud": "MED-001",
        "rol": PersonalSalud.ROL_MEDICO,
        "especialidad_nombre": "Medicina General",
        "telefono": "71234567",
    },
    {
        "username": "enfermera_test",
        "item_min_salud": "ENF-001",
        "rol": PersonalSalud.ROL_ENFERMERA,
        "especialidad_nombre": None,
        "telefono": "76543210",
    },
    {
        "username": "admin_test",
        "item_min_salud": "ADM-001",
        "rol": PersonalSalud.ROL_ADMIN,
        "especialidad_nombre": None,
        "telefono": "69876543",
    },
]

PACIENTES_SEED = [
    {
        "ci": "1234567",
        "nombres": "Juan Carlos",
        "apellido_paterno": "Quispe",
        "apellido_materno": "Mamani",
        "fecha_nacimiento": date(1980, 5, 15),
        "sexo": "M",
        "autoidentificacion": "AYMARA",
        "telefono": "71234567",
        "direccion": "Av. Montes 123, La Paz",
        "tipo_seguro": "CNS",
        "numero_asegurado": "CNS-001-2024",
        "antecedentes": {
            "grupo_sanguineo": "O+",
            "alergias": "Penicilina\nAspirinca",
            "ant_patologicos": "Diabetes tipo 2 (diagnosticada 2015)\nHipertensión arterial (HTA) desde 2018",
            "ant_no_patologicos": "Tabaquismo: 10 cigarrillos/día por 20 años\nConsumo ocasional de alcohol los fines de semana",
            "ant_quirurgicos": "Apendicectomía (2010)\nColecistectomía laparoscópica (2019)",
            "ant_familiares": "Padre: Diabetes tipo 2, fallecido por IAM\nMadre: HTA, actualmente con tratamiento\nHermano mayor: Diabetes tipo 2",
            "ant_gineco_obstetricos": "",
            "medicacion_actual": "Metformina 850mg c/12h\nEnalapril 10mg c/día\nAtorvastinina 20mg en la noche",
            "esquema_vacunacion": "Hepatitis B (serie completa 2020)\nInfluenza (2024)\nCOVID-19 (2 dosis + refuerzo, 2022)",
        },
        "triajes": [
            {
                "peso_kg": "78.5",
                "talla_cm": "168.0",
                "frecuencia_cardiaca": 88,
                "frecuencia_respiratoria": 18,
                "presion_sistolica": 145,
                "presion_diastolica": 92,
                "temperatura_celsius": "36.8",
                "saturacion_oxigeno": 97,
                "escala_dolor": 4,
                "nivel_urgencia": "AMARILLO",
                "motivo_consulta_triaje": "Paciente refiere cefalea intensa y visión borrosa desde esta mañana. Antecedente de HTA.",
                "observaciones": "PA elevada al ingreso. Se notifica al médico de guardia.",
            },
            {
                "peso_kg": "79.0",
                "talla_cm": "168.0",
                "frecuencia_cardiaca": 72,
                "frecuencia_respiratoria": 16,
                "presion_sistolica": 130,
                "presion_diastolica": 85,
                "temperatura_celsius": "36.5",
                "saturacion_oxigeno": 98,
                "escala_dolor": 2,
                "nivel_urgencia": "VERDE",
                "motivo_consulta_triaje": "Control de rutina por diabetes e hipertensión. Traer análisis de laboratorio.",
                "observaciones": "",
            },
        ],
        "consultas": [
            {
                "estado": "FIRMADA",
                "motivo_consulta": "Cefalea intensa y visión borrosa de inicio matutino. Refiere no haber tomado el antihipertensivo en los últimos 2 días.",
                "historia_enfermedad_actual": "Paciente de 44 años con HTA conocida acude por cuadro de cefalea holocraneana 8/10 de inicio a las 7am, acompañada de visión borrosa bilateral y náuseas. Niega vómitos, pérdida de conciencia o déficit neurológico focal. Refiere abandono de tratamiento por 2 días.",
                "examen_fisico": "PA: 145/92 mmHg. FC: 88 lpm. Orientado en tiempo, espacio y persona. Pupilas isocóricas y normorreactivas. Fondo de ojo: leve borramiento de papilas. Sin déficit motor ni sensitivo.",
                "impresion_diagnostica": "Crisis hipertensiva no complicada por abandono de tratamiento antihipertensivo",
                "codigo_cie10_principal": "I10",
                "descripcion_cie10": "Hipertensión esencial (primaria)",
                "plan_tratamiento": "1. Reanudar Enalapril 10mg c/día inmediatamente\n2. Captopril 25mg sublingual SOS si PA > 160/100\n3. Reposo relativo\n4. Control en 48 horas\n5. Educación sobre adherencia al tratamiento",
                "indicaciones_alta": "Tomar medicación diariamente sin omitir dosis. Dieta baja en sodio. Acudir a emergencias si presenta: dolor de pecho, dificultad para respirar, pérdida de conciencia o déficit neurológico.",
                "requiere_derivacion": False,
            },
            {
                "estado": "COMPLETADA",
                "motivo_consulta": "Control mensual de diabetes e hipertensión. Trae resultados de laboratorio.",
                "historia_enfermedad_actual": "Paciente diabético e hipertenso acude a control mensual. Refiere buena adherencia al tratamiento. Glucemias matutinas en casa entre 110-130 mg/dL. Sin síntomas de hipoglucemia. Niega poliuria, polidipsia o cambios visuales recientes.",
                "examen_fisico": "PA: 130/85 mmHg. FC: 72 lpm. Glucemia capilar: 118 mg/dL. Peso: 79 kg. IMC: 28.0. Examen de pies: sin úlceras, pulsos periféricos presentes.",
                "impresion_diagnostica": "Diabetes tipo 2 y HTA bajo control adecuado",
                "codigo_cie10_principal": "E11.9",
                "descripcion_cie10": "Diabetes mellitus tipo 2 sin complicaciones",
                "plan_tratamiento": "1. Mantener Metformina 850mg c/12h\n2. Mantener Enalapril 10mg c/día\n3. Mantener Atorvastinina 20mg noche\n4. Solicitar HbA1c, creatinina, microalbuminuria en 3 meses\n5. Derivar a oftalmología para revisión anual de fondo de ojo",
                "indicaciones_alta": "Continuar con dieta y ejercicio. Controles cada mes. Próxima cita con resultados de laboratorio.",
                "requiere_derivacion": True,
                "derivacion_destino": "Oftalmología - Hospital de 2do nivel",
                "derivacion_motivo": "Control anual de retinopatía diabética según protocolo.",
            },
        ],
    },
    {
        "ci": "7654321",
        "nombres": "Maria Elena",
        "apellido_paterno": "Condori",
        "apellido_materno": "Huanca",
        "fecha_nacimiento": date(1995, 11, 22),
        "sexo": "F",
        "autoidentificacion": "MESTIZO",
        "telefono": "76543210",
        "direccion": "Calle Comercio 456, Cochabamba",
        "tipo_seguro": "SUS",
        "numero_asegurado": "",
        "antecedentes": {
            "grupo_sanguineo": "A+",
            "alergias": "Sin alergias conocidas",
            "ant_patologicos": "Asma bronquial leve intermitente desde la infancia",
            "ant_no_patologicos": "No fuma. No consume alcohol. Sedentaria.",
            "ant_quirurgicos": "Ninguno",
            "ant_familiares": "Madre con asma bronquial\nAbuela materna con diabetes tipo 2",
            "ant_gineco_obstetricos": "G1P1A0C0. Parto vaginal 2021. FUM: hace 20 días. MAC: Pastillas anticonceptivas.",
            "medicacion_actual": "Salbutamol inhalador SOS (uso ocasional)",
            "esquema_vacunacion": "Esquema completo según carnet de salud\nInfluenza (2024)\nCOVID-19 completo (2022)",
        },
        "triajes": [
            {
                "peso_kg": "58.0",
                "talla_cm": "162.0",
                "frecuencia_cardiaca": 96,
                "frecuencia_respiratoria": 22,
                "presion_sistolica": 118,
                "presion_diastolica": 76,
                "temperatura_celsius": "37.2",
                "saturacion_oxigeno": 94,
                "escala_dolor": 5,
                "nivel_urgencia": "NARANJA",
                "motivo_consulta_triaje": "Paciente con dificultad respiratoria progresiva desde hace 2 horas. Sibilancias audibles. Usa inhalador sin mejoría.",
                "observaciones": "SpO2 94%. Se administra salbutamol nebulizado mientras espera atención médica.",
            },
        ],
        "consultas": [
            {
                "estado": "COMPLETADA",
                "motivo_consulta": "Crisis asmática moderada que no cede con broncodilatador habitual.",
                "historia_enfermedad_actual": "Paciente de 30 años con asma bronquial conocida acude por disnea progresiva de 2 horas de evolución, desencadenada por exposición a polvo al limpiar su casa. Usó salbutamol inhalador 4 puffs sin mejoría suficiente. Niega fiebre, expectoración purulenta o trauma torácico.",
                "examen_fisico": "FR: 22 rpm. SpO2: 94%. Tórax: sibilancias espiratorias difusas bilaterales. Sin tiraje intercostal. Murmullo vesicular conservado.",
                "impresion_diagnostica": "Crisis asmática moderada",
                "codigo_cie10_principal": "J45.1",
                "descripcion_cie10": "Asma predominantemente alérgica - moderada",
                "plan_tratamiento": "1. Salbutamol nebulizado 2.5mg c/20min x 3 dosis\n2. Prednisona 40mg VO dosis única\n3. Control de SpO2 cada 30 minutos\n4. Alta con Beclometasona inhalada 250mcg c/12h por 7 días",
                "indicaciones_alta": "Evitar alérgenos y polvo. Continuar salbutamol SOS. Si SpO2 baja de 92% o disnea en reposo, acudir a emergencias de inmediato. Control en 7 días.",
                "requiere_derivacion": False,
            },
        ],
    },
    {
        "ci": "9876543",
        "nombres": "Pedro Antonio",
        "apellido_paterno": "Gutierrez",
        "apellido_materno": "Reyes",
        "fecha_nacimiento": date(1965, 3, 8),
        "sexo": "M",
        "autoidentificacion": "MESTIZO",
        "telefono": "69876543",
        "direccion": "Av. Arce 789, Santa Cruz",
        "tipo_seguro": "COSSMIL",
        "numero_asegurado": "COSSMIL-5678",
        "antecedentes": {
            "grupo_sanguineo": "B+",
            "alergias": "Ibuprofeno (úlcera péptica previa)",
            "ant_patologicos": "Úlcera péptica gástrica (2016, tratada con triple terapia)\nDislipidemia mixta desde 2020",
            "ant_no_patologicos": "Ex tabaquista: 20 cig/día por 25 años, dejó en 2020\nAlcohol: consumo moderado los fines de semana",
            "ant_quirurgicos": "Herniorrafia inguinal derecha (2008)",
            "ant_familiares": "Padre: IAM, fallecido a los 58 años\nHermano: Enfermedad coronaria, bypass x2 (2022)",
            "ant_gineco_obstetricos": "",
            "medicacion_actual": "Omeprazol 20mg c/día en ayunas\nAtorvastinina 40mg en la noche\nAAS 100mg c/día",
            "esquema_vacunacion": "Hepatitis B (serie completa)\nInfluenza anual\nNeumococo (2023)",
        },
        "triajes": [
            {
                "peso_kg": "88.0",
                "talla_cm": "175.0",
                "frecuencia_cardiaca": 102,
                "frecuencia_respiratoria": 20,
                "presion_sistolica": 160,
                "presion_diastolica": 98,
                "temperatura_celsius": "36.6",
                "saturacion_oxigeno": 96,
                "escala_dolor": 7,
                "nivel_urgencia": "NARANJA",
                "motivo_consulta_triaje": "Dolor opresivo en pecho irradiado a brazo izquierdo. Inicio hace 45 minutos en reposo. Sudoración fría.",
                "observaciones": "Signos de alarma cardiovascular. Notificado médico de urgencias. ECG solicitado de inmediato.",
            },
        ],
        "consultas": [
            {
                "estado": "FIRMADA",
                "motivo_consulta": "Dolor torácico opresivo irradiado a brazo izquierdo con sudoración fría de 45 minutos de evolución.",
                "historia_enfermedad_actual": "Paciente masculino de 61 años con múltiples FRCV (ex tabaquista, dislipidemia, antecedente familiar de IAM precoz) acude por dolor precordial opresivo 7/10 de inicio brusco en reposo, irradiado a brazo izquierdo y mandíbula, acompañado de diaforesis y náuseas. Toma AAS 100mg como medicación habitual.",
                "examen_fisico": "FC: 102 lpm. PA: 160/98 mmHg. FR: 20 rpm. SpO2: 96%. Paciente sudoroso, ansioso. Tonos cardíacos rítmicos sin soplos. Pulmones limpios. ECG: elevación del segmento ST en V2-V5.",
                "impresion_diagnostica": "Síndrome coronario agudo con elevación del ST (SCACEST). Infarto agudo de miocardio anterior.",
                "codigo_cie10_principal": "I21.0",
                "descripcion_cie10": "Infarto agudo de miocardio transmural de la pared anterior",
                "plan_tratamiento": "1. AAS 300mg masticable STAT\n2. Clopidogrel 600mg VO STAT\n3. Heparina sódica IV según peso\n4. Morfina 2-4mg IV SOS dolor\n5. O2 suplementario si SpO2 < 94%\n6. Activación de código infarto — cateterismo de urgencia",
                "indicaciones_alta": "Paciente derivado a UCI cardiológica para cateterismo urgente.",
                "requiere_derivacion": True,
                "derivacion_destino": "UCI Cardiológica — Hospital de 3er nivel",
                "derivacion_motivo": "SCACEST confirmado por ECG. Requiere cateterismo de urgencia e ICP primaria dentro de las 90 minutos.",
            },
        ],
    },
]


class Command(BaseCommand):
    help = "Carga datos de prueba: usuarios por rol, pacientes con antecedentes, triajes y consultas."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limpiar",
            action="store_true",
            help="Elimina los datos de seed previos antes de recrearlos.",
        )

    def handle(self, *args, **options):
        if options["limpiar"]:
            self._limpiar()

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Seed de datos Histolink ===\n"))

        self._crear_especialidades()
        usuarios  = self._crear_usuarios()
        medico    = usuarios.get("medico_test")
        enfermera = usuarios.get("enfermera_test")

        self._crear_personal(usuarios)
        self._crear_pacientes(medico, enfermera)

        self.stdout.write(self.style.SUCCESS("\n✓ Seed completado exitosamente.\n"))
        self.stdout.write("Credenciales de acceso:")
        for u in USUARIOS_SEED:
            self.stdout.write(f"  {u['username']} / {u['password']}  ({u['rol']})")
        self.stdout.write("")

    # ------------------------------------------------------------------
    def _limpiar(self):
        self.stdout.write(self.style.WARNING("Limpiando datos previos del seed..."))
        cis = [p["ci"] for p in PACIENTES_SEED]
        eliminados, _ = Paciente.objects.filter(ci__in=cis).delete()
        self.stdout.write(f"  Pacientes (y sus datos relacionados) eliminados: {eliminados}")

        usernames = [u["username"] for u in USUARIOS_SEED]
        u_eliminados, _ = User.objects.filter(username__in=usernames).delete()
        self.stdout.write(f"  Usuarios eliminados: {u_eliminados}")

        e_eliminados, _ = Especialidad.objects.filter(nombre__in=ESPECIALIDADES_SEED).delete()
        self.stdout.write(f"  Especialidades eliminadas: {e_eliminados}")

    # ------------------------------------------------------------------
    def _crear_especialidades(self):
        self.stdout.write(self.style.MIGRATE_HEADING("Creando especialidades..."))
        creadas = 0
        for nombre in ESPECIALIDADES_SEED:
            _, created = Especialidad.objects.get_or_create(nombre=nombre)
            if created:
                creadas += 1
        # Invalidar caché para que el API devuelva la lista actualizada
        try:
            from django.core.cache import caches
            caches["especialidad_cache"].delete("especialidades:list:v1")
            self.stdout.write("  · Caché de especialidades invalidado")
        except Exception:
            pass
        self.stdout.write(self.style.SUCCESS(f"  ✓ {creadas} especialidades nuevas  ({len(ESPECIALIDADES_SEED)} en total)"))

    # ------------------------------------------------------------------
    def _crear_personal(self, usuarios: dict):
        self.stdout.write(self.style.MIGRATE_HEADING("\nCreando perfiles de personal de salud..."))
        for datos in PERSONAL_SEED:
            user = usuarios.get(datos["username"])
            if not user:
                self.stdout.write(self.style.WARNING(f"  · Usuario '{datos['username']}' no encontrado, omitido."))
                continue

            if PersonalSalud.objects.filter(user=user).exists():
                self.stdout.write(f"  · Ya existe perfil para: {user.username}")
                continue

            especialidad = None
            if datos["especialidad_nombre"]:
                especialidad = Especialidad.objects.filter(nombre=datos["especialidad_nombre"]).first()

            PersonalSalud.objects.create(
                user=user,
                item_min_salud=datos["item_min_salud"],
                rol=datos["rol"],
                especialidad=especialidad,
                telefono=datos.get("telefono"),
            )
            self.stdout.write(self.style.SUCCESS(f"  ✓ Personal: {user.get_full_name()} ({datos['rol']})"))

    # ------------------------------------------------------------------
    def _crear_usuarios(self):
        self.stdout.write(self.style.MIGRATE_HEADING("Creando usuarios de prueba..."))
        resultado = {}

        for datos in USUARIOS_SEED:
            try:
                grupo = Group.objects.get(name=datos["rol"])
            except Group.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f"  ✗ Rol '{datos['rol']}' no existe. Ejecuta primero: python manage.py create_groups"
                ))
                continue

            user, created = User.objects.get_or_create(
                username=datos["username"],
                defaults={
                    "first_name": datos["first_name"],
                    "last_name":  datos["last_name"],
                    "email":      datos["email"],
                    "is_active":  True,
                },
            )
            if created:
                user.set_password(datos["password"])
                user.save()
                user.groups.add(grupo)
                self.stdout.write(self.style.SUCCESS(f"  ✓ Creado: {user.username} ({datos['rol']})"))
            else:
                self.stdout.write(f"  · Ya existe: {user.username}")

            resultado[datos["username"]] = user

        return resultado

    # ------------------------------------------------------------------
    def _crear_pacientes(self, medico, enfermera):
        self.stdout.write(self.style.MIGRATE_HEADING("\nCreando pacientes con expediente completo..."))

        for datos in PACIENTES_SEED:
            paciente, created = Paciente.objects.get_or_create(
                ci=datos["ci"],
                ci_complemento="",
                defaults={
                    "nombres":            datos["nombres"],
                    "apellido_paterno":   datos["apellido_paterno"],
                    "apellido_materno":   datos["apellido_materno"],
                    "fecha_nacimiento":   datos["fecha_nacimiento"],
                    "sexo":               datos["sexo"],
                    "autoidentificacion": datos["autoidentificacion"],
                    "telefono":           datos["telefono"],
                    "direccion":          datos["direccion"],
                    "tipo_seguro":        datos["tipo_seguro"],
                    "numero_asegurado":   datos.get("numero_asegurado", ""),
                    "creado_por":         medico,
                },
            )

            nombre_completo = f"{datos['nombres']} {datos['apellido_paterno']}"

            if not created:
                self.stdout.write(f"  · Paciente ya existe: {nombre_completo} (CI: {datos['ci']})")
            else:
                self.stdout.write(self.style.SUCCESS(f"  ✓ Paciente: {nombre_completo} (CI: {datos['ci']})"))

            # Antecedentes (el signal ya los crea vacíos — solo actualizamos)
            ant_data = datos.get("antecedentes", {})
            if ant_data:
                ant, _ = Antecedente.objects.get_or_create(paciente=paciente)
                for campo, valor in ant_data.items():
                    setattr(ant, campo, valor)
                ant.ultima_actualizacion_por = medico
                ant.save()
                self.stdout.write(f"    → Antecedentes actualizados")

            # Triajes
            triajes_creados = []
            for i, t_data in enumerate(datos.get("triajes", [])):
                if not Triaje.objects.filter(paciente=paciente, motivo_consulta_triaje=t_data["motivo_consulta_triaje"]).exists():
                    triaje = Triaje.objects.create(
                        paciente=paciente,
                        enfermera=enfermera if enfermera else medico,
                        **t_data,
                    )
                    triajes_creados.append(triaje)
                    self.stdout.write(f"    → Triaje {i+1} creado ({t_data['nivel_urgencia']})")
                else:
                    triaje = Triaje.objects.filter(
                        paciente=paciente,
                        motivo_consulta_triaje=t_data["motivo_consulta_triaje"]
                    ).first()
                    triajes_creados.append(triaje)
                    self.stdout.write(f"    · Triaje {i+1} ya existe")

            # Consultas
            for i, c_data in enumerate(datos.get("consultas", [])):
                if not Consulta.objects.filter(paciente=paciente, codigo_cie10_principal=c_data["codigo_cie10_principal"]).exists():
                    triaje_asoc = triajes_creados[i] if i < len(triajes_creados) else None
                    Consulta.objects.create(
                        paciente=paciente,
                        medico=medico if medico else enfermera,
                        triaje=triaje_asoc,
                        **c_data,
                    )
                    self.stdout.write(f"    → Consulta {i+1} creada ({c_data['codigo_cie10_principal']})")
                else:
                    self.stdout.write(f"    · Consulta {i+1} ya existe ({c_data['codigo_cie10_principal']})")
