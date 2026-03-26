"""Esquemas de validación para mantenimientos.

Define los modelos Pydantic para creación, actualización
y respuestas de la API relacionadas a registros de mantenimiento.
"""

import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class MaintenanceCreate(BaseModel):
    """Datos requeridos para crear un registro de mantenimiento.

    El vehicle_id se recibe como parámetro de ruta,
    no en el cuerpo de la petición.
    """

    date: datetime.date
    description: str
    cost: Decimal
    mileage: int
    category: str = "General"


class MaintenanceUpdate(BaseModel):
    """Datos opcionales para actualizar un registro de mantenimiento.

    Solo se actualizan los campos enviados en la petición.
    """

    date: Optional[datetime.date] = None
    description: Optional[str] = None
    cost: Optional[Decimal] = None
    mileage: Optional[int] = None
    category: Optional[str] = None


class MaintenanceResponse(BaseModel):
    """Datos del mantenimiento devueltos por la API."""

    id: int
    vehicle_id: int
    date: datetime.date
    description: str
    cost: Decimal
    mileage: int
    category: str = "General"

    model_config = {"from_attributes": True}
