"""Motor de reglas para notificaciones automáticas.

Evalúa condiciones basadas en datos de vehículos y mantenimientos
para generar notificaciones proactivas. Usa consultas SQL agregadas
(una por regla) en vez de iterar usuario por usuario.

Reglas implementadas:
- mileage_warning: Kilometraje >= 90% del máximo
- mileage_critical: Kilometraje >= 100% del máximo
- maintenance_overdue: Último mantenimiento de una categoría > 180 días
- no_maintenance: Vehículo sin mantenimiento registrado, creado hace >30 días
"""

import json
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, literal, not_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.maintenance import Maintenance
from app.models.notification import Notification, NotificationType
from app.models.notification_cooldown import NotificationCooldown
from app.models.user import User
from app.models.vehicle import Vehicle
from app.routers.notifications_ws import manager
from app.schemas.notification import NotificationResponse

logger = logging.getLogger(__name__)

# ─── Configuración de reglas ──────────────────────────────────

# Cooldown por regla: cuánto tiempo mínimo debe pasar antes de
# enviar la misma notificación para el mismo vehículo.
RULE_COOLDOWNS = {
    "mileage_warning": timedelta(hours=24),
    "mileage_critical": timedelta(hours=24),
    "maintenance_overdue": timedelta(hours=48),
    "no_maintenance": timedelta(hours=72),
}

# Umbral para alerta de kilometraje (proporción del max_mileage)
MILEAGE_WARNING_THRESHOLD = 0.9    # 90%
MILEAGE_CRITICAL_THRESHOLD = 1.0   # 100%

# Días sin mantenimiento para considerar vencido
MAINTENANCE_OVERDUE_DAYS = 180  # 6 meses

# Días mínimos sin mantenimiento para vehículos nuevos
NO_MAINTENANCE_DAYS = 30


# ─── Funciones auxiliares ─────────────────────────────────────

def _cooldown_cutoff(rule_key: str) -> datetime:
    """Calcula el punto de corte temporal para el cooldown de una regla."""
    return datetime.now(timezone.utc) - RULE_COOLDOWNS[rule_key]


async def _create_notifications_batch(
    db: AsyncSession,
    notifications_data: list[dict],
) -> list[Notification]:
    """Crea múltiples notificaciones en una sola transacción.

    También registra los cooldowns correspondientes y envía
    por WebSocket a los usuarios que estén conectados.
    """
    if not notifications_data:
        return []

    created = []
    for data in notifications_data:
        # Crear notificación
        notification = Notification(
            user_id=data["user_id"],
            title=data["title"],
            message=data["message"],
            type=data["type"],
        )
        db.add(notification)

        # Registrar cooldown
        cooldown = NotificationCooldown(
            user_id=data["user_id"],
            vehicle_id=data["vehicle_id"],
            rule_key=data["rule_key"],
        )
        db.add(cooldown)
        created.append(notification)

    await db.commit()

    # Refresh para obtener IDs generados y broadcast por WebSocket
    for notification in created:
        await db.refresh(notification)

        # Enviar por WebSocket al usuario (si está conectado)
        try:
            response = NotificationResponse.model_validate(notification)
            await manager.send_to_user(
                notification.user_id,
                response.model_dump_json(),
            )
        except Exception as e:
            # El WebSocket puede fallar sin afectar la persistencia
            logger.debug(f"WebSocket broadcast falló para user {notification.user_id}: {e}")

    return created


# ─── Reglas de notificación ───────────────────────────────────

