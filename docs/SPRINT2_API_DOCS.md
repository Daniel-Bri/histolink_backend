# Documentación API - Sprint 2

## Sistema de Información Clínico Inteligente

**Versión:** 1.0.0  
**Fecha:** 2026-05-03  
**Sprint:** 2 - Flujo de Atención Clínica

---

## Índice

- [Autenticación](#autenticación)
- [Estado de implementación en el repositorio](#estado-de-implementación-en-el-repositorio)
- [1. Fichas (Apertura y Cola de Atención)](#1-fichas-apertura-y-cola-de-atención)
- [2. Triaje (Registro con IA)](#2-triaje-registro-con-ia)
- [3. Consultas SOAP](#3-consultas-soap)
- [4. Recetas Médicas](#4-recetas-médicas)
- [5. Órdenes de Estudio](#5-órdenes-de-estudio)
- [Paginación y errores comunes](#paginación-y-errores-comunes)

---

## Autenticación

Todas las rutas documentadas bajo `/api/` (excepto los endpoints públicos de autenticación) requieren JWT en la cabecera:

```http
Authorization: Bearer <access_token>
```

**Endpoints típicos de auth** (prefijo `api/auth/`):

| Método | Ruta | Descripción |
|:---|:---|:---|
| POST | `/api/auth/login/` | Obtiene `access` y `refresh` (y datos de usuario según vista personalizada) |
| POST | `/api/auth/token/` | Token JWT estándar (simplejwt) |
| POST | `/api/auth/token/refresh/` | Renueva access con refresh |
| POST | `/api/auth/logout/` | Invalida refresh (blacklist) |

Duración orientativa (según `kardex/settings.py`): access ~15 min; refresh ~30 días con rotación.

---

## Estado de implementación en el repositorio

| Prefijo API | Estado |
|:---|:---|
| `/api/fichas/` | **Implementado y registrado** en `kardex/urls.py` → `AtencionClinica.AperturaFichaYColaDeAtencion` |
| `/api/ordenes-estudio/` | **Implementado y registrado** → `AtencionClinica.SolicitudDeEstudios` |
| `/api/triaje/` | **No registrado**: `RegistroDeTriaje/urls.py` está vacío; `views.py` pendiente |
| `/api/consultas/` | **No registrado**: `ConsultaMedicaSOAP/urls.py` está vacío; `views.py` pendiente |
| `/api/recetas/` | **No registrado**: `EmisionDeRecetaMedica/urls.py` está vacío; `views.py` pendiente |

Las secciones 2–4 describen el **contrato previsto** según modelos Django (`Triaje`, `Consulta`, `Receta`, `DetalleReceta`) y la planificación del Sprint; los nombres de campos JSON pueden alinearse con el modelo al implementar serializers.

**Paginación:** No hay `PageNumberPagination` configurada globalmente en `REST_FRAMEWORK`. Los listados devuelven un **array JSON** de objetos (salvo que se añada paginación al ViewSet). Si en el futuro se activa paginación DRF, las respuestas usarán `count`, `next`, `previous`, `results`.

---

## 1. Fichas (Apertura y Cola de Atención)

**Permisos (implementación actual):** `IsAuthenticated` — cualquier usuario autenticado puede usar el CRUD según las reglas del modelo `Ficha` (validación en `full_clean` / `save`).

**Base path:** `/api/fichas/`

---

### `GET /api/fichas/`

**Descripción:** Lista fichas de atención con filtros opcionales.  
**Permisos:** Usuario autenticado.

**Parámetros de query:**

| Parámetro | Tipo | Requerido | Descripción |
|:---|:---|:---:|:---|
| `incluir_inactivas` | boolean (`true`/`1`/`yes`) | No | Incluye fichas con borrado lógico (`esta_activa=false`) |
| `estado` | string | No | Filtra por estado (`ABIERTA`, `EN_TRIAJE`, `EN_ATENCION`, `CERRADA`, `CANCELADA`) |
| `paciente` | integer | No | ID del paciente |
| `en_curso` | boolean | No | Solo estados ABIERTA, EN_TRIAJE, EN_ATENCION |
| `fecha_desde` | date/datetime | No | Inicio de rango sobre `fecha_apertura` (YYYY-MM-DD o ISO) |
| `fecha_hasta` | date/datetime | No | Fin de rango sobre `fecha_apertura` |

**Código:** `200 OK`

**Respuesta (ejemplo):**

```json
[
  {
    "id": 1,
    "correlativo": "FICHA-2026-00001",
    "paciente": { "id": 5, "nombre_completo": "Ana Pérez", "ci": "11223344" },
    "paciente_id": null,
    "profesional_apertura": { "id": 2, "nombre": "Dr. X" },
    "estado": "ABIERTA",
    "fecha_apertura": "2026-05-03T10:00:00Z",
    "fecha_inicio_atencion": null,
    "fecha_cierre": null,
    "esta_activa": true,
    "creado_en": "2026-05-03T10:00:00Z",
    "actualizado_en": "2026-05-03T10:00:00Z"
  }
]
```

---

### `POST /api/fichas/`

**Descripción:** Crea una ficha; asigna `profesional_apertura` desde el `PersonalSalud` del usuario autenticado.  
**Permisos:** Usuario autenticado con perfil `PersonalSalud` (si no hay perfil, error de validación al crear).

**Body (JSON):**

| Campo | Tipo | Requerido | Descripción |
|:---|:---|:---:|:---|
| `paciente_id` | integer | Sí | ID de paciente activo |

**Ejemplo:**

```json
{
  "paciente_id": 5
}
```

**Código:** `201 Created`

**Respuesta:** Objeto ficha (mismo esquema que GET detalle, con `paciente` anidado y correlativo generado).

---

### `GET /api/fichas/{id}/`

**Descripción:** Detalle de una ficha.  
**Permisos:** Usuario autenticado.

**Parámetros de ruta:**

| Parámetro | Tipo | Requerido | Descripción |
|:---|:---|:---:|:---|
| `id` | integer | Sí | ID de la ficha |

**Código:** `200 OK` | `404 Not Found`

---

### `PUT /api/fichas/{id}/` y `PATCH /api/fichas/{id}/`

**Descripción:** Actualización completa o parcial (campos editables según serializer; correlativo y varios campos son solo lectura en respuesta).  
**Permisos:** Usuario autenticado.

**Body (PATCH — campos típicos si el serializer los expone como editables):** Depende de campos no `read_only` en `FichaSerializer` (en la implementación actual la mayoría de metadatos son read-only; revisar serializer para lista exacta).

**Código:** `200 OK`

---

### `DELETE /api/fichas/{id}/`

**Descripción:** Borrado **lógico** (`esta_activa=false`), no elimina el registro.  
**Permisos:** Usuario autenticado.

**Código:** `204 No Content` (típico DRF) o según `DestroyAPIView` — verificar respuesta en cliente.

---

### `PATCH /api/fichas/{id}/cambiar-estado/`

**Descripción:** Transición de estado con validación en modelo (`Ficha`).  
**Permisos:** Usuario autenticado.

**Parámetros de ruta:**

| Parámetro | Tipo | Requerido | Descripción |
|:---|:---|:---:|:---|
| `id` | integer | Sí | ID de la ficha |

**Body (JSON):**

| Campo | Tipo | Requerido | Descripción |
|:---|:---|:---:|:---|
| `estado` | string | Sí | Nuevo estado (`ABIERTA`, `EN_TRIAJE`, `EN_ATENCION`, `CERRADA`, `CANCELADA`) según transiciones válidas |

**Código:** `200 OK`

---

## 2. Triaje (Registro con IA)

> **Nota:** Rutas **no expuestas** aún. La siguiente documentación refleja el **modelo** `Triaje` y el **contrato previsto** para el Sprint (incl. campos de IA en respuesta cuando se integre `ServicioML` / NLP).

**Base path previsto:** `/api/triaje/`

**Permisos previstos:** Enfermería (registro), lectura posible para Médico / roles de atención (definir en `permission_classes` al implementar).

---

### `GET /api/triaje/` (previsto)

**Descripción:** Listar registros de triaje con filtros.  
**Parámetros de query (propuesta):** `ficha`, `nivel_urgencia`, `fecha_desde`, `fecha_hasta`.

---

### `POST /api/triaje/` (previsto)

**Descripción:** Registrar triaje vinculado a una ficha; la respuesta puede enriquecerse con salida de IA.

**Body (JSON) — alineado al modelo `Triaje`:**

| Campo | Tipo | Requerido | Descripción |
|:---|:---|:---:|:---|
| `ficha` | integer | Sí | ID de ficha (OneToOne: una ficha → un triaje) |
| `motivo_consulta_triaje` | string | No | Texto para NLP / motivo |
| `peso_kg`, `talla_cm` | number | No | IMC calculado vía propiedad |
| `frecuencia_cardiaca` | integer | No | 20–300 |
| `frecuencia_respiratoria` | integer | No | 5–80 |
| `presion_sistolica`, `presion_diastolica` | integer | No | Rangos según modelo |
| `temperatura_celsius` | number | No | 25–45 |
| `saturacion_oxigeno` | integer | No | 50–100 |
| `glucemia` | number | No | Opcional |
| `escala_dolor` | integer | No | 0–10 |
| `nivel_urgencia` | string | No | `ROJO` / `NARANJA` / `AMARILLO` / `VERDE` / `AZUL` |
| `observaciones` | string | No | |

El modelo usa `enfermera` → usuario autenticado al crear (no en body).

**Respuesta con IA (campos adicionales previstos en API, no persistidos todos en BD):**

| Campo | Tipo | Descripción |
|:---|:---|:---|
| `nivel_asignado` | string | Nivel final aplicado (manual o tras reglas + IA) |
| `nivel_sugerido_ia` | string | Sugerencia del modelo NLP |
| `confianza_ia` | float | 0.0–1.0 |
| `probabilidades_ia` | object | Mapa nivel → probabilidad |

**Ejemplo de respuesta enriquecida (contrato Sprint):**

```json
{
  "id": 42,
  "ficha": 15,
  "motivo_consulta_triaje": "Dolor de cabeza intenso desde hace 3 días",
  "presion_sistolica": 130,
  "presion_diastolica": 85,
  "frecuencia_cardiaca": 95,
  "saturacion_oxigeno": 98,
  "temperatura_celsius": 37.2,
  "nivel_urgencia": "AMARILLO",
  "nivel_asignado": "AMARILLO",
  "nivel_sugerido_ia": "AMARILLO",
  "confianza_ia": 0.87,
  "probabilidades_ia": {
    "ROJO": 0.02,
    "NARANJA": 0.05,
    "AMARILLO": 0.87,
    "VERDE": 0.04,
    "AZUL": 0.02
  },
  "hora_triaje": "2026-05-03T10:30:00Z"
}
```

> **Rendimiento:** La clasificación NLP puede sumar ~1–2 s; documentar timeout en cliente.

---

### `GET /api/triaje/{id}/` (previsto)

**Descripción:** Detalle de triaje.

---

### `PUT/PATCH /api/triaje/{id}/` (previsto)

**Descripción:** Actualizar triaje si las reglas de negocio lo permiten (definir al implementar).

---

## 3. Consultas SOAP

> **Nota:** Rutas **no expuestas** aún. Basado en modelo `Consulta`.

**Base path previsto:** `/api/consultas/`

**Permisos previstos:** Principalmente Médico para crear/editar; lectura según rol.

---

### `GET /api/consultas/` (previsto)

**Descripción:** Listado con filtros propuestos: `ficha`, `estado`, `medico`, `fecha_desde`, `fecha_hasta`.

---

### `POST /api/consultas/` (previsto)

**Descripción:** Crear consulta SOAP asociada a ficha.

**Body (JSON) — campos principales del modelo:**

| Campo | Tipo | Requerido | Descripción |
|:---|:---|:---:|:---|
| `ficha` | integer | Sí | ID de ficha |
| `triaje` | integer | No | ID triaje (OneToOne opcional) |
| `motivo_consulta` | string | Sí | SOAP S |
| `historia_enfermedad_actual` | string | Sí | SOAP S |
| `examen_fisico` | string | No | SOAP O |
| `impresion_diagnostica` | string | Sí | SOAP A |
| `codigo_cie10_principal` | string | Sí | SNIS Bolivia |
| `codigo_cie10_secundario` | string | No | |
| `descripcion_cie10` | string | No | |
| `plan_tratamiento` | string | No | SOAP P |
| `indicaciones_alta` | string | No | |
| `requiere_derivacion` | boolean | No | |
| `derivacion_destino`, `derivacion_motivo` | string | No | |

`medico` se asigna desde el usuario autenticado (patrón habitual).

**Código:** `201 Created`

---

### `GET /api/consultas/{id}/` · `PUT/PATCH /api/consultas/{id}/` (previsto)

**Descripción:** Detalle y actualización mientras `estado` permita edición (`BORRADOR` típicamente).

**Estados:** `BORRADOR` → `COMPLETADA` → `FIRMADA`.

---

### `PATCH /api/consultas/{id}/firmar/` (previsto)

**Descripción:** Firma digital de la consulta: rellena `hash_documento`, `firmada_por`, `firmada_en` (y posible tarea Celery blockchain según arquitectura).

**Código:** `200 OK` | `400/409` si no cumple precondiciones.

---

## 4. Recetas Médicas

> **Nota:** Rutas **no expuestas** aún. Modelos `Receta` y `DetalleReceta`.

**Base path previsto:** `/api/recetas/`

---

### `GET /api/recetas/` (previsto)

Filtros propuestos: `consulta`, `estado`, `fecha_desde`, `fecha_hasta`, `medico`.

---

### `POST /api/recetas/` (previsto)

**Descripción:** Emitir receta con líneas de medicamentos.

**Body (JSON) — propuesta:**

| Campo | Tipo | Requerido | Descripción |
|:---|:---|:---:|:---|
| `consulta` | integer | Sí | ID consulta |
| `observaciones` | string | No | |
| `detalles` | array | Sí | Lista de ítems tipo `DetalleReceta` |

**Elemento de `detalles`:**

| Campo | Tipo | Requerido | Descripción |
|:---|:---|:---:|:---|
| `medicamento` | string | Sí | DCI |
| `concentracion` | string | No | |
| `forma_farmaceutica` | string | No | |
| `via_administracion` | string | No | `VO`, `IV`, … |
| `dosis` | string | Sí | |
| `frecuencia` | string | Sí | |
| `duracion` | string | Sí | |
| `cantidad_total` | string | No | |
| `instrucciones` | string | No | |
| `orden` | integer | No | Orden de impresión |

`numero_receta`, `medico`, `fecha_emision` suelen generarse en servidor.

---

### `GET /api/recetas/{id}/` · `PUT/PATCH /api/recetas/{id}/` (previsto)

Actualización según estado (`EMITIDA`, `DISPENSADA`, `ANULADA`).

---

### `PATCH /api/recetas/{id}/dispensar/` (previsto)

**Descripción:** Marca dispensación en farmacia: `estado=DISPENSADA`, `dispensada_por`, `fecha_dispensacion`.

**Permisos previstos:** Rol Farmacia / Administrativo (definir).

---

## 5. Órdenes de Estudio

**Estado:** **Implementado** y registrado bajo `/api/ordenes-estudio/`.

**Permisos (resumen `OrdenEstudioPermission`):**

| Acción | Roles |
|:---|:---|
| `create` | Grupo **Médico** o admin-like / superusuario |
| `list`, `retrieve` | Médico, **Laboratorio**, **Enfermera**, admin-like |
| `update`/`partial_update` | Médico (solo si es el solicitante y orden no terminal) o admin |
| `cola_laboratorio`, `cambiar_estado` | **Laboratorio** o admin-like |
| `destroy` | Admin-like / superusuario (borrado lógico `esta_activa`) |

---

### `GET /api/ordenes-estudio/`

**Descripción:** Lista órdenes con filtros; para **Médico** no admin, solo órdenes donde él es `medico_solicitante`.

**Parámetros de query:**

| Parámetro | Tipo | Requerido | Descripción |
|:---|:---|:---:|:---|
| `incluir_inactivas` | boolean | No | Incluye borrado lógico |
| `estado` | string | No | `SOLICITADA`, `EN_PROCESO`, `COMPLETADA`, `ANULADA` |
| `solo_urgentes` | boolean | No | Solo `urgente=true` |
| `urgente` | boolean | No | `true`/`false` filtra por urgencia |
| `tipo` | string | No | `LAB`, `RX`, `ECO`, … |
| `consulta` | integer | No | ID consulta |
| `pendientes` | boolean | No | Excluye `COMPLETADA` y `ANULADA` |
| `fecha_desde`, `fecha_hasta` | date/datetime | No | Sobre `fecha_solicitud` |

**Código:** `200 OK`

**Respuesta:** Array de ítems con campos entre otros: `id`, `correlativo_orden`, `tipo`, `tipo_label`, `urgente`, `estado`, `estado_label`, `fecha_solicitud`, `paciente_nombre`.

---

### `POST /api/ordenes-estudio/`

**Descripción:** Crea orden; asigna `medico_solicitante` desde el usuario autenticado.

**Body (JSON):**

| Campo | Tipo | Requerido | Descripción |
|:---|:---|:---:|:---|
| `consulta_id` | integer | Sí | ID de consulta |
| `tipo` | string | Sí | Tipo de estudio |
| `descripcion` | string | Sí | |
| `indicacion_clinica` | string | Sí | |
| `urgente` | boolean | No | Default false |
| `motivo_urgencia` | string | Condicional | Obligatorio si `urgente=true` |

**Código:** `201 Created`

**Respuesta (ejemplo):** `id`, `correlativo_orden`, `consulta`, `paciente` (nombre), `tipo`, `descripcion`, `urgente`, `estado`, `fecha_solicitud`, `medico_solicitante` (nombre).

---

### `GET /api/ordenes-estudio/{id}/`

**Descripción:** Detalle completo (`OrdenEstudioDetailSerializer`).

---

### `PUT/PATCH /api/ordenes-estudio/{id}/`

**Descripción:** Médico: tipo, descripción, indicación, urgencia (sin estado terminal); Admin: campos adicionales incl. estado y archivos.

---

### `PATCH /api/ordenes-estudio/{id}/cambiar-estado/`

**Descripción:** Cambio de estado operativo (Laboratorio). Valida transiciones en modelo.

**Body (JSON o multipart si hay archivo):**

| Campo | Tipo | Requerido | Descripción |
|:---|:---|:---:|:---|
| `estado` | string | Sí | `EN_PROCESO`, `COMPLETADA`, `ANULADA` según transición |
| `resultado_texto` | string | No | |
| `resultado_archivo` | file | No | Adjunto |
| `tecnico_responsable_id` | integer | No | PK `PersonalSalud`; si no se envía en `EN_PROCESO`, se intenta asignar el laboratorista autenticado |

**Código:** `200 OK`

---

### `GET /api/ordenes-estudio/cola-laboratorio/`

**Descripción:** Cola prioritaria: pendientes no completados ni anulados; orden por urgencia y fecha.

**Respuesta (ejemplo):**

```json
{
  "urgentes": [],
  "normales": [],
  "en_proceso": [],
  "total_pendientes": 0
}
```

---

## Paginación y errores comunes

**Paginación:** Ver [Estado de implementación](#estado-de-implementación-en-el-repositorio).

**Códigos de error típicos DRF:**

| Código | Descripción |
|:---|:---|
| `400 Bad Request` | Validación de serializer o modelo |
| `401 Unauthorized` | Sin JWT o token inválido |
| `403 Forbidden` | Rol insuficiente (`OrdenEstudioPermission`, etc.) |
| `404 Not Found` | Recurso inexistente |
| `409 Conflict` | Posible en reglas de negocio según implementación |

**Ejemplo error 400 (orden urgente sin motivo):**

```json
{
  "motivo_urgencia": ["Debe especificar el motivo de urgencia."]
}
```

---

*Documento generado a partir del código en `histolink_backend` (2026-05-03). Actualizar al registrar nuevas rutas en `kardex/urls.py`.*
