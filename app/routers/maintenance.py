"""Router de mantenimientos."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

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
def create_maintenance(
    vehicle_id: int,
    maintenance_data: MaintenanceCreate,
    db: Session = Depends(get_db),
):
    """Crea un nuevo registro de mantenimiento para un vehículo."""
    return maintenance_service.create_maintenance(
        db=db, vehicle_id=vehicle_id, maintenance_data=maintenance_data
    )


@router.get(
    "/vehicles/{vehicle_id}/maintenance",
    response_model=list[MaintenanceResponse],
    summary="Listar mantenimientos de un vehículo",
)
def get_vehicle_maintenances(
    vehicle_id: int,
    db: Session = Depends(get_db),
):
    """Obtiene todos los registros de mantenimiento de un vehículo."""
    return maintenance_service.get_vehicle_maintenances(db=db, vehicle_id=vehicle_id)


@router.get(
    "/maintenance/{maintenance_id}",
    response_model=MaintenanceResponse,
    summary="Obtener detalle de un mantenimiento",
)
def get_maintenance(maintenance_id: int, db: Session = Depends(get_db)):
    """Obtiene los datos de un registro de mantenimiento por su ID."""
    return maintenance_service.get_maintenance_by_id(db=db, maintenance_id=maintenance_id)


@router.put(
    "/maintenance/{maintenance_id}",
    response_model=MaintenanceResponse,
    summary="Actualizar un mantenimiento",
)
def update_maintenance(
    maintenance_id: int,
    maintenance_data: MaintenanceUpdate,
    db: Session = Depends(get_db),
):
    """Actualiza los campos de un registro de mantenimiento."""
    return maintenance_service.update_maintenance(
        db=db, maintenance_id=maintenance_id, maintenance_data=maintenance_data
    )


@router.delete(
    "/maintenance/{maintenance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un mantenimiento",
)
def delete_maintenance(maintenance_id: int, db: Session = Depends(get_db)):
    """Elimina un registro de mantenimiento por su ID."""
    maintenance_service.delete_maintenance(db=db, maintenance_id=maintenance_id)
