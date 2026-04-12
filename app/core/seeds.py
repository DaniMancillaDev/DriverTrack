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
        "icon": "directions_car_filled_rounded",
        "image_url": "https://cdn-icons-png.flaticon.com/512/741/741407.png",
    },
    {
        "slug": "motorcycle",
        "label": "Motorcycle",
        "icon": "motorcycle_rounded",
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

    Si ya existen registros, sincroniza los campos icon y label con los
    valores canónicos del catálogo. Esto garantiza que cambios en el seed
    (ej. renombrar un icon) se propaguen sin necesidad de migración manual.

    Returns:
        Número de registros insertados (0 si ya existían, pero pudo haber updates).
    """
    result = await session.execute(select(VehicleType))
    existing = list(result.scalars().all())

    if not existing:
        types = [VehicleType(**data) for data in VEHICLE_TYPES]
        session.add_all(types)
        await session.commit()
        return len(types)

    # Sincronizar campos que puedan haber cambiado en el seed
    slug_map = {d["slug"]: d for d in VEHICLE_TYPES}
    updated = 0
    for vt in existing:
        canonical = slug_map.get(vt.slug)
        if canonical and (vt.icon != canonical["icon"] or vt.label != canonical["label"]):
            vt.icon = canonical["icon"]
            vt.label = canonical["label"]
            updated += 1
    if updated:
        await session.commit()
        print(f"  ✓ Updated {updated} vehicle type(s) to match seed")
    return 0


async def seed_admin_user(session: AsyncSession) -> bool:
    """Crea el usuario admin si no existe, o actualiza su hash si ya existía.

    En desarrollo es normal que la contraseña del seed cambie. Este seed
    siempre sincroniza el hash para que las credenciales del archivo sean
    las que funcionan, evitando errores 401 por hashes obsoletos.

    Returns:
        True si fue creado, False si ya existía (solo actualizado).
    """
    result = await session.execute(
        select(User).where(User.email == ADMIN_EMAIL)
    )
    existing = result.scalars().first()

    if existing is not None:
        # Actualizar el hash por si la contraseña del seed cambió
        existing.hashed_password = get_password_hash(ADMIN_PASSWORD)
        await session.commit()
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
        print(f"  ✓ Admin created: {ADMIN_EMAIL}")
    else:
        print(f"  ✓ Admin already exists: {ADMIN_EMAIL}")
