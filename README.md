# DriveTrack API 🚗🏍️

> **Frontend**: Este backend se conecta con [DriverTrack Frontend 🚗📱](https://github.com/DaniMancillaDev/DriverTrack_Frontend), una aplicación Flutter con Material 3 para gestión vehicular inteligente.

DriveTrack es una API RESTful construida con **FastAPI** para la gestión integral de vehículos y sus registros de mantenimiento. Permite a los usuarios registrar sus vehículos (autos o motocicletas), mantener un historial detallado de mantenimientos (costos, fechas, kilometraje), gestionar fotos de perfil, recibir notificaciones en tiempo real vía WebSockets y consultar datos climáticos.

## 🏗️ Arquitectura
El proyecto sigue principios **SOLID** y una arquitectura de capas bien estructurada:
- **Models**: Esquemas de base de datos ORM con SQLAlchemy 2.0 (async).
- **Schemas**: Validación de datos de entrada/salida con Pydantic v2.
- **Repositories**: Patrón repositorio para la interacción exclusiva y aislada con la capa de datos.
- **Services**: Toda la lógica de negocio y validación.
- **Routers**: Controladores ligeros que gestionan únicamente las peticiones HTTP.

## 🚀 Tecnologías
- [Python 3.14+](https://www.python.org/)
- [FastAPI](https://fastapi.tiangolo.com/) — Framework web de alto rendimiento.
- [SQLAlchemy 2.0](https://www.sqlalchemy.org/) — ORM async para interacción con la base de datos.
- [Alembic](https://alembic.sqlalchemy.org/) — Migraciones de base de datos versionadas.
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) — Gestión validada de variables de entorno.
- [uv](https://github.com/astral-sh/uv) — Gestor de paquetes y entornos virtuales ultra rápido escrito en Rust.
- **SQLite** (desarrollo) / **PostgreSQL** (producción) — Bases de datos soportadas vía `asyncpg` y `aiosqlite`.
- [MinIO / S3](https://min.io/) — Almacenamiento de objetos para fotos de perfil y archivos (`boto3`).
- [python-jose + PyJWT](https://github.com/mpdavis/python-jose) — Autenticación JWT con access y refresh tokens.
- [SlowAPI](https://github.com/laurentS/slowapi) — Rate limiting para protección contra abuso.
- [Uvicorn](https://www.uvicorn.org/) — Servidor ASGI de alto rendimiento.
- **WebSockets** — Notificaciones en tiempo real.
- **OpenWeatherMap** — Proxy de datos climáticos para el frontend.

---

## ⚙️ Modos de Ejecución

La aplicación tiene dos modos de operación: **desarrollo** y **producción**.

---

### 🛠️ Modo Desarrollo

Para correr la API localmente y desarrollar sobre ella:

#### 1. Requisitos Previos
- Instalar `uv`: [Instrucciones oficiales](https://github.com/astral-sh/uv?tab=readme-ov-file#installation)
- (Opcional) Python instalado en tu sistema.

#### 2. Clonar y Preparar el entorno
```bash
# Clona este repositorio
git clone https://github.com/DaniMancillaDev/DriverTrack.git
cd DriverTrack

# Configura las variables de entorno para desarrollo
cp .env.example .env

# uv instalará las dependencias y enlazará o descargará la versión de Python automáticamente
uv sync
```

#### 3. Ejecutar el Servidor
```bash
uv run fastapi dev app/main.py
```

El servidor estará corriendo en `http://127.0.0.1:8000` con hot-reload activado.

> **Nota**: En modo desarrollo se usa **SQLite** como base de datos y **MinIO** local para almacenamiento.

---

### 🚀 Modo Producción (Docker)

El despliegue en producción utiliza **Docker** con redes bridge, **PostgreSQL** y opcionalmente **Nginx Proxy Manager** para SSL.

#### 1. Clonar y configurar
```bash
git clone https://github.com/DaniMancillaDev/DriverTrack.git
cd DriverTrack

# Copiar y editar las variables de entorno
cp .env.example .env
# ⚠️ Edita .env con tus valores reales (SECRET_KEY, DATABASE_URL de PostgreSQL, etc.)
```

> **Nota**: Si no creas `.env` manualmente, el contenedor lo generará desde `.env.example` en el primer arranque. Debes editarlo después.

#### 2. Levantar los servicios
```bash
# Construir y levantar (API + MinIO)
docker compose up -d --build
```

**Servicios incluidos:**
- **API**: FastAPI en puerto `8010` del host (interno `8000`), con migraciones automáticas (Alembic).
- **MinIO**: Almacenamiento S3-compatible — Consola en `http://localhost:9001`, API en `9000`.

#### 3. (Opcional) Integración con Nginx Proxy Manager
Si tienes Nginx Proxy Manager corriendo en tu servidor, el archivo `docker-compose.override.yml` conecta los servicios a su red automáticamente:

```bash
# Simplemente levanta con el override presente en el directorio
docker compose up -d --build
```

> Si **no** usas NPM, elimina o renombra `docker-compose.override.yml`:
> ```bash
> mv docker-compose.override.yml docker-compose.override.yml.disabled
> ```

---

> **¿Quieres probar la app real en producción sin configurar nada?** 🚀 Contacta al [creador del proyecto](https://github.com/DaniMancillaDev) — él te dará acceso a la instancia live con todos los servicios corriendo.

---

## 📚 Documentación Interactiva de la API
Una gran ventaja de FastAPI es su documentación generada en automático.
Una vez corriendo el servidor, visita:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc UI**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## 📌 Endpoints Principales
- `POST /auth/register` — Registro de usuario con hasheo de contraseña (bcrypt).
- `POST /auth/login` — Autenticación con JWT (access + refresh tokens).
- `POST /auth/otp` — Verificación OTP para recuperación de cuenta.
- `GET/POST /vehicles/` — CRUD de vehículos.
- `GET/POST /maintenance/` — CRUD de historiales de mantenimiento con sincronización automática de odómetro.
- `WS /notifications/` — Notificaciones en tiempo real vía WebSocket.
- `GET /weather/` — Proxy de datos climáticos (OpenWeatherMap).
- `POST /users/photo` — Subida y resolución de foto de perfil (MinIO).

---
*Desarrollado con ❤️ usando FastAPI en Python.*
