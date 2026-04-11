"""Servicio para control de acceso y validación de propiedad de vehículos.

Provee funciones críticas de seguridad para verificar que el usuario
solicitante es efectivamente el dueño de un vehículo, mitigando ataques
de tipo BOLA (Broken Object Level Authorization).
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vehicle import Vehicle
from app.services import vehicles as vehicles_service


async def assert_vehicle_owner(vehicle_id: int, current_user_id: int, db: AsyncSession) -> Vehicle:
    """Valida de forma estricta que el vehículo pertenece al usuario autenticado.

    Lógica de Seguridad:
    - 404 Not Found: Si el ID del vehículo no existe en el sistema.
    - 403 Forbidden: Si el vehículo existe pero pertenece a un user_id diferente.
    """
    vehicle = await vehicles_service.get_vehicle_by_id(db=db, vehicle_id=vehicle_id)
    
    if vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehículo no encontrado",
        )
        
    if vehicle.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado para operar sobre este vehículo",
        )
        
    return vehicle
