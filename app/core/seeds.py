"""Datos de catálogo (seeds) para la base de datos.

Se ejecuta al iniciar el servidor. Solo inserta datos si las tablas
de catálogo están vacías, así que es idempotente y seguro de correr
cada vez que inicia la app.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vehicle import VehicleType


VEHICLE_TYPES = [
    {
        "slug": "car",
        "label": "Car",
        "icon": "directions_car",
        "image_url": "https://cdn-icons-png.flaticon.com/512/741/741407.png",
    },
    {
        "slug": "motorcycle",
        "label": "Motorcycle",
        "icon": "two_wheeler",
        "image_url": "https://cdn-icons-png.flaticon.com/512/2451/2451685.png",
    },
]


async def seed_vehicle_types(session: AsyncSession) -> int:
    """Inserta los tipos de vehículo si la tabla está vacía.
    
    Returns:
        Número de registros insertados (0 si ya existían).
    """
    result = await session.execute(select(VehicleType).limit(1))
    if result.scalars().first() is not None:
        return 0

    types = [VehicleType(**data) for data in VEHICLE_TYPES]
    session.add_all(types)
    await session.commit()
    return len(types)


async def run_seeds(session: AsyncSession) -> None:
    """Ejecuta todos los seeders de catálogo."""
    count = await seed_vehicle_types(session)
    if count > 0:
        print(f"  ✓ Seeded {count} vehicle types")
    else:
        print("  ✓ Vehicle types already present")
