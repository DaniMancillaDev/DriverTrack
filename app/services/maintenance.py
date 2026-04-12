"""Servicios para la gestión del historial de mantenimientos.

Centraliza la lógica para registrar servicios técnicos, consultar
el historial por vehículo y obtener reportes consolidados para el usuario.
"""

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.maintenance import Maintenance
from app.models.vehicle import Vehicle
from app.repositories.maintenance import maintenance_repo
from app.repositories.vehicle import vehicle_repo
from app.schemas.maintenance import MaintenanceCreate, MaintenanceUpdate


async def create_maintenance(
    db: AsyncSession, vehicle_id: int, maintenance_data: MaintenanceCreate
) -> Maintenance:
    """Registra una nueva actividad de mantenimiento para un vehículo.

    Valida que el vehículo exista antes de crear el registro vinculado.
    """
    vehicle = await vehicle_repo.get(db, id=vehicle_id)
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehículo no encontrado",
        )

    maintenance = await maintenance_repo.create_with_vehicle(
        db, obj_in=maintenance_data, vehicle_id=vehicle_id
    )

    # Sincronización automática: Si el kilometraje del mantenimiento es mayor, 
    # actualizamos el odómetro del vehículo.
    if maintenance.mileage > vehicle.mileage:
        await vehicle_repo.update(db, db_obj=vehicle, obj_in={"mileage": maintenance.mileage})

    return maintenance


async def get_vehicle_maintenances(
    db: AsyncSession, vehicle_id: int, skip: int = 0, limit: int = 50
) -> list[Maintenance]:
    """Obtiene el historial asíncronamente con paginación."""
    vehicle = await vehicle_repo.get(db, id=vehicle_id)
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehículo no encontrado",
        )

    return await maintenance_repo.get_by_vehicle(
        db, vehicle_id=vehicle_id, skip=skip, limit=limit
    )


async def get_maintenance_by_id(
    db: AsyncSession, maintenance_id: int
) -> Optional[Maintenance]:
    """Busca un registro por ID. Retorna None si no existe.

    El router es responsable de lanzar el 404 si es necesario.
    """
    return await maintenance_repo.get(db, id=maintenance_id)


async def update_maintenance(
    db: AsyncSession, maintenance_id: int, maintenance_data: MaintenanceUpdate
) -> Maintenance:
    """Actualiza la información asíncronamente."""
    maintenance = await get_maintenance_by_id(db, maintenance_id)

    return await maintenance_repo.update(db, db_obj=maintenance, obj_in=maintenance_data)


async def delete_maintenance(db: AsyncSession, maintenance_id: int) -> None:
    """Elimina un registro de mantenimiento asíncronamente."""
    maintenance = await get_maintenance_by_id(db, maintenance_id)
    await maintenance_repo.remove(db, id=maintenance.id)


async def get_all_maintenances(
    db: AsyncSession, skip: int = 0, limit: int = 50
) -> list[Maintenance]:
    """Obtiene todos los registros de mantenimiento con paginación (uso interno)."""
    return await maintenance_repo.get_all_sorted(db, skip=skip, limit=limit)


async def get_user_maintenances(
    db: AsyncSession, user_id: int, skip: int = 0, limit: int = 50
) -> list[Maintenance]:
    """Obtiene el historial completo de mantenimientos de un usuario.

    Realiza un Join con la tabla de vehículos para filtrar todos los
    registros que pertenecen a los vehículos de un usuario específico.
    """
    result = await db.execute(
        select(Maintenance)
        .join(Vehicle, Maintenance.vehicle_id == Vehicle.id)
        .where(Vehicle.user_id == user_id)
        .order_by(Maintenance.date.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())
