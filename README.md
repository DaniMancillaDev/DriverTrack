<h1 align="center">DriveTrack API</h1>

<p align="center">
  <strong>Backend RESTful para gestión vehicular inteligente</strong>
</p>

<p align="center">
  <a href="https://github.com/DaniMancillaDev/DriverTrack_Frontend"><strong>Frontend Flutter →</strong></a>
</p>

---

## 📌 Descripción del Proyecto

**DriveTrack API** es un backend RESTful construido con **FastAPI** para la gestión integral de vehículos y sus registros de mantenimiento. Permite a los usuarios registrar vehículos (autos o motocicletas), mantener un historial detallado de mantenimientos (costos, fechas, kilometraje), gestionar fotos de perfil y vehículos, recibir notificaciones en tiempo real vía WebSockets y consultar datos climáticos mediante un proxy seguro.

**Público objetivo**: Conductores y propietarios de vehículos que necesitan una plataforma centralizada para gestionar el mantenimiento, localizar servicios automotrices y recibir alertas preventivas.

---

## 🏗️ Arquitectura General

```
┌─────────────────────┐       REST + JSON        ┌──────────────────────┐
│                     │  ──────────────────────►  │                      │
│   Flutter App       │       JWT (Bearer)        │   FastAPI Backend    │
│   (Frontend)        │  ◄──────────────────────  │   (DriveTrack API)   │
│                     │       JSON Response        │                      │
└─────────────────────┘                           └──────────────────────┘
         │                                                  │
    ┌────┴─────┐                              ┌────────────┼────────────┐
    │ WebSocket │                              │            │            │
    │ (Notifications)│                         │  PostgreSQL │   MinIO    │
    └──────────┘                               │  / SQLite   │   / S3     │
                                               └────────────┴────────────┘
```

El proyecto sigue principios **SOLID** y una arquitectura de capas:

| Capa | Responsabilidad |
|------|----------------|
| **Models** | Esquemas ORM con SQLAlchemy 2.0 (async) |
| **Schemas** | Validación de entrada/salida con Pydantic v2 |
| **Repositories** | Patrón repositorio — interacción aislada con la capa de datos |
| **Services** | Lógica de negocio y validación |
| **Routers** | Controladores ligeros — solo gestionan peticiones HTTP |

---

## 🛠️ Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| **Lenguaje** | Python 3.14+ |
| **Framework** | FastAPI |
| **ORM** | SQLAlchemy 2.0 (async) |
| **Migraciones** | Alembic |
| **Validación** | Pydantic v2 + Pydantic Settings |
| **Autenticación** | JWT (python-jose + PyJWT) — access + refresh tokens |
| **Rate Limiting** | SlowAPI |
| **Almacenamiento** | MinIO / S3 (boto3) — presigned URLs |
| **Base de datos** | SQLite (dev) / PostgreSQL (prod) vía asyncpg + aiosqlite |
| **Tiempo real** | WebSockets (notificaciones) |
| **Clima** | OpenWeatherMap (proxy seguro) |
| **Servidor** | Uvicorn (ASGI) |
| **Gestor de paquetes** | uv (Rust) |
| **Contenedores** | Docker + Docker Compose |

---

## ⚙️ Instalación y Ejecución

### 🛠️ Modo Desarrollo

