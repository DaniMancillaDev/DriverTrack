"""Servicios para la gestión de vehículos."""

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vehicle import Vehicle, VehicleType
from app.repositories.user import user_repo
from app.repositories.vehicle import vehicle_repo
from app.schemas.vehicle import VehicleCreate, VehicleUpdate


async def get_vehicle_types(db: AsyncSession) -> list[VehicleType]:
    """Obtiene el catálogo de tipos de vehículos asíncronamente."""
    from sqlalchemy import select
    result = await db.execute(select(VehicleType))
    return list(result.scalars().all())


async def create_vehicle(db: AsyncSession, vehicle_data: VehicleCreate) -> Vehicle:
    """Registra un nuevo vehículo asegurando validaciones asíncronamente."""
    # Verificamos si existe el usuario
    user = await user_repo.get(db, id=vehicle_data.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    # Verificamos si la placa existe
    existing_plate = await vehicle_repo.get_by_plate(db, plate=vehicle_data.plate)
    if existing_plate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La placa ya está registrada",
        )

    # Creamos el registro en DB
    return await vehicle_repo.create(db, obj_in=vehicle_data)


async def get_vehicles(db: AsyncSession, user_id: Optional[int] = None) -> list[Vehicle]:
    """Obtiene la lista de vehículos asíncronamente."""
    if user_id is not None:
        return await vehicle_repo.get_by_user(db, user_id=user_id)
    return await vehicle_repo.get_all(db)


async def get_vehicle_by_id(db: AsyncSession, vehicle_id: int) -> Vehicle:
    """Obtiene un vehículo asíncronamente."""
    vehicle = await vehicle_repo.get(db, id=vehicle_id)
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehículo no encontrado",
        )
    return vehicle


async def update_vehicle(
    db: AsyncSession, vehicle_id: int, vehicle_data: VehicleUpdate
) -> Vehicle:
    """Actualiza los datos de un vehículo asíncronamente."""
    vehicle = await get_vehicle_by_id(db, vehicle_id)
    update_data = vehicle_data.model_dump(exclude_unset=True)

    # Validar duplicación de placa
    if "plate" in update_data:
        existing_plate = await vehicle_repo.get_by_plate(
            db, plate=update_data["plate"], exclude_id=vehicle_id
        )
        if existing_plate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La placa ya está registrada",
            )

    return await vehicle_repo.update(db, db_obj=vehicle, obj_in=update_data)


async def delete_vehicle(db: AsyncSession, vehicle_id: int) -> None:
    """Elimina un vehículo asíncronamente."""
    vehicle = await get_vehicle_by_id(db, vehicle_id)
    await vehicle_repo.remove(db, id=vehicle.id)
