# Ejemplos de uso - Sprint 2

**Base URL de ejemplo:** `http://localhost:8000`  
**Autenticación:** sustituir `<ACCESS_TOKEN>` por el token devuelto en login.

---

## 1. Login

```bash
curl -X POST "http://localhost:8000/api/auth/login/" ^
  -H "Content-Type: application/json" ^
  -d "{\"username\": \"medico1\", \"password\": \"su_password\"}"
```

En Linux/macOS use `\` en lugar de `^` para continuar líneas.

Guarde `access` del JSON de respuesta para las siguientes peticiones.

---

## 2. Abrir ficha

```bash
curl -X POST "http://localhost:8000/api/fichas/" ^
  -H "Authorization: Bearer <ACCESS_TOKEN>" ^
  -H "Content-Type: application/json" ^
  -d "{\"paciente_id\": 5}"
```

---

## 3. Registrar triaje (con IA) — *cuando la API esté cableada*

El endpoint `/api/triaje/` aún no está registrado en el proyecto; el ejemplo refleja el contrato previsto y los nombres del modelo (`motivo_consulta_triaje`, `presion_sistolica`, …).

```bash
curl -X POST "http://localhost:8000/api/triaje/" ^
  -H "Authorization: Bearer <ACCESS_TOKEN>" ^
  -H "Content-Type: application/json" ^
  -d "{\"ficha\": 1, \"motivo_consulta_triaje\": \"Dolor de cabeza intenso\", \"presion_sistolica\": 130, \"presion_diastolica\": 85, \"frecuencia_cardiaca\": 95, \"saturacion_oxigeno\": 98, \"temperatura_celsius\": 37.2}"
```

---

## 4. Consulta SOAP — *cuando la API esté cableada*

```bash
curl -X POST "http://localhost:8000/api/consultas/" ^
  -H "Authorization: Bearer <ACCESS_TOKEN>" ^
  -H "Content-Type: application/json" ^
  -d "{\"ficha\": 1, \"motivo_consulta\": \"Cefalea\", \"historia_enfermedad_actual\": \"Inicio hace 3 días\", \"impresion_diagnostica\": \"Cefalea tensional\", \"codigo_cie10_principal\": \"G44.2\", \"plan_tratamiento\": \"Analgésico según indicación\"}"
```

---

## 5. Firmar consulta — *cuando exista el endpoint*

```bash
curl -X PATCH "http://localhost:8000/api/consultas/1/firmar/" ^
  -H "Authorization: Bearer <ACCESS_TOKEN>" ^
  -H "Content-Type: application/json" ^
  -d "{}"
```

---

## 6. Emitir receta — *cuando la API esté cableada*

```bash
curl -X POST "http://localhost:8000/api/recetas/" ^
  -H "Authorization: Bearer <ACCESS_TOKEN>" ^
  -H "Content-Type: application/json" ^
  -d "{\"consulta\": 1, \"detalles\": [{\"medicamento\": \"Paracetamol\", \"concentracion\": \"500 mg\", \"via_administracion\": \"VO\", \"dosis\": \"1 tableta\", \"frecuencia\": \"cada 8 horas\", \"duracion\": \"5 días\", \"orden\": 1}]}"
```

---

## 7. Solicitar estudio (implementado)

Use el ID real de una consulta existente (`consulta_id`).

```bash
curl -X POST "http://localhost:8000/api/ordenes-estudio/" ^
  -H "Authorization: Bearer <ACCESS_TOKEN_MEDICO>" ^
  -H "Content-Type: application/json" ^
  -d "{\"consulta_id\": 1, \"tipo\": \"LAB\", \"descripcion\": \"Hemograma completo\", \"indicacion_clinica\": \"Control\", \"urgente\": true, \"motivo_urgencia\": \"Sospecha de sepsis\"}"
```

---

## 8. Cola de laboratorio (implementado)

Usuario con grupo **Laboratorio** (y perfil `PersonalSalud` si aplica).

```bash
curl -X GET "http://localhost:8000/api/ordenes-estudio/cola-laboratorio/" ^
  -H "Authorization: Bearer <ACCESS_TOKEN_LAB>"
```

---

## 9. Cambiar estado de orden (implementado)

```bash
curl -X PATCH "http://localhost:8000/api/ordenes-estudio/1/cambiar-estado/" ^
  -H "Authorization: Bearer <ACCESS_TOKEN_LAB>" ^
  -H "Content-Type: application/json" ^
  -d "{\"estado\": \"EN_PROCESO\", \"tecnico_responsable_id\": 3}"
```

Para completar con resultado en texto:

```bash
curl -X PATCH "http://localhost:8000/api/ordenes-estudio/1/cambiar-estado/" ^
  -H "Authorization: Bearer <ACCESS_TOKEN_LAB>" ^
  -H "Content-Type: application/json" ^
  -d "{\"estado\": \"COMPLETADA\", \"resultado_texto\": \"Hemograma dentro de parámetros normales\"}"
```

---

## Flujo mínimo actualmente ejecutable en backend

1. `POST /api/auth/login/`  
2. `POST /api/fichas/` con `paciente_id`  
3. Crear consulta en BD o vía futura API; obtener `consulta_id`  
4. `POST /api/ordenes-estudio/`  
5. Laboratorio: `GET .../cola-laboratorio/` y `PATCH .../cambiar-estado/`

---

*Sprint 2 — Histolink (2026-05-03)*