#### Requisitos
- [uv](https://github.com/astral-sh/uv?tab=readme-ov-file#installation) — Gestor de paquetes ultra rápido
- (Opcional) Python instalado en tu sistema

#### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/DaniMancillaDev/DriverTrack.git
cd DriverTrack

# 2. Configurar variables de entorno
cp .env.example .env
# ⚠️ Edita .env — genera un SECRET_KEY real:
#   python -c "import secrets; print(secrets.token_hex(32))"

# 3. Instalar dependencias (uv descarga Python automáticamente)
uv sync

# 4. Ejecutar el servidor con hot-reload
uv run fastapi dev app/main.py
```

El servidor corre en `http://127.0.0.1:8000`.

> **Nota**: En modo desarrollo se usa **SQLite** y `DEBUG=True` habilita `/docs`, `/redoc` y logs SQL.

---

### 🚀 Modo Producción (Docker)

#### Requisitos
- [Docker](https://docs.docker.com/get-docker/) + Docker Compose

#### Pasos

```bash
# 1. Clonar y configurar
git clone https://github.com/DaniMancillaDev/DriverTrack.git
cd DriverTrack

cp .env.example .env
# ⚠️ Edita .env con valores de producción:
#   - SECRET_KEY (mínimo 32 caracteres)
#   - DATABASE_URL=postgresql+asyncpg://user:pass@host/db
#   - DEBUG=False
#   - ALLOWED_ORIGINS=["https://tu-dominio.com"]
#   - MINIO_ACCESS_KEY / MINIO_SECRET_KEY
```

> Si no creas `.env`, el contenedor lo genera desde `.env.example` en el primer arranque. Debes editarlo después.

```bash
# 2. Levantar servicios (API + MinIO)
docker compose up -d --build
```

**Servicios:**

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| **API** | `8010` (host) → `8010` (container) | FastAPI con migraciones automáticas (Alembic) |
| **MinIO** | `9000` (API) / `9001` (Consola) | Almacenamiento S3-compatible |

#### Integración con Nginx Proxy Manager (SSL)

Si usas NPM en tu servidor, `docker-compose.override.yml` conecta los servicios automáticamente:

```bash
docker compose up -d --build
```

> Si **no** usas NPM, desactívalo:
> ```bash
> mv docker-compose.override.yml docker-compose.override.yml.disabled
> ```

---

## 🔐 Configuración Importante

### Variables de Entorno (`.env`)

| Variable | Requerida | Default | Descripción |
|----------|-----------|---------|-------------|
| `DATABASE_URL` | No | `sqlite+aiosqlite:///./drivetrack.db` | URL de conexión a la BD |
| `SECRET_KEY` | **Sí** | — | Clave JWT (mínimo 32 caracteres) |
| `ALGORITHM` | No | `HS256` | Algoritmo de firma JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `15` | Duración del access token |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Duración del refresh token |
| `DEBUG` | No | `False` | Modo debug (activa /docs, logs SQL) |
| `ALLOWED_ORIGINS` | No | `["http://localhost:8080"]` | Orígenes CORS (JSON array) |
| `OPENWEATHER_API_KEY` | No | `""` | API key de OpenWeatherMap |
| `MINIO_ENDPOINT` | No | `localhost:9000` | Endpoint de MinIO/S3 |
| `MINIO_ACCESS_KEY` | No | `minioadmin` | Access key de MinIO |
| `MINIO_SECRET_KEY` | No | `minioadmin` | Secret key de MinIO |
| `MINIO_BUCKET` | No | `drivertrack` | Bucket de almacenamiento |
| `MINIO_SECURE` | No | `False` | Usar HTTPS para MinIO |

> ⚠️ **NUNCA** subas `.env` a Git. El archivo `.env.example` es la plantilla segura.

### Seguridad

- `SECRET_KEY` es validada al arranque: rechaza keys inseguras conocidas y menores a 32 caracteres
- En producción (`DEBUG=False`): se desactivan `/docs`, `/redoc`, `/openapi.json` y se añade HSTS
- Rate limiting en endpoints sensibles (login: 10/min, registro: 5/min, forgot-password: 3/min)

---

## 🔌 Documentación de la API

### Documentación Interactiva

Cuando `DEBUG=True`, FastAPI genera documentación automática:

- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

### Endpoints

#### Autenticación (`/auth`)

| Método | Endpoint | Descripción | Auth | Rate Limit |
|--------|----------|-------------|------|------------|
| `POST` | `/auth/register` | Registrar nuevo usuario | No | 5/min |
| `POST` | `/auth/login` | Iniciar sesión | No | 10/min |
| `POST` | `/auth/refresh` | Renovar access token | No | — |
| `GET` | `/auth/me` | Verificar token actual | Sí | — |
| `POST` | `/auth/forgot-password` | Solicitar código OTP | No | 3/min |
| `POST` | `/auth/verify-otp` | Verificar OTP | No | 10/min |
| `POST` | `/auth/reset-password` | Restablecer contraseña | No | 5/min |

**Ejemplo: Login**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "mypassword"}'
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_active": true
  }
}
```

#### Vehículos (`/vehicles`)

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| `GET` | `/vehicles/types` | Catálogo de tipos de vehículo | No |
| `POST` | `/vehicles/` | Registrar vehículo | Sí |
| `GET` | `/vehicles/` | Listar mis vehículos | Sí |
| `GET` | `/vehicles/{id}` | Detalle de vehículo | Sí |
| `PUT` | `/vehicles/{id}` | Actualizar vehículo | Sí |
| `DELETE` | `/vehicles/{id}` | Eliminar vehículo | Sí |
| `POST` | `/vehicles/{id}/photo/presigned-url` | URL para subir foto | Sí |
| `PUT` | `/vehicles/{id}/photo/confirm` | Confirmar subida de foto | Sí |

#### Mantenimiento (`/vehicles/{id}/maintenance`, `/maintenance`)

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| `POST` | `/vehicles/{id}/maintenance` | Registrar mantenimiento | Sí |
| `GET` | `/vehicles/{id}/maintenance` | Historial por vehículo (paginado) | Sí |
| `GET` | `/maintenance` | Todos mis mantenimientos (paginado) | Sí |
| `GET` | `/maintenance/{id}` | Detalle de mantenimiento | Sí |
| `PUT` | `/maintenance/{id}` | Actualizar mantenimiento | Sí |
| `DELETE` | `/maintenance/{id}` | Eliminar mantenimiento | Sí |

#### Usuarios (`/users`)

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| `GET` | `/users/me` | Mi perfil | Sí |
| `PUT` | `/users/me` | Actualizar perfil | Sí |
| `PATCH` | `/users/me/preferences` | Preferencias de notificaciones | Sí |
| `POST` | `/users/me/change-password` | Cambiar contraseña | Sí |
| `POST` | `/users/me/photo/presigned-url` | URL para subir foto de perfil | Sí |
| `PUT` | `/users/me/photo/confirm` | Confirmar foto de perfil | Sí |

#### Notificaciones (`/notifications`)

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| `GET` | `/notifications` | Listar notificaciones (paginado) | Sí |
| `PATCH` | `/notifications/{id}/read` | Marcar como leída | Sí |
| `PATCH` | `/notifications/read-all` | Marcar todas como leídas | Sí |
| `GET` | `/notifications/unread-count` | Contador de no leídas | Sí |
| `DELETE` | `/notifications/{id}` | Eliminar notificación | Sí |
| `WS` | `/ws/notifications` | Notificaciones en tiempo real | Sí |

**Protocolo WebSocket:**
1. Cliente envía: `{"type": "auth", "token": "<JWT>"}`
2. Servidor responde: `{"type": "connection_established", "user_id": int}`
3. Notificaciones push: `<NotificationResponse JSON>`
4. Keep-alive: cliente envía `{"type": "ping"}` → servidor responde `{"type": "pong"}`

#### Clima (`/weather`)

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| `GET` | `/weather/current?lat=&lon=` | Clima por coordenadas | Sí |
| `GET` | `/weather/city/{name}` | Clima por nombre de ciudad | Sí |

### Manejo de Errores

| Código | Significado | Detalle |
|--------|------------|---------|
| `401` | Token expirado/inválido | Usar `/auth/refresh` para renovar |
| `403` | Sin permisos | El usuario no es propietario del recurso |
| `404` | Recurso no encontrado | El ID no existe en la BD |
| `422` | Validación fallida | Pydantic detalla los campos inválidos |
| `429` | Rate limit excedido | Reintentar después del período indicado |
| `5xx` | Error del servidor | Verificar logs del contenedor |

---

## 📂 Estructura del Proyecto

```
app/
├── core/
│   ├── config.py          # Pydantic Settings (variables de entorno)
│   ├── security.py        # JWT creation/decode, password hashing
│   ├── deps.py            # Dependencias (CurrentUser, get_db)
│   └── seeds.py           # Datos iniciales (admin, vehicle types)
├── models/                # SQLAlchemy ORM models
│   ├── user.py
│   ├── vehicle.py
│   ├── maintenance.py
│   ├── notification.py
│   ├── notification_cooldown.py
│   ├── password_reset.py
│   └── scheduler_lock.py
├── schemas/               # Pydantic request/response schemas
│   ├── user.py
│   ├── vehicle.py
│   ├── maintenance.py
│   ├── notification.py
│   └── weather.py
├── repositories/          # Data access layer (Repository pattern)
│   ├── base.py
│   ├── user.py
│   ├── vehicle.py
│   ├── maintenance.py
│   └── notification.py
├── services/              # Business logic
│   ├── auth.py
│   ├── users.py
│   ├── vehicles.py
│   ├── vehicle_access.py
│   ├── maintenance.py
│   ├── notification.py
│   ├── notification_rules.py
│   ├── notification_scheduler.py
│   ├── storage.py
│   └── weather.py
├── routers/               # HTTP/WebSocket controllers
│   ├── auth.py
│   ├── users.py
│   ├── vehicles.py
│   ├── maintenance.py
│   ├── notifications.py
│   ├── notifications_ws.py
│   └── weather.py
├── database.py            # Engine, session, Base
├── docs/                  # Additional docs
└── main.py                # FastAPI app, middlewares, lifespan
```

---

## 🧠 Buenas Prácticas Implementadas

- **Arquitectura en capas**: Models → Repositories → Services → Routers, cada capa con responsabilidad única
- **Patrón Repositorio**: Aislamiento completo de la capa de datos; los services nunca tocan SQLAlchemy directamente
- **Pydantic Settings**: Validación estricta de variables de entorno al arranque (falla rápido si falta `SECRET_KEY`)
- **Presigned URLs**: Subida de archivos directa a MinIO/S3 sin exponer credenciales del servidor al cliente
- **Rate Limiting**: Protección contra abuso en endpoints sensibles (auth, OTP)
- **Security Headers**: X-Content-Type-Options, X-Frame-Options, HSTS en producción
- **CORS adaptativo**: Wildcard en desarrollo, orígenes explícitos en producción con credenciales
- **Seeds automáticos**: Admin y tipos de vehículo se crean al arrancar si no existen
- **Scheduler de notificaciones**: Background task que analiza vehículos y genera alertas de mantenimiento
- **Migraciones automáticas**: Alembic `upgrade head` se ejecuta en el entrypoint de Docker

---

## 🧪 Testing

### Probar endpoints con curl

```bash
# Registro
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test1234","full_name":"Test User"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test1234"}'

# Listar vehículos (reemplazar TOKEN)
curl http://localhost:8000/vehicles/ \
  -H "Authorization: Bearer TOKEN"

# Clima actual
curl "http://localhost:8000/weather/current?lat=19.43&lon=-99.13" \
  -H "Authorization: Bearer TOKEN"
```

### Ejecutar tests

```bash
uv run pytest
```

---

## ❗ Problemas Conocidos

- **Overpass API**: El frontend puede experimentar errores 429/504 en búsquedas intensivas de servicios automotrices
- **MinIO en desarrollo**: Si MinIO no está disponible, las funciones de foto no están disponibles (la API no crashea)
- **SQLite en producción**: No soporta concurrencia completa. Para producción, usar PostgreSQL

---

## 💡 Despliegue

| Plataforma | Configuración |
|-----------|--------------|
| **VPS + Docker** | `docker compose up -d` + Nginx Proxy Manager para SSL |
| **Render** | Docker deploy, puerto 8010, variables de entorno en dashboard |
| **Railway** | Conectar repo GitHub, auto-detecta Dockerfile |

---

Desarrollado con ❤️ por [DaniMancillaDev](https://github.com/DaniMancillaDev) & [GatoRX8](https://github.com/GatoRX8)
