"""Dependencias de autenticación para FastAPI.

Módulo ÚNICO de dependencias de auth. Usa security.py como
fuente exclusiva de lógica JWT.

Todos los routers deben importar get_current_user desde aquí.
NO importar desde dependencies.py (archivo legacy eliminado).
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.database import get_db
from app.models.user import User
from app.services import users as users_service

# tokenUrl apunta al endpoint de login real
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
) -> User:
    """Valida el Bearer token JWT y devuelve el usuario autenticado.

    - Decodifica el token con la clave secreta.
    - Verifica que el claim 'sub' existe y es un user_id válido.
    - Verifica que el usuario existe en BD y está activo.

    Raises:
        HTTPException 401: token inválido, expirado o usuario inexistente.
        HTTPException 403: cuenta desactivada.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    # sub siempre es str(user_id) — nunca email
    user_id_str: str | None = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise credentials_exception

    user = await users_service.get_user(db, user_id=user_id)
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta desactivada",
        )

    return user


# Alias tipado para uso conciso en routers
CurrentUser = Annotated[User, Depends(get_current_user)]
