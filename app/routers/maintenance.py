"""Router de mantenimientos.

Este módulo gestiona el ciclo de vida de los registros de mantenimiento
(servicios, reparaciones, revisiones) asociados a los vehículos del usuario.
Garantiza que un usuario solo pueda operar sobre mantenimientos de su propiedad.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser
from app.database import get_db
from app.schemas.maintenance import (
    MaintenanceCreate,
    MaintenanceResponse,
    MaintenanceUpdate,
)
from app.services import maintenance as maintenance_service
from app.services.vehicle_access import assert_vehicle_owner

router = APIRouter(tags=["Mantenimientos"])

# ─── Endpoints de mantenimiento por vehículo ─────────────────


@router.post(
    "/vehicles/{vehicle_id}/maintenance",
    response_model=MaintenanceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un mantenimiento",
)
async def create_maintenance(
    vehicle_id: int,
    maintenance_data: MaintenanceCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Crea un registro de mantenimiento para un vehículo.

    Verificaciones:
    - El vehículo debe existir.
    - El vehículo debe pertenecer al usuario autenticado.
    """
    await assert_vehicle_owner(vehicle_id, current_user.id, db)
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
    current_user: CurrentUser,
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(50, ge=1, le=100, description="Límite máximo de resultados"),
    db: AsyncSession = Depends(get_db),
):
    """Obtiene el historial de mantenimientos de un vehículo específico.

    Soporta paginación mediante los parámetros `skip` y `limit`.
    """
    await assert_vehicle_owner(vehicle_id, current_user.id, db)
    return await maintenance_service.get_vehicle_maintenances(
        db=db, vehicle_id=vehicle_id, skip=skip, limit=limit
    )


@router.get(
    "/maintenance",
    response_model=list[MaintenanceResponse],
    summary="Listar todos mis mantenimientos",
)
async def get_all_my_maintenances(
    current_user: CurrentUser,
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(50, ge=1, le=100, description="Límite máximo de resultados"),
    db: AsyncSession = Depends(get_db),
):
    """Obtiene el historial consolidado de todos los vehículos del usuario.

    Es útil para vistas generales de 'Actividad Reciente' o 'Gastos Totales'
    sin tener que consultar vehículo por vehículo.
    """
    return await maintenance_service.get_user_maintenances(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )


@router.get(
    "/maintenance/{maintenance_id}",
    response_model=MaintenanceResponse,
    summary="Obtener detalle de un mantenimiento",
)
async def get_maintenance(
    maintenance_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Obtiene un registro de mantenimiento verificando la propiedad."""
    maintenance = await maintenance_service.get_maintenance_by_id(
        db=db, maintenance_id=maintenance_id
    )
    if maintenance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Mantenimiento no encontrado"
        )
    # Verificar propiedad a través del vehículo
    await assert_vehicle_owner(maintenance.vehicle_id, current_user.id, db)
    return maintenance


@router.put(
    "/maintenance/{maintenance_id}",
    response_model=MaintenanceResponse,
    summary="Actualizar un mantenimiento",
)
async def update_maintenance(
    maintenance_id: int,
    maintenance_data: MaintenanceUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Actualiza un registro de mantenimiento del usuario."""
    maintenance = await maintenance_service.get_maintenance_by_id(
        db=db, maintenance_id=maintenance_id
    )
    if maintenance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Mantenimiento no encontrado"
        )
    await assert_vehicle_owner(maintenance.vehicle_id, current_user.id, db)
    return await maintenance_service.update_maintenance(
        db=db, maintenance_id=maintenance_id, maintenance_data=maintenance_data
    )


@router.delete(
    "/maintenance/{maintenance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un mantenimiento",
)
async def delete_maintenance(
    maintenance_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Elimina un registro de mantenimiento del usuario."""
    maintenance = await maintenance_service.get_maintenance_by_id(
        db=db, maintenance_id=maintenance_id
    )
    if maintenance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Mantenimiento no encontrado"
        )
    await assert_vehicle_owner(maintenance.vehicle_id, current_user.id, db)
    await maintenance_service.delete_maintenance(db=db, maintenance_id=maintenance_id)
