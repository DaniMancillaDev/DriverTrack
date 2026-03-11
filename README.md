# DriveTrack API 🚗🏍️

DriveTrack es una API RESTfull construida con **FastAPI** para la gestión de vehículos y sus registros de mantenimiento. Permite a los usuarios registrar sus vehículos (autos o motocicletas) y mantener un historial detallado de los mantenimientos realizados (costos, fechas, kilometraje).

## 🏗️ Arquitectura
El proyecto sigue principios **SOLID** y una arquitectura de capas bien estructurada:
- **Models**: Esquemas de base de datos ORM con SQLAlchemy.
- **Schemas**: Validación de datos de entrada/salida con Pydantic v2.
- **Repositories**: Patrón repositorio para la interacción exclusiva y aislada con la capa de datos.
- **Services**: Toda la lógica de negocio y validación.
- **Routers**: Controladores ligeros que gestionan únicamente las peticiones HTTP HTTP.

## 🚀 Tecnologías
- [Python 3.14+](https://www.python.org/)
- [FastAPI](https://fastapi.tiangolo.com/) - Framework web de alto rendimiento.
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM para la interacción con la base de datos.
- [uv](https://github.com/astral-sh/uv) - Gestor de paquetes y entornos virtuales ultra rápido escrito en Rust.
- **SQLite** - Base de datos por defecto para desarrollo (fácilmente escalable a PostgreSQL).

---

## ⚙️ Instalación y Configuración Local

### 1. Requisitos Previos
- Instalar `uv`: [Instrucciones oficiales](https://github.com/astral-sh/uv?tab=readme-ov-file#installation)
- (Opcional) Python instalado en tu sistema.

### 2. Clonar y Preparar el entorno
```bash
# Clona este repositorio
git clone https://github.com/DaniMancillaDev/DriverTrack.git
cd DriverTrack

# Configura las variables de entorno para desarrollo
cp .env.example .env

# uv instalará las dependencias y enlazará o descargará la versión de Python automáticamente
uv sync
```

### 3. Ejecutar el Servidor de Desarrollo
Puedes alzar el servidor para modo de desarrollo en tiempo real con este comando:
```bash
uv run fastapi dev app/main.py
```

El servidor estará corriendo en `http://127.0.0.1:8000`.

---

## 📚 Documentación Interactiva de la API
Una gran ventaja de FastAPI es su documentación generada en automático.
Una vez corriendo el servidor, visita:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc UI**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## 📌 Endpoints Principales (WIP)
- `POST /auth/register`: Registro de usuario con hasheo de contraseña (bcrypt).
- `POST /auth/login`: Autenticación del usuario (Próximamente JWT).
- `GET/POST /vehicles/`: CRUD de vehículos.
- `GET/POST /maintenance/`: CRUD de historiales de mecánicos atados a un vehículo.

---
*Desarrollado con ❤️ usando FastAPI en Python.*
