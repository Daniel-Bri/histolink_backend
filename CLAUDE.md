# CLAUDE.md — histolink_backend

## Setup & Run

```bash
python -m venv venv
.\venv\Scripts\activate          # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py create_groups   # Crea los 7 roles clínicos
python manage.py createsuperuser
python manage.py runserver       # http://127.0.0.1:8000
```

**DB:** PostgreSQL — nombre `histolink`, user `postgres`, pass `12345678`, port `5432`.

## Comandos útiles

```bash
python manage.py makemigrations          # Detecta cambios en models
python manage.py makemigrations <App>    # Solo una app
python manage.py makemigrations --merge  # Resuelve conflictos de migraciones
python manage.py migrate
python manage.py create_groups           # Recrea los 7 roles si se pierden
python manage.py createsuperuser
python manage.py check                   # Valida configuración Django
python manage.py shell

# Entrenar modelos ML (escribe en ml/modelos_guardados/)
python ml/modelo_riesgo.py
python ml/modelo_triaje.py
```

## Estructura de apps

```
kardex/                                  ← Config: settings.py, urls.py raíz
Tenants/                                 ← Multitenant (Tenant, ConfiguracionTenant, GestionAnual)
GestionDeUsuarios/
  LoginYAutenticacion/                   ← CU1: JWT login/logout/register/profile
  GestionDePersonalDeSalud/              ← CU2: PersonalSalud + especialidades
  RegistroYBusquedaDePacientes/          ← CU3: Paciente CRUD
  VisualizacionDelExpediente/            ← CU4: Expediente completo
  EdicionDeAntecedentesMedicos/          ← CU5: Antecedentes
AtencionClinica/
  AperturaFichaYColaDeAtencion/          ← CU6: Ficha + cola de atención
  RegistroDeTriaje/                      ← CU7: Triaje + clasificación IA
  ConsultaMedicaSOAP/                    ← CU8: Consulta SOAP
  EmisionDeRecetaMedica/                 ← CU9: Recetas
  SolicitudDeEstudios/                   ← CU10: Órdenes de estudio
  FirmaDigitalDeConsulta/                ← CU11: Firma digital
IA_Blockchain/                           ← CU12–CU15: Stubs sin implementar
SeguridadAvanzadaYAdministracion/
  BreakGlass_Solicitud/                  ← CU16
  BreakGlass_Aprobacion/                 ← CU17
  GestionDePermisosPaciente/             ← CU18
  PanelDeAuditoriaYReportesSNIS/         ← CU20
  ReporteProduccion/                     ← CU22
  BackupRestore/                         ← Backup/Restore + GestionAnual
  Auditoria/                             ← Auditoría automática de escrituras
ml/
  modelo_riesgo.py / modelo_triaje.py / servicio_ml.py / modelos_guardados/
```

## URL Routing (kardex/urls.py)

| Prefijo | App |
|---|---|
| `api/tenants/` | `Tenants.urls` |
| `api/auth/` | `GestionDeUsuarios.LoginYAutenticacion.urls` |
| `api/pacientes/` | `GestionDeUsuarios.RegistroYBusquedaDePacientes.urls` |
| `api/expediente/` | `GestionDeUsuarios.VisualizacionDelExpediente.urls` |
| `api/antecedentes/` | `GestionDeUsuarios.EdicionDeAntecedentesMedicos.urls` |
| `api/personal/` | `GestionDeUsuarios.GestionDePersonalDeSalud.urls` |
| `api/especialidades/` | especialidades_urlpatterns (mismo app personal) |
| `api/consultas/` | `AtencionClinica.ConsultaMedicaSOAP.urls` |
| `api/clinica/` | `AtencionClinica.EmisionDeRecetaMedica.urls` |
| `api/` | `AtencionClinica.AperturaFichaYColaDeAtencion.urls` |
| `api/triaje/` | `AtencionClinica.RegistroDeTriaje.urls` |
| `api/` | `AtencionClinica.SolicitudDeEstudios.urls` |
| `api/reportes/` | `SeguridadAvanzadaYAdministracion.ReporteProduccion.urls` |
| `api/auditoria/` | `SeguridadAvanzadaYAdministracion.PanelDeAuditoriaYReportesSNIS.urls` |
| `api/admin/backup/` | `SeguridadAvanzadaYAdministracion.BackupRestore.urls` |

## Autenticación y Roles

- JWT: access 15 min, refresh 30 días con rotación + blacklist.
- Login response: `{ access, refresh, user: { id, username, email, first_name, last_name, groups, is_staff, is_superuser } }`.
- **7 roles**: `Médico`, `Enfermera`, `Administrativo`, `Laboratorio`, `Farmacia`, `Auditor`, `Director`.
- Permiso por defecto: `IsAuthenticated`. Endpoints públicos usan `AllowAny` explícito.
- Superadmin (`is_staff=True`): acceso total, Django admin en `/admin/`.

## Multitenant

