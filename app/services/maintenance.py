"""Servicios para el registro de mantenimientos."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.maintenance import Maintenance
from app.repositories.maintenance import maintenance_repo
from app.repositories.vehicle import vehicle_repo
from app.schemas.maintenance import MaintenanceCreate, MaintenanceUpdate


def create_maintenance(
    db: Session, vehicle_id: int, maintenance_data: MaintenanceCreate
) -> Maintenance:
    """Registra un nuevo mantenimiento para un vehículo."""
    # Verificar vehículo con el repo abstracto
    vehicle = vehicle_repo.get(db, id=vehicle_id)
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehículo no encontrado",
        )

    # Crear desde el repo
    return maintenance_repo.create_with_vehicle(
        db, obj_in=maintenance_data, vehicle_id=vehicle_id
    )


def get_vehicle_maintenances(db: Session, vehicle_id: int) -> list[Maintenance]:
    """Obtiene el historial de mantenimientos de un vehículo."""
    vehicle = vehicle_repo.get(db, id=vehicle_id)
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehículo no encontrado",
        )

    return maintenance_repo.get_by_vehicle(db, vehicle_id=vehicle_id)


def get_maintenance_by_id(db: Session, maintenance_id: int) -> Maintenance:
    """Busca un registro de mantenimiento o lanza 404."""
    maintenance = maintenance_repo.get(db, id=maintenance_id)
    if not maintenance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de mantenimiento no encontrado",
        )
    return maintenance


def update_maintenance(
    db: Session, maintenance_id: int, maintenance_data: MaintenanceUpdate
) -> Maintenance:
    """Actualiza la información de un mantenimiento existente."""
    maintenance = get_maintenance_by_id(db, maintenance_id)

    return maintenance_repo.update(db, db_obj=maintenance, obj_in=maintenance_data)


def delete_maintenance(db: Session, maintenance_id: int) -> None:
    """Elimina un registro de mantenimiento."""
    maintenance = get_maintenance_by_id(db, maintenance_id)
    maintenance_repo.remove(db, id=maintenance.id)
