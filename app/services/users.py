"""Servicios para la gestión de perfiles de usuario.

Contiene la lógica de negocio para la administración de cuentas,
actualización de perfiles, gestión de preferencias de notificación
y flujos de seguridad como el cambio de contraseñas.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.models.user import User
from app.schemas.user import UserUpdate
from app.core.security import get_password_hash, verify_password


async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    """Obtiene un registro de usuario por su clave primaria.

    Retorna el modelo SQLAlchemy completo o None si no se encuentra.
    """
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalars().first()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Obtiene un usuario por su email (para compatibilidad con tokens legacy).

    Usado en get_current_user cuando el claim 'sub' del JWT contiene
    un email en lugar de un user_id (formato anterior a la migración).
    """
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()


async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
    """Obtiene una lista de usuarios asíncronamente."""
    result = await db.execute(select(User).offset(skip).limit(limit))
    return list(result.scalars().all())


async def update_user(db: AsyncSession, user_id: int, user_data: UserUpdate) -> Optional[User]:
    """Actualiza la información de un usuario asíncronamente."""
    db_user = await get_user(db, user_id)
    if not db_user:
        return None

    update_data = user_data.model_dump(exclude_unset=True)
    
    if "password" in update_data and update_data["password"]:
        hashed_password = get_password_hash(update_data["password"])
        update_data["hashed_password"] = hashed_password
        del update_data["password"]

    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def update_profile(db: AsyncSession, user_id: int, full_name: str) -> Optional[User]:
    """Actualiza solo el nombre del usuario autenticado."""
    db_user = await get_user(db, user_id)
    if not db_user:
        return None

    db_user.full_name = full_name
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def update_preferences(
    db: AsyncSession,
    user_id: int,
    push_notifications: Optional[bool] = None,
    service_reminders: Optional[bool] = None,
    critical_alerts: Optional[bool] = None,
) -> Optional[User]:
    """Actualiza las preferencias de notificaciones del usuario."""
    db_user = await get_user(db, user_id)
    if not db_user:
        return None

    if push_notifications is not None:
        db_user.pref_push_notifications = push_notifications
    if service_reminders is not None:
        db_user.pref_service_reminders = service_reminders
    if critical_alerts is not None:
        db_user.pref_critical_alerts = critical_alerts

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def change_password(
    db: AsyncSession,
    user_id: int,
    current_password: str,
    new_password: str,
) -> tuple[bool, str]:
    """Cambia la contraseña de un usuario validando su identidad.

    Proceso:
    1. Verifica que la contraseña actual sea correcta.
    2. Hashea la nueva contraseña.
    3. Registra la fecha del cambio para invalidar tokens si es necesario.
    """
    db_user = await get_user(db, user_id)
    if not db_user:
        return False, "Usuario no encontrado"

    if not verify_password(current_password, db_user.hashed_password):
        return False, "Contraseña actual incorrecta"

    db_user.hashed_password = get_password_hash(new_password)
    db_user.password_changed_at = datetime.now(timezone.utc)
    db.add(db_user)
    await db.commit()
    return True, "Contraseña actualizada exitosamente"


async def update_photo_url(db: AsyncSession, user_id: int, photo_url: str | None) -> Optional[User]:
    """Actualiza la URL de la foto de perfil del usuario."""
    db_user = await get_user(db, user_id)
    if not db_user:
        return None

    db_user.photo_url = photo_url
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def delete_user(db: AsyncSession, user_id: int) -> bool:
    """Elimina un usuario asíncronamente."""
    db_user = await get_user(db, user_id)
    if not db_user:
        return False
        
    await db.delete(db_user)
    await db.commit()
    return True
