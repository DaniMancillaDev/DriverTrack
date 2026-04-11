"""Repositorio especializado para la gestión de la entidad User.

Extiende la funcionalidad base para incluir búsquedas por email y la
creación de usuarios con contraseñas ya procesadas (hasheadas).
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.user import UserCreate


class UserRepository(BaseRepository[User, UserCreate, UserCreate]):
    """Capa de acceso a datos para usuarios.

    Provee métodos específicos para la autenticación y el registro seguro.
    """

    async def get_by_email(self, db: AsyncSession, *, email: str) -> User | None:
        """Busca un usuario por su dirección de email."""
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalars().first()

    async def create_with_hashed_password(
        self, db: AsyncSession, *, obj_in: UserCreate, hashed_password: str
    ) -> User:
        """Crea un usuario inyectando la contraseña ya hasheada asíncronamente."""
        db_obj = User(
            email=obj_in.email,
            hashed_password=hashed_password,
            full_name=obj_in.full_name,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


# Instancia única a ser inyectada/usada por los servicios
user_repo = UserRepository(User)
