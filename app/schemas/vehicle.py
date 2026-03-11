"""Esquemas de validación para vehículos.

Define los modelos Pydantic para creación, actualización
y respuestas de la API relacionadas a vehículos.
"""

from typing import Optional

from pydantic import BaseModel

from app.models.vehicle import VehicleType


class VehicleCreate(BaseModel):
    """Datos requeridos para registrar un nuevo vehículo.

    Nota: user_id se incluye temporalmente aquí.
    Cuando se implemente JWT, se obtendrá del token.
    """

    user_id: int
    type: VehicleType
    brand: str
    model: str
    plate: str
    year: int


class VehicleUpdate(BaseModel):
    """Datos opcionales para actualizar un vehículo.

    Todos los campos son opcionales; solo se actualizan
    los que se envían en la petición.
    """

    type: Optional[VehicleType] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    plate: Optional[str] = None
    year: Optional[int] = None


class VehicleResponse(BaseModel):
    """Datos del vehículo devueltos por la API."""

    id: int
    user_id: int
    type: VehicleType
    brand: str
    model: str
    plate: str
    year: int

    model_config = {"from_attributes": True}
