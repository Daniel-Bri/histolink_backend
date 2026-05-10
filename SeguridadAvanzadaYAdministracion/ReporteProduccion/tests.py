from datetime import date

from django.test import SimpleTestCase

from .nlp_filtros import parsear_texto


class NlpFiltrosTests(SimpleTestCase):
    def test_caso_mario_soria_recetas_emitidas_rango_compacto(self):
        texto = "Dame el reporte del Médico Mario Soria de las recetas emitidas del primero al 9 de mayo"
        out = parsear_texto(texto, hoy=date(2026, 5, 9))
        self.assertEqual(out.get("fecha_desde"), "2026-05-01")
        self.assertEqual(out.get("fecha_hasta"), "2026-05-09")
        self.assertEqual(out.get("medico_nombre"), "Mario Soria")
        self.assertEqual(out.get("tipo_reporte"), "recetas_emitidas")

    def test_caso_mario_soria_con_frase_fecha_explicita(self):
        texto = "quiero que me dejes el reporte del Médico Mario Soria de la fecha primero de mayo al 5 de mayo"
        out = parsear_texto(texto, hoy=date(2026, 5, 9))
        self.assertEqual(out.get("fecha_desde"), "2026-05-01")
        self.assertEqual(out.get("fecha_hasta"), "2026-05-05")
        self.assertEqual(out.get("medico_nombre"), "Mario Soria")
        self.assertEqual(out.get("tipo_reporte"), "resumen_general")

    def test_tipo_reporte_consultas(self):
        texto = "Dame las consultas del médico Mario Soria del 1 al 9 de mayo"
        out = parsear_texto(texto, hoy=date(2026, 5, 9))
        self.assertEqual(out.get("tipo_reporte"), "consultas")

    def test_tipo_reporte_resumen_general(self):
        texto = "Dame el reporte general de este mes"
        out = parsear_texto(texto, hoy=date(2026, 5, 9))
        self.assertEqual(out.get("tipo_reporte"), "resumen_general")

    def test_caso_1_rango_medico_diabetes(self):
        texto = (
            "quiero que me des el reporte del 1 de mayo al 5 de mayo "
            "del médico Roberto Vargas con pacientes con diabetes"
        )
        out = parsear_texto(texto, hoy=date(2026, 5, 9))
        self.assertEqual(out.get("fecha_desde"), "2026-05-01")
        self.assertEqual(out.get("fecha_hasta"), "2026-05-05")
        self.assertEqual(out.get("medico_nombre"), "Roberto Vargas")
        self.assertEqual(out.get("codigo_cie10"), "E11")

    def test_caso_2_rojos_semana_pasada(self):
        texto = "pacientes rojos de la semana pasada"
        out = parsear_texto(texto, hoy=date(2026, 5, 9))
        self.assertEqual(out.get("nivel_urgencia"), "ROJO")
        self.assertEqual(out.get("fecha_desde"), "2026-04-27")
        self.assertEqual(out.get("fecha_hasta"), "2026-05-03")

    def test_caso_3_hipertension_doctor_abril(self):
        texto = "consultas de hipertensión del doctor Mamani en abril"
        out = parsear_texto(texto, hoy=date(2026, 5, 9))
        self.assertEqual(out.get("codigo_cie10"), "I10")
        self.assertEqual(out.get("medico_nombre"), "Mamani")
        self.assertEqual(out.get("fecha_desde"), "2026-04-01")
        self.assertEqual(out.get("fecha_hasta"), "2026-04-30")

    def test_caso_4_diabetes_este_mes(self):
        texto = "consultas de diabetes este mes"
        out = parsear_texto(texto, hoy=date(2026, 5, 9))
        self.assertEqual(out.get("codigo_cie10"), "E11")
        self.assertEqual(out.get("fecha_desde"), "2026-05-01")
        self.assertEqual(out.get("fecha_hasta"), "2026-05-09")
