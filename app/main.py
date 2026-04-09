"""Aplicación principal de FastAPI.

Configura la instancia de FastAPI, los middlewares de seguridad
y registra todos los routers de la API.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.database import engine, Base, AsyncSessionLocal
import app.models  # Importante para que SQLAlchemy detecte todos los modelos
from app.core.seeds import run_seeds
from app.routers import auth, maintenance, vehicles, users, notifications, notifications_ws


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
    # Crea las tablas asíncronamente al iniciar
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Inserta datos de catálogo si no existen
    async with AsyncSessionLocal() as session:
        await run_seeds(session)

    yield
    # Limpieza al cerrar
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

# 1. Security Headers (antes que CORS para que aplique a todas las respuestas)
app.add_middleware(SecurityHeadersMiddleware)

# 2. CORS — Orígenes explícitos desde configuración, nunca wildcard en prod
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    expose_headers=["X-Total-Count"],
)


# ─── Routers ──────────────────────────────────────────────────

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(vehicles.router)
app.include_router(maintenance.router)
app.include_router(notifications.router)
app.include_router(notifications_ws.router)


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