async def check_mileage_warning(db: AsyncSession) -> list[dict]:
    """Detecta vehículos con kilometraje >= 90% del máximo.

    UNA sola query con LEFT JOIN contra cooldowns para excluir
    los que ya recibieron esta alerta recientemente.
    """
    rule_key = "mileage_warning"
    cutoff = _cooldown_cutoff(rule_key)

    # Subquery: vehículos que ya tienen cooldown activo para esta regla
    cooldown_subq = (
        select(NotificationCooldown.vehicle_id)
        .where(
            NotificationCooldown.rule_key == rule_key,
            NotificationCooldown.last_sent_at > cutoff,
        )
        .correlate(Vehicle)
        .scalar_subquery()
    )

    # Query principal: vehículos en zona de advertencia (90-99%) sin cooldown
    stmt = (
        select(Vehicle)
        .join(User, Vehicle.user_id == User.id)
        .where(
            User.pref_service_reminders == True,
            Vehicle.max_mileage > 0,
            Vehicle.mileage >= Vehicle.max_mileage * MILEAGE_WARNING_THRESHOLD,
            Vehicle.mileage < Vehicle.max_mileage * MILEAGE_CRITICAL_THRESHOLD,
            not_(Vehicle.id.in_(
                select(NotificationCooldown.vehicle_id).where(
                    NotificationCooldown.rule_key == rule_key,
                    NotificationCooldown.last_sent_at > cutoff,
                )
            )),
        )
    )

    result = await db.execute(stmt)
    vehicles = result.scalars().all()

    notifications = []
    for v in vehicles:
        pct = int((v.mileage / v.max_mileage) * 100)
        notifications.append({
            "user_id": v.user_id,
            "vehicle_id": v.id,
            "rule_key": rule_key,
            "title": rule_key,
            "message": json.dumps({
                "brand": v.brand,
                "model": v.model,
                "plate": v.plate,
                "percent": pct,
                "mileage": f"{v.mileage:,}",
                "max_mileage": f"{v.max_mileage:,}"
            }),
            "type": NotificationType.WARNING,
        })

    return notifications


async def check_mileage_critical(db: AsyncSession) -> list[dict]:
    """Detecta vehículos con kilometraje >= 100% del máximo."""
    rule_key = "mileage_critical"
    cutoff = _cooldown_cutoff(rule_key)

    stmt = (
        select(Vehicle)
        .join(User, Vehicle.user_id == User.id)
        .where(
            User.pref_critical_alerts == True,
            Vehicle.max_mileage > 0,
            Vehicle.mileage >= Vehicle.max_mileage * MILEAGE_CRITICAL_THRESHOLD,
            not_(Vehicle.id.in_(
                select(NotificationCooldown.vehicle_id).where(
                    NotificationCooldown.rule_key == rule_key,
                    NotificationCooldown.last_sent_at > cutoff,
                )
            )),
        )
    )

    result = await db.execute(stmt)
    vehicles = result.scalars().all()

    notifications = []
    for v in vehicles:
        pct = int((v.mileage / v.max_mileage) * 100)
        notifications.append({
            "user_id": v.user_id,
            "vehicle_id": v.id,
            "rule_key": rule_key,
            "title": rule_key,
            "message": json.dumps({
                "brand": v.brand,
                "model": v.model,
                "plate": v.plate,
                "percent": pct,
                "mileage": f"{v.mileage:,}",
                "max_mileage": f"{v.max_mileage:,}"
            }),
            "type": NotificationType.ERROR,
        })

    return notifications


async def check_maintenance_overdue(db: AsyncSession) -> list[dict]:
    """Detecta vehículos cuya última fecha de mantenimiento
    de cualquier categoría supera el umbral configurado.

    Usa una subquery con MAX(date) agrupada por vehicle_id
    para encontrar el mantenimiento más reciente por vehículo.
    """
    rule_key = "maintenance_overdue"
    cutoff = _cooldown_cutoff(rule_key)
    overdue_date = datetime.now(timezone.utc) - timedelta(days=MAINTENANCE_OVERDUE_DAYS)

    # Subquery: fecha del mantenimiento más reciente por vehículo
    latest_maintenance = (
        select(
            Maintenance.vehicle_id,
            func.max(Maintenance.date).label("last_date"),
        )
        .group_by(Maintenance.vehicle_id)
        .subquery()
    )

    stmt = (
        select(Vehicle, latest_maintenance.c.last_date)
        .join(User, Vehicle.user_id == User.id)
        .join(latest_maintenance, Vehicle.id == latest_maintenance.c.vehicle_id)
        .where(
            User.pref_service_reminders == True,
            latest_maintenance.c.last_date < overdue_date.date(),
            not_(Vehicle.id.in_(
                select(NotificationCooldown.vehicle_id).where(
                    NotificationCooldown.rule_key == rule_key,
                    NotificationCooldown.last_sent_at > cutoff,
                )
            )),
        )
    )

    result = await db.execute(stmt)
    rows = result.all()

    notifications = []
    for vehicle, last_date in rows:
        days_since = (datetime.now(timezone.utc).date() - last_date).days
        notifications.append({
            "user_id": vehicle.user_id,
            "vehicle_id": vehicle.id,
            "rule_key": rule_key,
            "title": rule_key,
            "message": json.dumps({
                "brand": vehicle.brand,
                "model": vehicle.model,
                "plate": vehicle.plate,
                "days": days_since,
                "last_date": last_date.strftime('%d/%m/%Y')
            }),
            "type": NotificationType.WARNING,
        })

    return notifications


