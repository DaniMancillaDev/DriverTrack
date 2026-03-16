"""Servicios de autenticación y gestión de usuarios."""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.repositories.user import user_repo
from app.schemas.user import LoginRequest, UserCreate


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """Crea un nuevo usuario asíncronamente."""
    existing_user = await user_repo.get_by_email(db, email=user_data.email)
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado",
        )

    return await user_repo.create_with_hashed_password(
        db, 
        obj_in=user_data, 
        hashed_password=get_password_hash(user_data.password)
    )


async def authenticate_user(db: AsyncSession, credentials: LoginRequest) -> User:
    """Verifica las credenciales asíncronamente."""
    user = await user_repo.get_by_email(db, email=credentials.email)

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )

    return user
