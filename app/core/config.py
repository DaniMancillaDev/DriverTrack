"""Configuración central de la aplicación.

Carga las variables de entorno desde un archivo .env
usando Pydantic Settings. Todos los valores sensibles
son obligatorios y se validan al arrancar la app.
"""

from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración global cargada desde variables de entorno."""

    # URL de conexión a la Base de Datos (SQLite por defecto para desarrollo)
    database_url: str = "sqlite:///./drivetrack.db"

    # Nombre de la aplicación
    app_name: str = "DriveTrack API"

    # Modo debug — SIEMPRE False por defecto para evitar exposición accidental
    debug: bool = False

    # --- JWT ---
    # SECRET_KEY: Obligatoria, sin fallback inseguro.
    # Genera una con: python -c "import secrets; print(secrets.token_hex(32))"
    secret_key: str
    algorithm: str = "HS256"
    # Duración del access token en minutos (default: 15 min)
    access_token_expire_minutes: int = 15
    # Duración del refresh token en días (default: 7 días)
    refresh_token_expire_days: int = 7

    # --- CORS ---
    # Lista de orígenes permitidos. En producción, especificar exactamente.
    # Ejemplo: ["https://drivertrack.app", "https://api.drivertrack.app"]
    allowed_origins: List[str] = ["http://localhost:8080", "http://localhost:3000"]

    # --- MinIO / S3 ---
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "drivertrack"
    minio_secure: bool = False

    @field_validator("secret_key")
    @classmethod
    def secret_key_must_be_strong(cls, v: str) -> str:
        """Rechaza secret keys inseguras o de ejemplo conocidas."""
        _known_insecure = {
            "SUPER_SECRET_KEY_CHANGE_ME",
            "drivetrack-dev-secret-key-change-in-production-2026",
            "changeme",
            "secret",
        }
        if v in _known_insecure:
            raise ValueError(
                "SECRET_KEY insegura detectada. Genera una nueva con: "
                "python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        if len(v) < 32:
            raise ValueError("SECRET_KEY debe tener al menos 32 caracteres")
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


# Instancia global de configuración
settings = Settings()
