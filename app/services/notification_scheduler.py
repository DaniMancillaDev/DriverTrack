"""Planificador (Scheduler) de tareas automáticas.

Gestiona la ejecución periódica de procesos en segundo plano, como la
verificación de reglas de mantenimiento y la limpieza de registros
de 'cooldown' obsoletos. Funciona de forma integrada con el ciclo de vida
de FastAPI sin requerir sistemas externos como Celery.
"""

import asyncio
import logging
from datetime import timedelta

from app.database import AsyncSessionLocal
from app.services.notification_rules import purge_old_cooldowns, run_all_checks
from app.models.scheduler_lock import SchedulerLock
from sqlalchemy import select
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ─── Configuración de intervalos ──────────────────────────────

# Intervalo entre ejecuciones del checker de reglas
CHECK_INTERVAL = timedelta(hours=6)

# Intervalo entre purgas de cooldowns viejos
PURGE_INTERVAL = timedelta(hours=24)


# ─── Task principal ──────────────────────────────────────────

async def _try_acquire_and_run(task_name: str, interval: timedelta, run_func):
    """Implementa un mecanismo de bloqueo (lock) distribuido simple.

    Asegura que, en entornos con múltiples trabajadores (workers), una tarea
    solo se ejecute si ha pasado el intervalo de tiempo definido desde
    su última ejecución exitosa.
    """
    try:
        async with AsyncSessionLocal() as db:
            # Upsert logic and timestamp check
            result = await db.execute(select(SchedulerLock).where(SchedulerLock.task_name == task_name))
            lock = result.scalars().first()
            now = datetime.now(timezone.utc)

            if lock:
                # Add timezone info to lock.last_run_at if it's naive (SQLite behavior)
                last_run = lock.last_run_at.replace(tzinfo=timezone.utc) if lock.last_run_at.tzinfo is None else lock.last_run_at
                if (now - last_run) < interval:
                    # Alguien más ya la corrió recientemente
                    return
            else:
                lock = SchedulerLock(task_name=task_name)
                db.add(lock)

            lock.last_run_at = now
            await db.commit()
            
            # Ejecutar la lógica real ya que logramos entrar
            await run_func(db)
            
    except Exception as e:
        logger.error(f"Error en tarea {task_name}: {e}", exc_info=True)


async def _run_check_cycle():
    """Ejecuta un ciclo de verificación de reglas."""
    async def logic(db):
        count = await run_all_checks(db)
        logger.info(f"Ciclo completado: {count} notif generadas")

    await _try_acquire_and_run("notification_check", CHECK_INTERVAL, logic)


async def _run_purge_cycle():
    """Ejecuta un ciclo de purga de cooldowns viejos."""
    async def logic(db):
        purged = await purge_old_cooldowns(db)
        logger.info(f"Purga completada: {purged} eliminados")

    await _try_acquire_and_run("notification_purge", PURGE_INTERVAL, logic)


async def notification_scheduler_loop():
    """Bucle principal de ejecución del planificador.

    Se mantiene en ejecución mientras la aplicación esté activa, coordinando
    la frecuencia de las verificaciones de mantenimiento y las purgas de datos.
    Se detiene de forma limpia mediante la cancelación de la tarea de asyncio.
    """
    logger.info(
        f"Scheduler de notificaciones iniciado "
        f"(check: cada {CHECK_INTERVAL}, purge: cada {PURGE_INTERVAL})"
    )

    check_seconds = CHECK_INTERVAL.total_seconds()
    purge_seconds = PURGE_INTERVAL.total_seconds()
    check_elapsed = 0.0
    purge_elapsed = 0.0
    tick = 60.0  # Revisar cada minuto si es hora de ejecutar

    # Ejecutar la primera verificación 30 segundos después del arranque
    # para dar tiempo a que las tablas se creen
    await asyncio.sleep(30)
    await _run_check_cycle()

    while True:
        try:
            await asyncio.sleep(tick)
            check_elapsed += tick
            purge_elapsed += tick

            # Verificar reglas cada CHECK_INTERVAL
            if check_elapsed >= check_seconds:
                await _run_check_cycle()
                check_elapsed = 0.0

            # Purgar cooldowns cada PURGE_INTERVAL
            if purge_elapsed >= purge_seconds:
                await _run_purge_cycle()
                purge_elapsed = 0.0

        except asyncio.CancelledError:
            logger.info("Scheduler de notificaciones detenido (shutdown)")
            break
        except Exception as e:
            logger.error(
                f"Error inesperado en scheduler: {e}",
                exc_info=True,
            )
            # Esperar 5 minutos antes de reintentar tras un error grave
            await asyncio.sleep(300)
