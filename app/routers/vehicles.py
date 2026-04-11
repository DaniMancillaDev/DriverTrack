"""Router de vehículos.

Este módulo permite a los usuarios gestionar su inventario de vehículos,
incluyendo la creación, consulta, actualización y eliminación de registros,
así como la gestión de fotografías de los mismos.
"""

import re

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser
from app.database import get_db
from app.schemas.vehicle import (
    VehicleCreate,
    VehicleResponse,
    VehicleTypeResponse,
    VehicleUpdate,
)
from app.schemas.user import PresignedUrlResponse
from app.services import vehicles as vehicles_service
from app.services import storage as storage_service

router = APIRouter(prefix="/vehicles", tags=["Vehículos"])


# ─── Schemas locales ──────────────────────────────────────────


class VehiclePhotoConfirmRequest(BaseModel):
    """Body para confirmar la subida de foto de un vehículo."""

    object_key: str = Field(..., min_length=5, max_length=512)

    @field_validator("object_key")
    @classmethod
    def validate_key_format(cls, v: str) -> str:
        """Valida que el object_key siga el patrón esperado: vehicles/{id}/{uuid}.jpg"""
        pattern = r"^vehicles/\d+/[a-f0-9]{32}\.jpg$"
        if not re.match(pattern, v):
            raise ValueError("Formato de object_key inválido")
        return v


from app.services.vehicle_access import assert_vehicle_owner

# ─── Endpoints ────────────────────────────────────────────────


# ─── Endpoints públicos (catálogo) ────────────────────────────


@router.get(
    "/types",
    response_model=list[VehicleTypeResponse],
    summary="Listar tipos de vehículos disponibles",
)
async def get_vehicle_types(db: AsyncSession = Depends(get_db)):
    """Obtiene el catálogo maestro de tipos de vehículos.

    Este catálogo es necesario para que el usuario pueda seleccionar una categoría
    válida (Coche, Moto, Camioneta, etc.) al registrar un nuevo vehículo.
    Es un endpoint público para facilitar el flujo de registro.
    """
    return await vehicles_service.get_vehicle_types(db=db)


# ─── Endpoints protegidos ─────────────────────────────────────


@router.post(
    "/",
    response_model=VehicleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un vehículo",
)
async def create_vehicle(
    vehicle_data: VehicleCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Crea un nuevo vehículo asociado al usuario autenticado.

    El user_id siempre se toma del token JWT, nunca del body.
    """
    # Forzar que el vehículo pertenezca al usuario autenticado
    vehicle_data.user_id = current_user.id
    return await vehicles_service.create_vehicle(db=db, vehicle_data=vehicle_data)


@router.get(
    "/",
    response_model=list[VehicleResponse],
    summary="Listar mis vehículos",
)
async def get_vehicles(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Obtiene solo los vehículos del usuario autenticado."""
    return await vehicles_service.get_vehicles(db=db, user_id=current_user.id)


@router.get(
    "/{vehicle_id}",
    response_model=VehicleResponse,
    summary="Obtener detalle de un vehículo",
)
async def get_vehicle(
    vehicle_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Obtiene los datos de un vehículo.

    Solo el propietario puede ver su vehículo.
    """
    vehicle = await assert_vehicle_owner(vehicle_id, current_user.id, db)
    return vehicle


@router.put(
    "/{vehicle_id}",
    response_model=VehicleResponse,
    summary="Actualizar un vehículo",
)
async def update_vehicle(
    vehicle_id: int,
    vehicle_data: VehicleUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Actualiza un vehículo del usuario autenticado."""
    await assert_vehicle_owner(vehicle_id, current_user.id, db)
    return await vehicles_service.update_vehicle(
        db=db, vehicle_id=vehicle_id, vehicle_data=vehicle_data
    )


@router.delete(
    "/{vehicle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un vehículo",
)
async def delete_vehicle(
    vehicle_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Elimina un vehículo del usuario autenticado."""
    await assert_vehicle_owner(vehicle_id, current_user.id, db)
    await vehicles_service.delete_vehicle(db=db, vehicle_id=vehicle_id)


@router.post(
    "/{vehicle_id}/photo/presigned-url",
    response_model=PresignedUrlResponse,
    summary="Obtener URL pre-firmada para foto del vehículo",
)
async def get_vehicle_photo_presigned_url(
    vehicle_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Genera una URL pre-firmada para subir la foto de un vehículo.

    Solo el propietario del vehículo puede iniciar este proceso. La URL permite
    la subida directa al almacenamiento de objetos (MinIO/S3) protegiendo
    las claves de acceso del servidor.
    """
    await assert_vehicle_owner(vehicle_id, current_user.id, db)
    return storage_service.generate_presigned_upload_url_for_vehicle(vehicle_id)


@router.put(
    "/{vehicle_id}/photo/confirm",
    response_model=VehicleResponse,
    summary="Confirmar subida de foto del vehículo",
)
async def confirm_vehicle_photo_upload(
    vehicle_id: int,
    body: VehiclePhotoConfirmRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Confirma la subida exitosa de la foto y actualiza el vehículo.

    Valida que el `object_key` proporcionado por el cliente tenga el formato
    correcto y pertenezca realmente al vehículo en cuestión. Tras la validación,
    actualiza la URL de imagen del vehículo en la base de datos.
    """
    await assert_vehicle_owner(vehicle_id, current_user.id, db)

    # Verificar que la key es para este vehículo
    if not body.object_key.startswith(f"vehicles/{vehicle_id}/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El object_key no corresponde a este vehículo",
        )

    photo_url = storage_service.generate_presigned_get_url(body.object_key)
    update_data = VehicleUpdate(image_url=photo_url)
    return await vehicles_service.update_vehicle(
        db=db, vehicle_id=vehicle_id, vehicle_data=update_data
    )
