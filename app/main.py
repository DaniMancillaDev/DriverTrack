"""Aplicación principal de FastAPI.

Configura la instancia de FastAPI, los middlewares de seguridad
y registra todos los routers de la API.
"""

import asyncio

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.database import engine, Base, AsyncSessionLocal
import app.models  # Importante para que SQLAlchemy detecte todos los modelos
from app.core.seeds import run_seeds
from app.routers import auth, maintenance, vehicles, users, notifications, notifications_ws, weather
from app.services.storage import ensure_bucket_exists
from app.services.notification_scheduler import notification_scheduler_loop


# ─── Security Headers Middleware ─────────────────────────────

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Añade cabeceras de seguridad HTTP a todas las respuestas."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Solo añadir HSTS en producción (cuando no está en modo debug)
        if not settings.debug:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response


# ─── Lifespan ─────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja el ciclo de vida de la aplicación."""
    # 1. Crear tablas en la BD
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2. Seeds: vehicle types + admin
    async with AsyncSessionLocal() as session:
        await run_seeds(session)

    # 3. Crear bucket de MinIO si no existe
    try:
        ensure_bucket_exists()
        print(f"  ✓ MinIO bucket '{settings.minio_bucket}' OK")
    except Exception as exc:
        # Si MinIO no está disponible, solo advertir (no crashear)
        print(f"  ⚠️  MinIO no disponible: {exc}")
        print("     Las funciones de foto no estarán disponibles.")

    # 4. Iniciar scheduler de notificaciones automáticas en background
    scheduler_task = asyncio.create_task(notification_scheduler_loop())
    print("  ✓ Scheduler de notificaciones automáticas iniciado")

    yield

    # Limpieza al cerrar
    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass
    await engine.dispose()


# ─── App Instance ─────────────────────────────────────────────

app = FastAPI(
    title="DriveTrack API",
    description="API para gestión de vehículos y mantenimientos",
    version="0.2.0",
    lifespan=lifespan,
    # Desactivar documentación automática en producción
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)


# ─── Middlewares ──────────────────────────────────────────────

# IMPORTANTE: El orden de add_middleware en Starlette es LIFO (último en añadirse
# se ejecuta primero). Por eso CORS debe añadirse DESPUÉS de SecurityHeaders
# para que CORS procese la petición antes (y pueda responder los OPTIONS directamente).

# 1. Security Headers — se ejecutará DESPUÉS que CORS en el pipeline
app.add_middleware(SecurityHeadersMiddleware)

# 2. CORS — se ejecutará PRIMERO (responde OPTIONS antes de llegar a los handlers)
#
# En modo DEBUG: wildcard para permitir cualquier origen de desarrollo.
#   ⚠️ allow_credentials debe ser False con allow_origins=["*"].
# En PRODUCCIÓN: orígenes explícitos con credenciales.
if settings.debug:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],           # Cualquier origen en dev
        allow_credentials=False,       # No se puede usar True con wildcard
        allow_methods=["*"],
        allow_headers=["*"],           # Sin restricciones en dev
        expose_headers=["X-Total-Count"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With"],
        expose_headers=["X-Total-Count"],
    )


# ─── Routers ──────────────────────────────────────────────────

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(vehicles.router)
app.include_router(maintenance.router)
app.include_router(notifications.router)
app.include_router(notifications_ws.router)
app.include_router(weather.router)


# ─── Root ─────────────────────────────────────────────────────

@app.get("/", tags=["Root"])
async def root():
    """Endpoint raíz con información básica de la API."""
    return {
        "app": "DriveTrack API",
        "version": "0.2.0",
        # No revelar la URL de docs en producción
        **({"docs": "/docs"} if settings.debug else {}),
    }


@app.get("/health", tags=["Root"])
async def health_check():
    """Health check para monitoreo y load balancers."""
    return {"status": "ok"}
