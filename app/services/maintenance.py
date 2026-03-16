"""Servicios para el registro de mantenimientos."""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.maintenance import Maintenance
from app.repositories.maintenance import maintenance_repo
from app.repositories.vehicle import vehicle_repo
from app.schemas.maintenance import MaintenanceCreate, MaintenanceUpdate


async def create_maintenance(
    db: AsyncSession, vehicle_id: int, maintenance_data: MaintenanceCreate
) -> Maintenance:
    """Registra un nuevo mantenimiento asíncronamente."""
    vehicle = await vehicle_repo.get(db, id=vehicle_id)
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehículo no encontrado",
        )

    return await maintenance_repo.create_with_vehicle(
        db, obj_in=maintenance_data, vehicle_id=vehicle_id
    )


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


async def get_maintenance_by_id(db: AsyncSession, maintenance_id: int) -> Maintenance:
    """Busca un registro asíncronamente."""
    maintenance = await maintenance_repo.get(db, id=maintenance_id)
    if not maintenance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de mantenimiento no encontrado",
        )
    return maintenance


async def update_maintenance(
    db: AsyncSession, maintenance_id: int, maintenance_data: MaintenanceUpdate
) -> Maintenance:
    """Actualiza la información asíncronamente."""
    maintenance = await get_maintenance_by_id(db, maintenance_id)

    return await maintenance_repo.update(db, db_obj=maintenance, obj_in=maintenance_data)


async def delete_maintenance(db: AsyncSession, maintenance_id: int) -> None:
    """Elimina un registro asíncronamente."""
    maintenance = await get_maintenance_by_id(db, maintenance_id)
    await maintenance_repo.remove(db, id=maintenance.id)
