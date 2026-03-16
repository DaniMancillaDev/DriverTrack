"""Router de vehículos."""

from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.vehicle import (
    VehicleCreate,
    VehicleResponse,
    VehicleTypeResponse,
    VehicleUpdate,
)
from app.services import vehicles as vehicles_service

router = APIRouter(prefix="/vehicles", tags=["Vehículos"])


@router.get(
    "/types",
    response_model=list[VehicleTypeResponse],
    summary="Listar tipos de vehículos disponibles",
)
async def get_vehicle_types(db: AsyncSession = Depends(get_db)):
    """Obtiene el catálogo de tipos de vehículos asíncronamente."""
    return await vehicles_service.get_vehicle_types(db=db)


@router.post(
    "/",
    response_model=VehicleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un vehículo",
)
async def create_vehicle(vehicle_data: VehicleCreate, db: AsyncSession = Depends(get_db)):
    """Crea un nuevo vehículo asíncronamente."""
    return await vehicles_service.create_vehicle(db=db, vehicle_data=vehicle_data)


@router.get(
    "/",
    response_model=list[VehicleResponse],
    summary="Listar vehículos",
)
async def get_vehicles(
    user_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """Obtiene la lista de vehículos asíncronamente."""
    return await vehicles_service.get_vehicles(db=db, user_id=user_id)


@router.get(
    "/{vehicle_id}",
    response_model=VehicleResponse,
    summary="Obtener detalle de un vehículo",
)
async def get_vehicle(vehicle_id: int, db: AsyncSession = Depends(get_db)):
    """Obtiene los datos de un vehículo asíncronamente."""
    return await vehicles_service.get_vehicle_by_id(db=db, vehicle_id=vehicle_id)


@router.put(
    "/{vehicle_id}",
    response_model=VehicleResponse,
    summary="Actualizar un vehículo",
)
async def update_vehicle(
    vehicle_id: int,
    vehicle_data: VehicleUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Actualiza un vehículo asíncronamente."""
    return await vehicles_service.update_vehicle(
        db=db, vehicle_id=vehicle_id, vehicle_data=vehicle_data
    )


@router.delete(
    "/{vehicle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un vehículo",
)
async def delete_vehicle(vehicle_id: int, db: AsyncSession = Depends(get_db)):
    """Elimina un vehículo asíncronamente."""
    await vehicles_service.delete_vehicle(db=db, vehicle_id=vehicle_id)
