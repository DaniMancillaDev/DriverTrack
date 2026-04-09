"""Utilidades de seguridad: hashing de contraseñas y tokens JWT.

Módulo ÚNICO de seguridad. Usa:
  - bcrypt directamente para hashing de contraseñas.
  - PyJWT para generación y verificación de tokens JWT.

⚠️ No importar python-jose en ningún otro módulo.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from jwt.exceptions import PyJWTError

from app.core.config import settings

# ─── Constantes JWT ───────────────────────────────────────────

ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = settings.refresh_token_expire_days


# ─── JWT ──────────────────────────────────────────────────────


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Genera un JWT de acceso firmado con los datos proporcionados.

    El payload debe incluir 'sub' = str(user_id).
    La expiración por defecto es ACCESS_TOKEN_EXPIRE_MINUTES desde settings.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Genera un JWT de refresco con expiración larga.

    Permite al cliente obtener un nuevo access token sin re-autenticarse.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """Decodifica y valida un JWT de acceso.

    Acepta tokens que:
    - Tienen type='access' (tokens nuevos generados por este sistema)
    - No tienen claim 'type' (tokens legacy, compatibilidad hacia atrás)

    Rechaza tokens que explícitamente tienen type='refresh'.

    Returns:
        El payload si el token es válido, None si no.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        # Solo rechazar si el type está presente y es explícitamente 'refresh'
        # Los tokens legacy (sin type) son aceptados durante la migración
        if payload.get("type") == "refresh":
            return None
        return payload
    except PyJWTError:
        return None


def decode_refresh_token(token: str) -> dict | None:
    """Decodifica y valida un JWT de refresco.

    Returns:
        El payload si es válido y es de tipo 'refresh', None si no.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        return payload
    except PyJWTError:
        return None


# ─── Passwords ────────────────────────────────────────────────


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compara una contraseña en texto plano contra su hash bcrypt."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except (ValueError, Exception):
        return False


def get_password_hash(password: str) -> str:
    """Genera un hash bcrypt a partir de una contraseña en texto plano."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")
