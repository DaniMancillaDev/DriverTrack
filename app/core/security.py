"""Utilidades de seguridad: hashing de contraseñas y gestión de tokens JWT.

Este módulo centraliza la lógica criptográfica de la aplicación, utilizando
bcrypt para el almacenamiento seguro de contraseñas y PyJWT para la
emisión y validación de tokens de acceso y refresco.
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
    """Genera un JWT de acceso con una validez de corta duración.

    Incluye un atributo 'type' con valor 'access' para prevenir el uso indebido
    de tokens de refresco en endpoints protegidos.
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

    Solo acepta tokens con type='access'. Rechaza cualquier otro tipo
    (legacy, refresh, sin type).

    Returns:
        El payload si el token es válido y tiene type='access', None si no.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        # Requerir explicitamente type='access' — sin excepciones
        if payload.get("type") != "access":
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
    """Transforma una contraseña en una cadena irreversible mediante bcrypt.

    Utiliza un factor de costo de 12 (rounds) y un 'salt' aleatorio por defecto
    para fortalecer la protección contra ataques de fuerza bruta o tablas arcoíris.
    """
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")
