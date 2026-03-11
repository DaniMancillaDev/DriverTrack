"""Servicios para la gestión de vehículos."""

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.vehicle import Vehicle
from app.repositories.user import user_repo
from app.repositories.vehicle import vehicle_repo
from app.schemas.vehicle import VehicleCreate, VehicleUpdate


def create_vehicle(db: Session, vehicle_data: VehicleCreate) -> Vehicle:
    """Registra un nuevo vehículo asegurando validaciones de negocio."""
    # Verificamos si existe el usuario usando su repo
    user = user_repo.get(db, id=vehicle_data.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    # Verificamos si la placa existe usando el repo
    existing_plate = vehicle_repo.get_by_plate(db, plate=vehicle_data.plate)
    if existing_plate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La placa ya está registrada",
        )

    # Creamos el registro en DB
    return vehicle_repo.create(db, obj_in=vehicle_data)


def get_vehicles(db: Session, user_id: Optional[int] = None) -> list[Vehicle]:
    """Obtiene la lista de vehículos, opcionalmente filtrados por usuario."""
    if user_id is not None:
        return vehicle_repo.get_by_user(db, user_id=user_id)
    return vehicle_repo.get_all(db)


def get_vehicle_by_id(db: Session, vehicle_id: int) -> Vehicle:
    """Obtiene un vehículo o lanza error 404 si no existe."""
    vehicle = vehicle_repo.get(db, id=vehicle_id)
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehículo no encontrado",
        )
    return vehicle


def update_vehicle(
    db: Session, vehicle_id: int, vehicle_data: VehicleUpdate
) -> Vehicle:
    """Actualiza los datos de un vehículo existente."""
    vehicle = get_vehicle_by_id(db, vehicle_id)
    update_data = vehicle_data.model_dump(exclude_unset=True)

    # Validar duplicación de placa ignorando el propio vehículo
    if "plate" in update_data:
        existing_plate = vehicle_repo.get_by_plate(
            db, plate=update_data["plate"], exclude_id=vehicle_id
        )
        if existing_plate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La placa ya está registrada",
            )

    return vehicle_repo.update(db, db_obj=vehicle, obj_in=update_data)


def delete_vehicle(db: Session, vehicle_id: int) -> None:
    """Elimina un vehículo del sistema."""
    vehicle = get_vehicle_by_id(db, vehicle_id)
    vehicle_repo.remove(db, id=vehicle.id)
