"""Router para la gestión de usuarios.

Expone endpoints CRUD para perfiles de usuario.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import UserResponse, UserUpdate
from app.services import users as users_service

router = APIRouter(prefix="/users", tags=["Usuarios"])


@router.get("/", response_model=List[UserResponse], summary="Listar usuarios")
async def read_users(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    """Obtiene una lista paginada de usuarios asíncronamente."""
    users = await users_service.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserResponse, summary="Detalle de usuario")
async def read_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Obtiene el perfil de un usuario asíncronamente."""
    db_user = await users_service.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
        )
    return db_user


@router.put("/{user_id}", response_model=UserResponse, summary="Actualizar usuario")
async def update_user(user_id: int, user_data: UserUpdate, db: AsyncSession = Depends(get_db)):
    """Actualiza la información del usuario asíncronamente."""
    db_user = await users_service.update_user(db, user_id=user_id, user_data=user_data)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
        )
    return db_user


@router.delete(
    "/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar usuario"
)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Elimina una cuenta de usuario asíncronamente."""
    success = await users_service.delete_user(db, user_id=user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
        )
