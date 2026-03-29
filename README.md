# 🏥 Histolink — Sistema de Gestión Clínica

**Backend API** construido con Django + Django REST Framework + JWT.

---

## 🚀 Inicio Rápido

### Requisitos Previos

| Herramienta | Versión     |
|-------------|-------------|
| Python      | 3.11+       |
| PostgreSQL  | 14+         |

### Instalación Automática

```bash
python setup_env.py
```

Este script hace todo automáticamente:
1. ✅ Crea el entorno virtual (`./venv`)
2. ✅ Instala todas las dependencias
3. ✅ Crea la base de datos `histolink` en PostgreSQL
4. ✅ Ejecuta las migraciones de Django
5. ✅ Crea los 7 roles clínicos del sistema

### Instalación Manual

```bash
# 1. Crear entorno virtual
python -m venv venv

# 2. Activar (Windows)
.\venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Crear la BD en PostgreSQL
#    CREATE DATABASE histolink;

# 5. Migraciones
python manage.py migrate

# 6. Crear roles del sistema
python manage.py create_groups

# 7. (Opcional) Crear superusuario para /admin/
python manage.py createsuperuser
```

---

## ▶️ Iniciar el Servidor

```bash
# Activar entorno virtual
.\venv\Scripts\activate          # Windows
source venv/bin/activate         # Linux/Mac

# Ejecutar servidor de desarrollo
python manage.py runserver
```

El servidor inicia en **http://127.0.0.1:8000**

---

## 📡 API de Autenticación — Endpoints

Base URL: `http://127.0.0.1:8000/api/auth/`

### 📖 Documentación Interactiva

DRF incluye una **API navegable** (como Swagger). Abrí cualquier endpoint en el navegador y vas a ver un formulario interactivo para probar las peticiones:

→ **http://127.0.0.1:8000/api/auth/login/**

---

### 📋 Tabla de Endpoints

| Método | Endpoint                         | Auth     | Descripción                              |
|--------|----------------------------------|----------|------------------------------------------|
| POST   | `/api/auth/register/`            | ❌ No    | Registrar nuevo usuario                  |
| POST   | `/api/auth/login/`               | ❌ No    | Login — obtener tokens JWT               |
| POST   | `/api/auth/logout/`              | ✅ Sí    | Logout — invalidar refresh token         |
| GET    | `/api/auth/profile/`             | ✅ Sí    | Ver perfil del usuario autenticado       |
| PUT    | `/api/auth/change-password/`     | ✅ Sí    | Cambiar contraseña                       |
| POST   | `/api/auth/token/refresh/`       | ❌ No    | Renovar access token con refresh token   |
| POST   | `/api/auth/token/verify/`        | ❌ No    | Verificar si un token es válido          |

---

### 1️⃣ Registrar Usuario

```
POST /api/auth/register/
Content-Type: application/json
```

**Body:**
```json
{
  "username": "dr_lopez",
  "email": "lopez@hospital.com",
  "password": "MiPassword123!",
  "password_confirm": "MiPassword123!",
  "first_name": "Carlos",
  "last_name": "López"
}
```

**Respuesta (201):**
```json
{
  "message": "Usuario registrado exitosamente.",
  "user": {
    "id": 1,
    "username": "dr_lopez",
    "email": "lopez@hospital.com",
    "first_name": "Carlos",
    "last_name": "López",
    "is_active": true,
    "is_staff": false,
    "date_joined": "2026-03-29T21:00:00Z",
    "last_login": null,
    "groups": []
  }
}
```

---

### 2️⃣ Login (Obtener Tokens JWT)

```
POST /api/auth/login/
Content-Type: application/json
```

**Body:**
```json
{
  "username": "dr_lopez",
  "password": "MiPassword123!"
}
```

**Respuesta (200):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "refresh": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 1,
    "username": "dr_lopez",
    "email": "lopez@hospital.com",
    "first_name": "Carlos",
    "last_name": "López",
    "is_staff": false,
    "is_superuser": false,
    "groups": ["Médico"]
  }
}
```

> **⏱ Tokens:**
> - `access` expira en **15 minutos**
> - `refresh` expira en **30 días** (se rota automáticamente)

---

### 3️⃣ Usar Token en Peticiones Protegidas

Agregar el header `Authorization` con el access token:

```
GET /api/auth/profile/
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

Si el token expira, usar `/api/auth/token/refresh/` para obtener uno nuevo.

---

### 4️⃣ Renovar Access Token

```
POST /api/auth/token/refresh/
Content-Type: application/json
```

