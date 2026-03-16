"""Utilidades de seguridad para hashing de contraseñas.

Usa bcrypt directamente para generar y verificar hashes seguros,
evitando incompatibilidades de passlib con versiones modernas de bcrypt.
En el futuro se añadirá generación de tokens JWT aquí.
"""

import bcrypt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compara una contraseña en texto plano contra su hash bcrypt."""
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except ValueError:
        return False


def get_password_hash(password: str) -> str:
    """Genera un hash bcrypt a partir de una contraseña en texto plano."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')
