"""Scheduler de notificaciones automáticas.

Ejecuta las reglas de notificación periódicamente usando
asyncio.create_task integrado con el lifespan de FastAPI.
No requiere dependencias externas (sin Celery, sin APScheduler).

Intervalos configurables:
- CHECK_INTERVAL: cada cuánto se ejecutan las reglas (default: 6 horas)
- PURGE_INTERVAL: cada cuánto se limpian cooldowns viejos (default: 24 horas)
"""

import asyncio
import logging
from datetime import timedelta

from app.database import AsyncSessionLocal
from app.services.notification_rules import purge_old_cooldowns, run_all_checks

logger = logging.getLogger(__name__)

# ─── Configuración de intervalos ──────────────────────────────

# Intervalo entre ejecuciones del checker de reglas
CHECK_INTERVAL = timedelta(hours=6)

# Intervalo entre purgas de cooldowns viejos
PURGE_INTERVAL = timedelta(hours=24)


# ─── Task principal ──────────────────────────────────────────

async def _run_check_cycle():
    """Ejecuta un ciclo de verificación de reglas.

    Abre su propia sesión de DB para ser independiente
    del ciclo de vida de las peticiones HTTP.
    """
    try:
        async with AsyncSessionLocal() as db:
            count = await run_all_checks(db)
            logger.info(
                f"Ciclo de notificaciones completado: "
                f"{count} notificaciones generadas"
            )
    except Exception as e:
        logger.error(f"Error en ciclo de notificaciones: {e}", exc_info=True)


async def _run_purge_cycle():
    """Ejecuta un ciclo de purga de cooldowns viejos."""
    try:
        async with AsyncSessionLocal() as db:
            purged = await purge_old_cooldowns(db)
            logger.info(f"Purga de cooldowns completada: {purged} eliminados")
    except Exception as e:
        logger.error(f"Error en purga de cooldowns: {e}", exc_info=True)


async def notification_scheduler_loop():
    """Loop principal del scheduler de notificaciones.

    Corre indefinidamente, ejecutando verificaciones cada
    CHECK_INTERVAL y purgas cada PURGE_INTERVAL.

    Se cancela automáticamente cuando FastAPI se apaga
    (al llamar task.cancel() desde el lifespan).
    """
    logger.info(
        f"Scheduler de notificaciones iniciado "
        f"(check: cada {CHECK_INTERVAL}, purge: cada {PURGE_INTERVAL})"
    )

    check_seconds = CHECK_INTERVAL.total_seconds()
    purge_seconds = PURGE_INTERVAL.total_seconds()
    elapsed = 0.0
    tick = 60.0  # Revisar cada minuto si es hora de ejecutar

    # Ejecutar la primera verificación 30 segundos después del arranque
    # para dar tiempo a que las tablas se creen
    await asyncio.sleep(30)
    await _run_check_cycle()

    while True:
        try:
            await asyncio.sleep(tick)
            elapsed += tick

            # Verificar reglas cada CHECK_INTERVAL
            if elapsed >= check_seconds:
                await _run_check_cycle()
                elapsed = 0.0

            # Purgar cooldowns cada PURGE_INTERVAL
            # (usa el mismo contador, se ejecuta cuando es múltiplo)
            if elapsed % purge_seconds < tick:
                await _run_purge_cycle()

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
