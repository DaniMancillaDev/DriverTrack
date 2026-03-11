"""Router de vehículos."""

from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.vehicle import VehicleCreate, VehicleResponse, VehicleUpdate
from app.services import vehicles as vehicles_service

router = APIRouter(prefix="/vehicles", tags=["Vehículos"])


@router.post(
    "/",
    response_model=VehicleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un vehículo",
)
def create_vehicle(vehicle_data: VehicleCreate, db: Session = Depends(get_db)):
    """Crea un nuevo vehículo asociado a un usuario."""
    return vehicles_service.create_vehicle(db=db, vehicle_data=vehicle_data)


@router.get(
    "/",
    response_model=list[VehicleResponse],
    summary="Listar vehículos",
)
def get_vehicles(
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Obtiene la lista de vehículos, permite filtrar por usuario."""
    return vehicles_service.get_vehicles(db=db, user_id=user_id)


@router.get(
    "/{vehicle_id}",
    response_model=VehicleResponse,
    summary="Obtener detalle de un vehículo",
)
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    """Obtiene los datos de un vehículo específico por su ID."""
    return vehicles_service.get_vehicle_by_id(db=db, vehicle_id=vehicle_id)


@router.put(
    "/{vehicle_id}",
    response_model=VehicleResponse,
    summary="Actualizar un vehículo",
)
def update_vehicle(
    vehicle_id: int,
    vehicle_data: VehicleUpdate,
    db: Session = Depends(get_db),
):
    """Actualiza los campos de un vehículo existente."""
    return vehicles_service.update_vehicle(
        db=db, vehicle_id=vehicle_id, vehicle_data=vehicle_data
    )


@router.delete(
    "/{vehicle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un vehículo",
)
def delete_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    """Elimina un vehículo y todos sus registros de mantenimiento asociados."""
    vehicles_service.delete_vehicle(db=db, vehicle_id=vehicle_id)
