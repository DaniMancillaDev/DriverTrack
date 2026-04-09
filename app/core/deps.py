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

# tokenUrl apunta a /auth/token — endpoint OAuth2 form-encoding dedicado
# (separado de /auth/login que recibe JSON desde Flutter).
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
) -> User:
    """Valida el Bearer token JWT y devuelve el usuario autenticado.

    Requiere token con:
    - type='access' (obligatorio, sin excepciones)
    - sub=str(user_id) (entero como string)

    Raises:
        HTTPException 401: token ausente, inválido, expirado o user inexistente.
        HTTPException 403: cuenta desactivada.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token is None:
        raise credentials_exception

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    # sub es siempre str(user_id) — entero como string
    sub: str | None = payload.get("sub")
    if sub is None:
        raise credentials_exception

    try:
        user_id = int(sub)
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
