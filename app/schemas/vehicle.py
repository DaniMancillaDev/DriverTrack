"""Esquemas de validación para vehículos.

Define los modelos Pydantic para creación, actualización
y respuestas de la API relacionadas a vehículos.
"""

from typing import Optional

from pydantic import BaseModel

class VehicleTypeResponse(BaseModel):
    """Datos de un tipo de vehículo del catálogo."""

    id: int
    slug: str
    label: str
    icon: str
    image_url: str

    model_config = {"from_attributes": True}


class VehicleCreate(BaseModel):
    """Datos requeridos para registrar un nuevo vehículo."""

    user_id: Optional[int] = None
    type_id: int
    brand: str
    model: str
    plate: str
    year: int
    mileage: int = 0
    max_mileage: int = 50000
    image_url: Optional[str] = None
    next_service: Optional[str] = None
    is_favorite: bool = False


class VehicleUpdate(BaseModel):
    """Datos opcionales para actualizar un vehículo."""

    type_id: Optional[int] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    plate: Optional[str] = None
    year: Optional[int] = None
    mileage: Optional[int] = None
    max_mileage: Optional[int] = None
    image_url: Optional[str] = None
    next_service: Optional[str] = None
    is_favorite: Optional[bool] = None


class VehicleResponse(BaseModel):
    """Datos del vehículo devueltos por la API."""

    id: int
    user_id: int
    type_id: int
    brand: str
    model: str
    plate: str
    year: int
    mileage: int
    max_mileage: int
    image_url: Optional[str]
    next_service: Optional[str]
    is_favorite: bool
    vehicle_type: VehicleTypeResponse

    model_config = {"from_attributes": True}
