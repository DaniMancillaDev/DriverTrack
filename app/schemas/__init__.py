"""Esquemas de validación Pydantic para la API.

Re-exporta todos los esquemas para uso conveniente:
    from app.schemas import UserCreate, VehicleResponse, etc.
"""

from app.schemas.user import LoginRequest, UserCreate, UserResponse
from app.schemas.vehicle import VehicleCreate, VehicleResponse, VehicleUpdate
from app.schemas.maintenance import (
    MaintenanceCreate,
    MaintenanceResponse,
    MaintenanceUpdate,
)

__all__ = [
    "UserCreate",
    "UserResponse",
    "LoginRequest",
    "VehicleCreate",
    "VehicleUpdate",
    "VehicleResponse",
    "MaintenanceCreate",
    "MaintenanceUpdate",
    "MaintenanceResponse",
]
