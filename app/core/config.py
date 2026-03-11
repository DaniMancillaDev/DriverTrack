"""Configuración central de la aplicación.

Carga las variables de entorno desde un archivo .env
usando Pydantic Settings.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración global cargada desde variables de entorno."""

    # URL de conexión a la Base de Datos (SQLite por defecto para desarrollo)
    database_url: str = "sqlite:///./drivetrack.db"

    # Nombre de la aplicación
    app_name: str = "DriveTrack API"

    # Modo debug para SQLAlchemy (muestra queries en consola)
    debug: bool = True

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


# Instancia global de configuración
settings = Settings()
