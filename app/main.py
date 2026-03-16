"""Aplicación principal de FastAPI.

Configura la instancia de FastAPI, el middleware CORS
y registra todos los routers de la API.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
import app.models # Importante para que SQLAlchemy detecte todos los modelos
from app.routers import auth, maintenance, vehicles, users

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja el ciclo de vida de la aplicación."""
    # Crea las tablas asíncronamente al iniciar
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Limpieza al cerrar (opcional)
    await engine.dispose()

# Instancia principal de la aplicación con lifespan
app = FastAPI(
    title="DriveTrack API",
    description="API parea gestión de vehículos y mantenimientos (Async Edition)",
    version="0.1.0",
    lifespan=lifespan,
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro de routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(vehicles.router)
app.include_router(maintenance.router)


@app.get("/", tags=["Root"])
async def root():
    """Endpoint raíz."""
    return {
        "app": "DriveTrack API",
        "version": "0.1.0 (Async)",
        "docs": "/docs",
    }
