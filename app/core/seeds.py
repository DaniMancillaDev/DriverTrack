"""Datos de catálogo (seeds) para la base de datos.

Se ejecuta al iniciar el servidor. Solo inserta datos si las tablas
de catálogo están vacías, así que es idempotente y seguro de correr
cada vez que inicia la app.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vehicle import VehicleType
from app.models.user import User
from app.core.security import get_password_hash


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

# ─── Cuenta de admin para desarrollo ─────────────────────────
# Credenciales: admin@admin.com / Admin1234
# La contraseña se hashea en el seed — no está en texto plano aquí.
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "Admin1234"       # ← Cumple validación: mayúscula + número
ADMIN_FULL_NAME = "Admin DriveTrack"


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


async def seed_admin_user(session: AsyncSession) -> bool:
    """Crea el usuario admin si no existe.

    Returns:
        True si fue creado, False si ya existía.
    """
    result = await session.execute(
        select(User).where(User.email == ADMIN_EMAIL)
    )
    if result.scalars().first() is not None:
        return False

    admin = User(
        email=ADMIN_EMAIL,
        hashed_password=get_password_hash(ADMIN_PASSWORD),
        full_name=ADMIN_FULL_NAME,
        is_active=True,
    )
    session.add(admin)
    await session.commit()
    return True


async def run_seeds(session: AsyncSession) -> None:
    """Ejecuta todos los seeders de catálogo."""
    count = await seed_vehicle_types(session)
    if count > 0:
        print(f"  ✓ Seeded {count} vehicle types")
    else:
        print("  ✓ Vehicle types already present")

    created = await seed_admin_user(session)
    if created:
        print(f"  ✓ Admin created: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
    else:
        print(f"  ✓ Admin already exists: {ADMIN_EMAIL}")
