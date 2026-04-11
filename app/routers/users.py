"""Router para la gestión de usuarios.

Proporciona endpoints para que los usuarios autenticados consulten y
actualicen su información de perfil, cambien su contraseña y gestionen
su foto de perfil mediante integración con MinIO.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    ChangePasswordRequest,
    PhotoConfirmRequest,
    PresignedUrlResponse,
    ProfileUpdateRequest,
    UserResponse,
    UserUpdate,
)
from app.services import users as users_service
from app.services import storage as storage_service

router = APIRouter(prefix="/users", tags=["Usuarios"])


# ─── Perfil del usuario autenticado (/me) ────────────────────


@router.get("/me", response_model=UserResponse, summary="Mi perfil")
async def read_current_user(current_user: CurrentUser):
    """Obtiene el perfil del usuario autenticado."""
    return current_user


@router.put("/me", response_model=UserResponse, summary="Actualizar mi perfil")
async def update_current_user(
    data: ProfileUpdateRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Actualiza el nombre del usuario autenticado.

    Solo permite cambiar full_name. Para cambiar email o contraseña
    usar los endpoints específicos.
    """
    updated = await users_service.update_profile(
        db, user_id=current_user.id, full_name=data.full_name
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )
    return updated


from app.schemas.user import UserPreferencesUpdate

@router.patch("/me/preferences", response_model=UserResponse, summary="Actualizar preferencias de notificaciones")
async def update_preferences(
    data: UserPreferencesUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Actualiza las preferencias de notificación del usuario.

    Permite habilitar o deshabilitar de forma granular:
    - Notificaciones Push globales.
    - Recordatorios de servicios de mantenimiento.
    - Alertas críticas del vehículo.
    """
    updated = await users_service.update_preferences(
        db,
        user_id=current_user.id,
        push_notifications=data.push_notifications,
        service_reminders=data.service_reminders,
        critical_alerts=data.critical_alerts,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )
    return updated


@router.post(
    "/me/change-password",
    status_code=status.HTTP_200_OK,
    summary="Cambiar contraseña",
)
async def change_password(
    data: ChangePasswordRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Cambia la contraseña del usuario autenticado.

    Requiere la contraseña actual para confirmar la identidad.
    """
    success, message = await users_service.change_password(
        db,
        user_id=current_user.id,
        current_password=data.current_password,
        new_password=data.new_password,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
        )
    return {"message": "Contraseña actualizada exitosamente"}


@router.post(
    "/me/photo/presigned-url",
    response_model=PresignedUrlResponse,
    summary="Obtener URL pre-firmada para subir foto de perfil",
)
async def get_photo_upload_url(current_user: CurrentUser):
    """Genera una URL pre-firmada para subir la foto de perfil.

    Este endpoint es el primer paso para cambiar la foto:
    1. El cliente solicita la URL pre-firmada.
    2. El cliente sube la imagen (PUT) directamente al almacenamiento S3/MinIO.
    3. El cliente confirma la subida llamando a `/me/photo/confirm`.
    """
    result = storage_service.generate_presigned_upload_url(
        user_id=current_user.id,
        filename="avatar.jpg",
    )
    return PresignedUrlResponse(**result)


@router.put(
    "/me/photo/confirm",
    response_model=UserResponse,
    summary="Confirmar subida de foto de perfil",
)
async def confirm_photo_upload(
    data: PhotoConfirmRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Confirma que la foto ha sido subida correctamente al almacenamiento.

    Actualiza el campo `photo_url` en la base de datos con una URL de acceso
    temporal (firmada) para el recurso recién subido.
    """
    # Validar que el object_key pertenece a este usuario
    if not data.object_key.startswith(f"avatars/{current_user.id}/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="object_key inválido para este usuario",
        )

    # Generar URL de acceso (7 días)
    photo_url = storage_service.generate_presigned_get_url(data.object_key)

    updated = await users_service.update_photo_url(
        db, user_id=current_user.id, photo_url=photo_url
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )
    return updated


# ─── Endpoints con verificación de identidad ─────────────────


@router.get("/{user_id}", response_model=UserResponse, summary="Detalle de usuario")
async def read_user(
    user_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Obtiene el perfil de un usuario.

    Un usuario solo puede ver su propio perfil.
    """
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado para ver este perfil",
        )
    db_user = await users_service.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
        )
    return db_user


@router.put("/{user_id}", response_model=UserResponse, summary="Actualizar usuario")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Actualiza la información de un usuario.

    Un usuario solo puede modificar su propio perfil.
    """
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado para modificar este perfil",
        )
    db_user = await users_service.update_user(db, user_id=user_id, user_data=user_data)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
        )
    return db_user


@router.delete(
    "/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar usuario"
)
async def delete_user(
    user_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Elimina una cuenta de usuario.

    Un usuario solo puede eliminar su propia cuenta.
    """
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado para eliminar este perfil",
        )
    success = await users_service.delete_user(db, user_id=user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
        )
