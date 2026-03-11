"""Utilidades de seguridad para hashing de contraseñas.

Usa passlib con bcrypt para generar y verificar hashes seguros.
En el futuro se añadirá generación de tokens JWT aquí.
"""

from passlib.context import CryptContext

# Contexto de hashing configurado con bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compara una contraseña en texto plano contra su hash bcrypt."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Genera un hash bcrypt a partir de una contraseña en texto plano."""
    return pwd_context.hash(password)
