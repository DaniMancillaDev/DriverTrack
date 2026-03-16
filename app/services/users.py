"""Servicios para la gestión de usuarios.

Contiene la lógica de negocio y las operaciones de base de datos
(CRUD) para los perfiles de usuario.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserUpdate
from app.core.security import get_password_hash


async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    """Obtiene un usuario por su ID asíncronamente."""
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalars().first()


async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
    """Obtiene una lista de usuarios asíncronamente."""
    result = await db.execute(select(User).offset(skip).limit(limit))
    return list(result.scalars().all())


async def update_user(db: AsyncSession, user_id: int, user_data: UserUpdate) -> Optional[User]:
    """Actualiza la información de un usuario asíncronamente."""
    db_user = await get_user(db, user_id)
    if not db_user:
        return None

    update_data = user_data.model_dump(exclude_unset=True)
    
    if "password" in update_data and update_data["password"]:
        hashed_password = get_password_hash(update_data["password"])
        update_data["hashed_password"] = hashed_password
        del update_data["password"]

    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def delete_user(db: AsyncSession, user_id: int) -> bool:
    """Elimina un usuario asíncronamente."""
    db_user = await get_user(db, user_id)
    if not db_user:
        return False
        
    await db.delete(db_user)
    await db.commit()
    return True