**Body:**
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Respuesta (200):**
```json
{
  "access": "eyJnuevoAccessToken...",
  "refresh": "eyJnuevoRefreshToken..."
}
```

> El refresh token viejo se invalida automáticamente (rotación + blacklist).

---

### 5️⃣ Logout (Invalidar Refresh Token)

```
POST /api/auth/logout/
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Body:**
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Respuesta (200):**
```json
{
  "message": "Sesión cerrada exitosamente."
}
```

---

### 6️⃣ Cambiar Contraseña

```
PUT /api/auth/change-password/
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Body:**
```json
{
  "old_password": "MiPassword123!",
  "new_password": "NuevaPassword456!",
  "new_password_confirm": "NuevaPassword456!"
}
```

**Respuesta (200):**
```json
{
  "message": "Contraseña actualizada exitosamente."
}
```

---

### 7️⃣ Verificar Token

```
POST /api/auth/token/verify/
Content-Type: application/json
```

**Body:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Respuesta (200):** `{}` → Token válido
**Respuesta (401):** Token inválido o expirado

---

## 👥 Roles del Sistema

El comando `python manage.py create_groups` crea estos roles en `auth_group`:

| Rol             | Descripción                                    |
|-----------------|------------------------------------------------|
| Médico          | Acceso a consultas, recetas, diagnósticos      |
| Enfermera       | Triaje, signos vitales, seguimiento            |
| Administrativo  | Registro de pacientes, citas, reportes         |
| Laboratorio     | Solicitudes y resultados de laboratorio        |
| Farmacia        | Gestión de recetas y despacho de medicamentos  |
| Auditor         | Acceso de solo lectura para auditoría          |
| Director        | Acceso completo, dashboards, estadísticas      |

Para asignar un rol a un usuario desde Django admin:
1. Ir a **http://127.0.0.1:8000/admin/**
2. Editar el usuario → sección **Grupos** → agregar el rol

---

## 🗄 Base de Datos

**PostgreSQL** — Base de datos: `histolink`

Configuración en `kardex/settings.py`:
```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "histolink",
        "USER": "postgres",
        "PASSWORD": "12345678",
        "HOST": "localhost",
        "PORT": "5432",
    }
}
```

> Para cambiar las credenciales, editar directamente el archivo `kardex/settings.py`.

---

## 📁 Estructura del Proyecto

```
histolink/
├── authentication/              # App de autenticación
│   ├── management/
│   │   └── commands/
│   │       └── create_groups.py # Comando para crear roles
│   ├── serializers.py           # Serializers (Register, Login, etc.)
│   ├── views.py                 # Vistas de la API
│   ├── urls.py                  # Rutas de /api/auth/
│   └── apps.py
├── kardex/                      # Configuración Django del proyecto
│   ├── settings.py              # Settings principal
│   ├── urls.py                  # URLs raíz
│   ├── wsgi.py
│   └── asgi.py
├── modelo_riesgo.py             # ML: Predicción de riesgos clínicos
├── modelo_triaje.py             # ML: Clasificación de prioridad de triaje
├── servicio_ml.py               # Servicio de ML
├── manage.py                    # Comando principal de Django
├── requirements.txt             # Dependencias del proyecto
├── setup_env.py                 # Script de instalación automática
└── README.md                    # Este archivo
```

---

## 🔧 Comandos Útiles

```bash
# Ejecutar servidor de desarrollo
python manage.py runserver

# Crear superusuario (admin)
python manage.py createsuperuser

# Crear roles del sistema
python manage.py create_groups

# Aplicar migraciones
python manage.py migrate

# Ver migraciones pendientes
python manage.py showmigrations

# Abrir shell de Django
python manage.py shell

# Verificar configuración
python manage.py check
```

---

## 🛡 Seguridad JWT

| Parámetro                   | Valor      | Descripción                                     |
|-----------------------------|------------|-------------------------------------------------|
| Access Token Lifetime       | 15 min     | Token de acceso corto para seguridad             |
| Refresh Token Lifetime      | 30 días    | Token de refresco de larga duración              |
| Rotate Refresh Tokens       | ✅ Sí      | Se emite un nuevo refresh en cada uso            |
| Blacklist After Rotation    | ✅ Sí      | El refresh viejo se invalida automáticamente     |
| Algorithm                   | HS256      | HMAC con SHA-256                                 |
| Auth Header                 | Bearer     | `Authorization: Bearer <token>`                  |

---

> **Histolink** — Sistema de Gestión Documental Clínico · UAGRM Grupo #13 INF412-SA