async def check_no_maintenance(db: AsyncSession) -> list[dict]:
    """Detecta vehículos registrados hace más de 30 días
    que no tienen ningún registro de mantenimiento.
    """
    rule_key = "no_maintenance"
    cutoff = _cooldown_cutoff(rule_key)
    threshold_date = datetime.now(timezone.utc) - timedelta(days=NO_MAINTENANCE_DAYS)

    # Subquery: vehículos que SÍ tienen al menos un mantenimiento
    has_maintenance = (
        select(Maintenance.vehicle_id)
        .distinct()
        .scalar_subquery()
    )

    stmt = (
        select(Vehicle)
        .join(User, Vehicle.user_id == User.id)
        .where(
            User.pref_service_reminders == True,
            Vehicle.created_at < threshold_date,
            not_(Vehicle.id.in_(has_maintenance)),
            not_(Vehicle.id.in_(
                select(NotificationCooldown.vehicle_id).where(
                    NotificationCooldown.rule_key == rule_key,
                    NotificationCooldown.last_sent_at > cutoff,
                )
            )),
        )
    )

    result = await db.execute(stmt)
    vehicles = result.scalars().all()

    notifications = []
    for v in vehicles:
        notifications.append({
            "user_id": v.user_id,
            "vehicle_id": v.id,
            "rule_key": rule_key,
            "title": rule_key,
            "message": json.dumps({
                "brand": v.brand,
                "model": v.model,
                "plate": v.plate
            }),
            "type": NotificationType.INFO,
        })

    return notifications


# ─── Orquestador principal ────────────────────────────────────

async def run_all_checks(db: AsyncSession) -> int:
    """Ejecuta todas las reglas de notificación.

    Retorna la cantidad total de notificaciones generadas.
    Cada regla ejecuta UNA sola query SQL optimizada.
    """
    all_notifications: list[dict] = []

    # Ejecutar cada regla (cada una es una sola query SQL)
    rules = [
        ("mileage_warning", check_mileage_warning),
        ("mileage_critical", check_mileage_critical),
        ("maintenance_overdue", check_maintenance_overdue),
        ("no_maintenance", check_no_maintenance),
    ]

    for rule_name, check_fn in rules:
        try:
            notifications = await check_fn(db)
            all_notifications.extend(notifications)
            if notifications:
                logger.info(
                    f"Regla '{rule_name}': {len(notifications)} notificaciones generadas"
                )
        except Exception as e:
            logger.error(f"Error en regla '{rule_name}': {e}")

    # Crear todas las notificaciones en batch
    if all_notifications:
        created = await _create_notifications_batch(db, all_notifications)
        logger.info(f"Total: {len(created)} notificaciones creadas y enviadas")
        return len(created)

    logger.info("Verificación completada: no se generaron notificaciones nuevas")
    return 0


async def purge_old_cooldowns(db: AsyncSession) -> int:
    """Elimina cooldowns viejos (>7 días) para mantener la tabla ligera.

    Se ejecuta periódicamente por el scheduler.
    """
    from sqlalchemy import delete

    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    result = await db.execute(
        delete(NotificationCooldown).where(
            NotificationCooldown.last_sent_at < cutoff
        )
    )
    await db.commit()

    purged = result.rowcount
    if purged > 0:
        logger.info(f"Cooldowns purgados: {purged} registros antiguos eliminados")
    return purged
