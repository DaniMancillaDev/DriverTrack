"""Router de mantenimientos."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.maintenance import (
    MaintenanceCreate,
    MaintenanceResponse,
    MaintenanceUpdate,
)
from app.services import maintenance as maintenance_service

router = APIRouter(tags=["Mantenimientos"])


@router.post(
    "/vehicles/{vehicle_id}/maintenance",
    response_model=MaintenanceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un mantenimiento",
)
async def create_maintenance(
    vehicle_id: int,
    maintenance_data: MaintenanceCreate,
    db: AsyncSession = Depends(get_db),
):
    """Crea un registro de mantenimiento asíncronamente."""
    return await maintenance_service.create_maintenance(
        db=db, vehicle_id=vehicle_id, maintenance_data=maintenance_data
    )


@router.get(
    "/vehicles/{vehicle_id}/maintenance",
    response_model=list[MaintenanceResponse],
    summary="Listar mantenimientos de un vehículo",
)
async def get_vehicle_maintenances(
    vehicle_id: int,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Obtiene los registros asíncronamente con paginación."""
    return await maintenance_service.get_vehicle_maintenances(
        db=db, vehicle_id=vehicle_id, skip=skip, limit=limit
    )


@router.get(
    "/maintenance/{maintenance_id}",
    response_model=MaintenanceResponse,
    summary="Obtener detalle de un mantenimiento",
)
async def get_maintenance(maintenance_id: int, db: AsyncSession = Depends(get_db)):
    """Obtiene un registro asíncronamente."""
    return await maintenance_service.get_maintenance_by_id(db=db, maintenance_id=maintenance_id)


@router.put(
    "/maintenance/{maintenance_id}",
    response_model=MaintenanceResponse,
    summary="Actualizar un mantenimiento",
)
async def update_maintenance(
    maintenance_id: int,
    maintenance_data: MaintenanceUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Actualiza un registro asíncronamente."""
    return await maintenance_service.update_maintenance(
        db=db, maintenance_id=maintenance_id, maintenance_data=maintenance_data
    )


@router.delete(
    "/maintenance/{maintenance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un mantenimiento",
)
async def delete_maintenance(maintenance_id: int, db: AsyncSession = Depends(get_db)):
    """Elimina un registro asíncronamente."""
    await maintenance_service.delete_maintenance(db=db, maintenance_id=maintenance_id)