- `TenantMiddleware` → `request.tenant` (desde JWT claim `tenant_id`).
- `TenantManager` → filtra querysets automáticamente por tenant.
- `ConfiguracionTenant` (OneToOne con Tenant): idioma, moneda, zona_horaria, `modulos_habilitados` (JSONField, lista vacía = todos activos), `campos_extra_paciente`.
- `Tenant.get_configuracion()` → get_or_create, nunca lanza excepción.
- `GestionAnual`: congela datos de un año. Descongelar solo superadmin.

## Endpoints de Tenants (Tenants/urls.py)

```
GET/POST   api/tenants/                          → lista/crea tenants (superadmin)
GET/PATCH  api/tenants/<pk>/                     → detalle/edita tenant (superadmin)
POST       api/tenants/<pk>/toggle-activo/       → activa/desactiva (superadmin)
GET/PATCH  api/tenants/<pk>/configuracion/       → config de cualquier tenant (superadmin)
GET        api/tenants/mi-tenant/                → tenant del usuario autenticado
GET/PATCH  api/tenants/mi-tenant/configuracion/  → config del propio tenant (Director/Admin)
```

## Backup/Restore (BackupRestore/urls.py)

```
POST  api/admin/backup/exportar-tenant/          → JSON del tenant (Director/Admin)
POST  api/admin/backup/completo/                 → dumpdata completo (superadmin)
POST  api/admin/backup/restore/                  → loaddata desde archivo (superadmin)
GET/POST api/admin/backup/gestiones/             → CRUD gestiones anuales
POST  api/admin/backup/gestiones/<pk>/congelar/
POST  api/admin/backup/gestiones/<pk>/descongelar/ → solo superadmin
```

## Auditoría (SeguridadAvanzadaYAdministracion/Auditoria/)

App agregada en merge de Araceli/JhonFernando. Registra automáticamente escrituras vía `AuditMiddleware` (en MIDDLEWARE de settings). Para auditoría manual en vistas:

```python
from SeguridadAvanzadaYAdministracion.Auditoria.audit_utils import registrar_evento
registrar_evento('DISPENSAR', receta, request=request)
```

## ML Service

```python
from ml.servicio_ml import ServicioML
svc = ServicioML.obtener_instancia()
svc.clasificar_triaje(texto_sintomas="dolor en el pecho", triaje_id=15)
svc.predecir_riesgo(paciente_id=42, tipo_riesgo="diabetes_tipo2")
```

**Nunca importar `modelo_riesgo.py` o `modelo_triaje.py` directamente desde vistas.**

Triaje — reglas duras (post-NLP): SpO₂ < 90% | PAS < 80 o > 200 | Glasgow ≤ 8 → ROJO forzado. SpO₂ < 94% | EVA ≥ 9 → mínimo NARANJA.

## Modelos de datos centrales

```
Tenant → ConfiguracionTenant (1:1)
Paciente (tenant) → Ficha → Triaje → Consulta → RecetaMedica / OrdenEstudio
Paciente → Antecedente
GestionAnual (tenant, año, congelada)
```

- `Paciente`: clave de negocio = `ci` + `ci_complemento` (unique_together).
- `Triaje`: IMC y presion_arterial son `@property`, no se almacenan.
- `Consulta`: estado BORRADOR → COMPLETADA → FIRMADA. `codigo_cie10_principal` requerido (SNIS Bolivia).

## Agregar nueva app

1. Crear directorio bajo el dominio con `__init__.py`, `apps.py`, `models.py`, `views.py`, `serializers.py`, `urls.py`.
2. `apps.py`: `name = 'Dominio.NuevaApp'`.
3. Agregar `"Dominio.NuevaApp"` en `INSTALLED_APPS` (kardex/settings.py).
4. Agregar `path("api/ruta/", include("Dominio.NuevaApp.urls"))` en `kardex/urls.py`.
5. `python manage.py makemigrations NuevaApp && python manage.py migrate`.

## Resolución de merges frecuentes

Al fusionar ramas de compañeros, los conflictos más comunes son en `kardex/settings.py` (`INSTALLED_APPS` y `MIDDLEWARE`). Siempre conservar TODAS las apps de ambas ramas. Nunca eliminar una app para resolver el conflicto.

Tras el merge siempre correr:
```bash
python manage.py makemigrations
python manage.py makemigrations --merge   # si hay conflicto de migraciones
python manage.py migrate
```

## Notas de entorno

- `DEBUG=True`, `CORS_ALLOW_ALL_ORIGINS=True`, credenciales hardcodeadas → solo desarrollo.
- `ALLOWED_HOSTS` incluye `192.168.0.108` para acceso desde dispositivos en la LAN.
- `AuditMiddleware` reemplazó al antiguo `kardex.middleware.AuditoriaMiddleware`.
- No hay Celery/Redis, Web3/Blockchain ni MinIO activos — están en `requirements.txt` pero sin implementar.
