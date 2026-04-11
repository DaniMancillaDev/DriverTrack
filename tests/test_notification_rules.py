"""Tests para el sistema de notificaciones automáticas.

Cubre:
- Modelo NotificationCooldown
- Reglas de kilometraje (warning y critical)
- Regla de mantenimiento vencido
- Regla de vehículo sin mantenimiento
- Anti-duplicación por cooldown
- Función run_all_checks (orquestador)
- Scheduler (inicio y cancelación)

Usa SQLite en memoria para aislamiento completo.
"""

import asyncio
from datetime import date, datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# ─── Engine en memoria ────────────────────────────────────────

DATABASE_URL = "sqlite+aiosqlite:///:memory:"


class Base(DeclarativeBase):
    pass


# ─── Fixtures ─────────────────────────────────────────────────

@pytest_asyncio.fixture(scope="function")
async def db():
    """Sesión de BD en memoria por cada test. Se descarta al terminar."""
    # Importar modelos para que SQLAlchemy los registre con la Base correcta
    from app.database import Base as AppBase
    from app.models import User, Vehicle, VehicleType, Maintenance, Notification, NotificationCooldown

    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(AppBase.metadata.create_all)

    AsyncTestSession = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with AsyncTestSession() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(AppBase.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def vehicle_type(db):
    """Tipo de vehículo base para los tests."""
    from app.models.vehicle import VehicleType
    vt = VehicleType(
        slug="car",
        label="Car",
        icon="directions_car",
        image_url="https://example.com/car.png",
    )
    db.add(vt)
    await db.commit()
    await db.refresh(vt)
    return vt


@pytest_asyncio.fixture
async def user(db):
    """Usuario de prueba."""
    from app.models.user import User
    from app.core.security import get_password_hash
    u = User(
        email="test@test.com",
        hashed_password=get_password_hash("Test1234"),
        full_name="Test User",
        is_active=True,
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


def make_vehicle(user_id: int, type_id: int, mileage: int, max_mileage: int, days_old: int = 60):
    """Factory para crear vehículos de prueba."""
    from app.models.vehicle import Vehicle
    return Vehicle(
        user_id=user_id,
        type_id=type_id,
        brand="Toyota",
        model="Corolla",
        plate=f"TST-{mileage:04d}",
        year=2020,
        mileage=mileage,
        max_mileage=max_mileage,
        created_at=datetime.now(timezone.utc) - timedelta(days=days_old),
    )


def make_maintenance(vehicle_id: int, days_ago: int, category: str = "General"):
    """Factory para crear mantenimientos de prueba."""
    from app.models.maintenance import Maintenance
    maintenance_date = date.today() - timedelta(days=days_ago)
    return Maintenance(
        vehicle_id=vehicle_id,
        date=maintenance_date,
        description=f"Servicio {category}",
        cost=100.00,
        mileage=5000,
        category=category,
    )


# ─── Tests: Modelo NotificationCooldown ──────────────────────

class TestNotificationCooldownModel:
    async def test_cooldown_se_crea_correctamente(self, db, user, vehicle_type):
        from app.models.notification_cooldown import NotificationCooldown
        v = make_vehicle(user.id, vehicle_type.id, 45000, 50000)
        db.add(v)
        await db.commit()
        await db.refresh(v)

        cooldown = NotificationCooldown(
            user_id=user.id,
            vehicle_id=v.id,
            rule_key="mileage_warning",
        )
        db.add(cooldown)
        await db.commit()
        await db.refresh(cooldown)

        assert cooldown.id is not None
        assert cooldown.vehicle_id == v.id
        assert cooldown.rule_key == "mileage_warning"
        assert cooldown.last_sent_at is not None

    async def test_cooldown_repr(self, db, user, vehicle_type):
        from app.models.notification_cooldown import NotificationCooldown
        v = make_vehicle(user.id, vehicle_type.id, 45000, 50000)
        db.add(v)
        await db.commit()
        await db.refresh(v)

        cooldown = NotificationCooldown(
            user_id=user.id,
            vehicle_id=v.id,
            rule_key="mileage_warning",
        )
        db.add(cooldown)
        await db.commit()
        await db.refresh(cooldown)

        assert "mileage_warning" in repr(cooldown)
        assert str(v.id) in repr(cooldown)


# ─── Tests: Regla mileage_warning ────────────────────────────

class TestMileageWarningRule:
    async def test_genera_alerta_cuando_mileage_es_90_pct(self, db, user, vehicle_type):
        """90% exacto debe generar alerta warning."""
        from app.services.notification_rules import check_mileage_warning

        v = make_vehicle(user.id, vehicle_type.id, mileage=45000, max_mileage=50000)  # 90%
        db.add(v)
        await db.commit()

        result = await check_mileage_warning(db)
        assert len(result) == 1
        assert result[0]["user_id"] == user.id
        assert result[0]["rule_key"] == "mileage_warning"
        import json
        payload = json.loads(result[0]["message"])
        assert payload["percent"] == 90

    async def test_no_genera_alerta_cuando_mileage_es_bajo(self, db, user, vehicle_type):
        """Vehículo al 50% no debe generar alerta."""
        from app.services.notification_rules import check_mileage_warning

        v = make_vehicle(user.id, vehicle_type.id, mileage=25000, max_mileage=50000)  # 50%
        db.add(v)
        await db.commit()

        result = await check_mileage_warning(db)
        assert len(result) == 0

    async def test_no_genera_alerta_cuando_ya_es_critico(self, db, user, vehicle_type):
        """100%+ no debe aparecer como warning (es critical)."""
        from app.services.notification_rules import check_mileage_warning

        v = make_vehicle(user.id, vehicle_type.id, mileage=50000, max_mileage=50000)  # 100%
        db.add(v)
        await db.commit()

        result = await check_mileage_warning(db)
        assert len(result) == 0  # Es critical, no warning

    async def test_no_genera_alerta_si_hay_cooldown_activo(self, db, user, vehicle_type):
        """Con cooldown activo, no debe generar duplicado."""
        from app.services.notification_rules import check_mileage_warning
        from app.models.notification_cooldown import NotificationCooldown

        v = make_vehicle(user.id, vehicle_type.id, mileage=45000, max_mileage=50000)
        db.add(v)
        await db.commit()
        await db.refresh(v)

        # Crear cooldown reciente
        cooldown = NotificationCooldown(
            user_id=user.id,
            vehicle_id=v.id,
            rule_key="mileage_warning",
            last_sent_at=datetime.now(timezone.utc) - timedelta(hours=1),  # hace 1h
        )
        db.add(cooldown)
        await db.commit()

        result = await check_mileage_warning(db)
        assert len(result) == 0  # Cooldown activo, sin duplicado

    async def test_genera_alerta_si_cooldown_esta_expirado(self, db, user, vehicle_type):
        """Con cooldown expirado (>24h), sí debe generar alerta."""
        from app.services.notification_rules import check_mileage_warning
        from app.models.notification_cooldown import NotificationCooldown

        v = make_vehicle(user.id, vehicle_type.id, mileage=45000, max_mileage=50000)
        db.add(v)
        await db.commit()
        await db.refresh(v)

        # Cooldown expirado (hace 25 horas)
        cooldown = NotificationCooldown(
            user_id=user.id,
            vehicle_id=v.id,
            rule_key="mileage_warning",
            last_sent_at=datetime.now(timezone.utc) - timedelta(hours=25),
        )
        db.add(cooldown)
        await db.commit()

        result = await check_mileage_warning(db)
        assert len(result) == 1  # Cooldown expirado, nueva alerta


# ─── Tests: Regla mileage_critical ───────────────────────────

class TestMileageCriticalRule:
    async def test_genera_alerta_error_al_100_pct(self, db, user, vehicle_type):
        from app.services.notification_rules import check_mileage_critical
        from app.models.notification import NotificationType

        v = make_vehicle(user.id, vehicle_type.id, mileage=50000, max_mileage=50000)  # 100%
        db.add(v)
        await db.commit()

        result = await check_mileage_critical(db)
        assert len(result) == 1
        assert result[0]["type"] == NotificationType.ERROR

    async def test_genera_alerta_al_superar_100_pct(self, db, user, vehicle_type):
        from app.services.notification_rules import check_mileage_critical

        v = make_vehicle(user.id, vehicle_type.id, mileage=60000, max_mileage=50000)  # 120%
        db.add(v)
        await db.commit()

        result = await check_mileage_critical(db)
        assert len(result) == 1

    async def test_no_genera_alerta_al_99_pct(self, db, user, vehicle_type):
        from app.services.notification_rules import check_mileage_critical

        v = make_vehicle(user.id, vehicle_type.id, mileage=49999, max_mileage=50000)  # 99.99%
        db.add(v)
        await db.commit()

        result = await check_mileage_critical(db)
        assert len(result) == 0


# ─── Tests: Regla maintenance_overdue ────────────────────────

class TestMaintenanceOverdueRule:
    async def test_genera_alerta_si_mantenimiento_mayor_180_dias(self, db, user, vehicle_type):
        from app.services.notification_rules import check_maintenance_overdue

        v = make_vehicle(user.id, vehicle_type.id, mileage=10000, max_mileage=50000)
        db.add(v)
        await db.commit()
        await db.refresh(v)

        m = make_maintenance(v.id, days_ago=200)  # 200 días = vencido
        db.add(m)
        await db.commit()

        result = await check_maintenance_overdue(db)
        assert len(result) == 1
        # El mensaje incluye los días pasados (puede ser 200 o 201 por zona horaria)
        import json
        payload = json.loads(result[0]["message"])
        assert payload["days"] >= 200

    async def test_no_genera_alerta_si_mantenimiento_reciente(self, db, user, vehicle_type):
        from app.services.notification_rules import check_maintenance_overdue

        v = make_vehicle(user.id, vehicle_type.id, mileage=10000, max_mileage=50000)
        db.add(v)
        await db.commit()
        await db.refresh(v)

        m = make_maintenance(v.id, days_ago=30)  # 30 días = reciente
        db.add(m)
        await db.commit()

        result = await check_maintenance_overdue(db)
        assert len(result) == 0

    async def test_usa_mantenimiento_mas_reciente_como_referencia(self, db, user, vehicle_type):
        """Si el último mantenimiento es reciente, no importa que haya otros viejos."""
        from app.services.notification_rules import check_maintenance_overdue

        v = make_vehicle(user.id, vehicle_type.id, mileage=10000, max_mileage=50000)
        db.add(v)
        await db.commit()
        await db.refresh(v)

        m_viejo = make_maintenance(v.id, days_ago=365)   # Viejo
        m_reciente = make_maintenance(v.id, days_ago=15) # Reciente
        db.add_all([m_viejo, m_reciente])
        await db.commit()

        result = await check_maintenance_overdue(db)
        assert len(result) == 0  # El último es reciente, sin alerta


# ─── Tests: Regla no_maintenance ─────────────────────────────

class TestNoMaintenanceRule:
    async def test_genera_alerta_para_vehiculo_sin_servicio(self, db, user, vehicle_type):
        from app.services.notification_rules import check_no_maintenance

        # Vehículo de 60 días sin mantenimiento
        v = make_vehicle(user.id, vehicle_type.id, mileage=10000, max_mileage=50000, days_old=60)
        db.add(v)
        await db.commit()

        result = await check_no_maintenance(db)
        assert len(result) == 1
        assert result[0]["user_id"] == user.id

    async def test_no_genera_alerta_para_vehiculo_nuevo(self, db, user, vehicle_type):
        """Vehículo de menos de 30 días no debe recibir alerta."""
        from app.services.notification_rules import check_no_maintenance

        v = make_vehicle(user.id, vehicle_type.id, mileage=0, max_mileage=50000, days_old=15)
        db.add(v)
        await db.commit()

        result = await check_no_maintenance(db)
        assert len(result) == 0

    async def test_no_genera_alerta_si_tiene_mantenimiento(self, db, user, vehicle_type):
        """Vehículo con mantenimiento registrado no debe recibir alerta."""
        from app.services.notification_rules import check_no_maintenance

        v = make_vehicle(user.id, vehicle_type.id, mileage=10000, max_mileage=50000, days_old=90)
        db.add(v)
        await db.commit()
        await db.refresh(v)

        m = make_maintenance(v.id, days_ago=45)
        db.add(m)
        await db.commit()

        result = await check_no_maintenance(db)
        assert len(result) == 0


# ─── Tests: run_all_checks (orquestador) ─────────────────────

class TestRunAllChecks:
    async def test_retorna_cero_sin_vehiculos(self, db):
        from app.services.notification_rules import run_all_checks

        count = await run_all_checks(db)
        assert count == 0

    async def test_detecta_multiples_reglas_en_mismo_vehiculo(self, db, user, vehicle_type):
        """Un vehículo puede disparar varias reglas independientes."""
        from app.services.notification_rules import run_all_checks
        from app.models.notification import Notification
        from sqlalchemy import select

        # Vehículo viejo sin mantenimiento, con kilometraje en zona warning
        v = make_vehicle(
            user.id, vehicle_type.id,
            mileage=45000, max_mileage=50000,  # 90% → mileage_warning
            days_old=90,                        # >30 días → no_maintenance
        )
        db.add(v)
        await db.commit()

        count = await run_all_checks(db)
        assert count == 2  # mileage_warning + no_maintenance

        # Verificar que las notificaciones quedaron en BD
        result = await db.execute(select(Notification).where(Notification.user_id == user.id))
        notifs = result.scalars().all()
        assert len(notifs) == 2

    async def test_cada_usuario_recibe_sus_propias_notificaciones(self, db, vehicle_type):
        """Verificar isolación de notificaciones por usuario."""
        from app.services.notification_rules import run_all_checks
        from app.models.notification import Notification
        from app.models.user import User
        from app.core.security import get_password_hash
        from sqlalchemy import select

        # Crear dos usuarios
        u1 = User(email="u1@test.com", hashed_password=get_password_hash("Test1234"), full_name="U1", is_active=True)
        u2 = User(email="u2@test.com", hashed_password=get_password_hash("Test1234"), full_name="U2", is_active=True)
        db.add_all([u1, u2])
        await db.commit()
        await db.refresh(u1)
        await db.refresh(u2)

        # Cada usuario tiene un vehículo con mileage crítico (sin mantenimiento
        # histórico, pero creados hace 5 días para no disparar no_maintenance)
        v1 = make_vehicle(u1.id, vehicle_type.id, mileage=50000, max_mileage=50000, days_old=5)
        v1.plate = "TST-U001"
        v2 = make_vehicle(u2.id, vehicle_type.id, mileage=50000, max_mileage=50000, days_old=5)
        v2.plate = "TST-U002"
        db.add_all([v1, v2])
        await db.commit()

        count = await run_all_checks(db)
        assert count == 2  # mileage_critical × 2 usuarios (1 por usuario)

        # Verificar que cada usuario solo ve sus notificaciones
        n1 = await db.execute(select(Notification).where(Notification.user_id == u1.id))
        n2 = await db.execute(select(Notification).where(Notification.user_id == u2.id))
        assert len(n1.scalars().all()) == 1
        assert len(n2.scalars().all()) == 1

    async def test_no_duplica_en_segunda_ejecucion(self, db, user, vehicle_type):
        """Ejecutar el checker dos veces no debe duplicar notificaciones."""
        from app.services.notification_rules import run_all_checks
        from app.models.notification import Notification
        from sqlalchemy import select

        v = make_vehicle(user.id, vehicle_type.id, mileage=45000, max_mileage=50000, days_old=90)
        db.add(v)
        await db.commit()

        first_run = await run_all_checks(db)
        second_run = await run_all_checks(db)

        assert first_run > 0
        assert second_run == 0  # Bloqueado por cooldown

        result = await db.execute(select(Notification).where(Notification.user_id == user.id))
        assert len(result.scalars().all()) == first_run  # Sin duplicados


# ─── Tests: Purga de cooldowns ────────────────────────────────

class TestPurgeOldCooldowns:
    async def test_elimina_cooldowns_viejos(self, db, user, vehicle_type):
        from app.services.notification_rules import purge_old_cooldowns
        from app.models.notification_cooldown import NotificationCooldown
        from sqlalchemy import select

        v = make_vehicle(user.id, vehicle_type.id, mileage=10000, max_mileage=50000)
        db.add(v)
        await db.commit()
        await db.refresh(v)

        # Cooldown viejo (8 días)
        old_cd = NotificationCooldown(
            user_id=user.id,
            vehicle_id=v.id,
            rule_key="mileage_warning",
            last_sent_at=datetime.now(timezone.utc) - timedelta(days=8),
        )
        # Cooldown reciente (1 día)
        new_cd = NotificationCooldown(
            user_id=user.id,
            vehicle_id=v.id,
            rule_key="no_maintenance",
            last_sent_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        db.add_all([old_cd, new_cd])
        await db.commit()

        purged = await purge_old_cooldowns(db)
        assert purged == 1  # Solo eliminó el viejo

        remaining = await db.execute(select(NotificationCooldown))
        assert len(remaining.scalars().all()) == 1  # El reciente sobrevive

    async def test_no_elimina_nada_si_todos_son_recientes(self, db, user, vehicle_type):
        from app.services.notification_rules import purge_old_cooldowns
        from app.models.notification_cooldown import NotificationCooldown

        v = make_vehicle(user.id, vehicle_type.id, mileage=10000, max_mileage=50000)
        db.add(v)
        await db.commit()
        await db.refresh(v)

        cd = NotificationCooldown(
            user_id=user.id,
            vehicle_id=v.id,
            rule_key="mileage_warning",
            last_sent_at=datetime.now(timezone.utc) - timedelta(hours=2),
        )
        db.add(cd)
        await db.commit()

        purged = await purge_old_cooldowns(db)
        assert purged == 0


# ─── Tests: Scheduler ─────────────────────────────────────────

class TestScheduler:
    async def test_scheduler_se_puede_cancelar(self):
        """El scheduler debe detenerse limpiamente al cancelar el task."""
        from app.services.notification_scheduler import notification_scheduler_loop

        task = asyncio.create_task(notification_scheduler_loop())
        await asyncio.sleep(0.1)  # Darle tiempo de arrancar
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass  # Esperado

        assert task.cancelled()
