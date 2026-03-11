"""Aplicación principal de FastAPI.

Configura la instancia de FastAPI, el middleware CORS
y registra todos los routers de la API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, maintenance, vehicles

# Instancia principal de la aplicación
app = FastAPI(
    title="DriveTrack API",
    description="API para gestión de vehículos y mantenimientos",
    version="0.1.0",
)

# Middleware CORS para permitir peticiones desde Flutter
# En producción, reemplazar ["*"] con los orígenes específicos permitidos
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro de routers
app.include_router(auth.router)
app.include_router(vehicles.router)
app.include_router(maintenance.router)


@app.get("/", tags=["Root"])
def root():
    """Endpoint raíz para verificar que la API está activa."""
    return {
        "app": "DriveTrack API",
        "version": "0.1.0",
        "docs": "/docs",
    }
