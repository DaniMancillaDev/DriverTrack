"""Script de setup para el test de integración con datos reales.

Crea vehículos de prueba para el usuario admin con distintas
condiciones que disparan las reglas de notificación:
- Vehículo 1: mileage al 95% → mileage_warning
- Vehículo 2: mileage al 105% → mileage_critical
- Vehículo 3: sin mantenimiento, 90 días de antigüedad → no_maintenance
- Vehículo 4: con mantenimiento de hace 200 días → maintenance_overdue

Luego llama a check-now y muestra las notificaciones generadas.
"""

import asyncio
import httpx

BASE_URL = "http://localhost:8000"
EMAIL = "admin@admin.com"
PASSWORD = "Admin1234"

# Vehículos de prueba con condiciones que disparan cada regla
VEHICLES_TO_CREATE = [
    {
        "brand": "Toyota", "model": "Corolla TEST-WARNING",
        "plate": "TST-W001", "year": 2020,
        "mileage": 47500, "max_mileage": 50000,   # 95% → mileage_warning
        "type_id": 1,
    },
    {
        "brand": "Honda", "model": "Civic TEST-CRITICAL",
        "plate": "TST-C001", "year": 2019,
        "mileage": 55000, "max_mileage": 50000,   # 110% → mileage_critical
        "type_id": 1,
    },
    {
        "brand": "Yamaha", "model": "MT-07 TEST-NOMAINT",
        "plate": "TST-N001", "year": 2021,
        "mileage": 8000, "max_mileage": 60000,    # 13% → no_maintenance
        "type_id": 2,
    },
]


async def setup_and_test():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=15.0) as client:

        # ── 1. Login ──────────────────────────────────────────
        print("\n🔐 Haciendo login...")
        login_resp = await client.post("/auth/login", json={"email": EMAIL, "password": PASSWORD})
        assert login_resp.status_code == 200, f"Login fallido: {login_resp.text}"
        token = login_resp.json()["access_token"]
        user_id = login_resp.json()["user"]["id"]
        client.headers["Authorization"] = f"Bearer {token}"
        print(f"   ✓ Login OK — usuario: {login_resp.json()['user']['full_name']} (id={user_id})")

        # ── 2. Eliminar vehículos de prueba anteriores ────────
        print("\n🧹 Limpiando vehículos de prueba anteriores...")
        vehicles_resp = await client.get("/vehicles/")
        existing = [v for v in vehicles_resp.json() if v["plate"].startswith("TST-")]
        for v in existing:
            await client.delete(f"/vehicles/{v['id']}")
            print(f"   → Eliminado: {v['plate']}")

        # ── 3. Crear vehículos de prueba ──────────────────────
        print("\n🚗 Creando vehículos de prueba...")
        created_vehicles = []
        for vdata in VEHICLES_TO_CREATE:
            payload = {**vdata, "user_id": user_id}  # ← el backend requiere user_id
            resp = await client.post("/vehicles/", json=payload)
            if resp.status_code in (200, 201):
                v = resp.json()
                created_vehicles.append(v)
                pct = int((vdata["mileage"] / vdata["max_mileage"]) * 100)
                print(f"   ✓ {vdata['brand']} {vdata['model']} — {pct}% km — placa: {vdata['plate']}")
            else:
                print(f"   ✗ Falló crear {vdata['plate']}: {resp.status_code} {resp.text}")

        # ── 4. Agregar mantenimiento viejo al vehículo 3 ──────
        if len(created_vehicles) >= 3:
            print("\n🔧 Agregando mantenimiento vencido (200 días atrás)...")
            v3_id = created_vehicles[2]["id"]  # El Yamaha
            from datetime import date, timedelta
            old_date = (date.today() - timedelta(days=200)).isoformat()
            maint_resp = await client.post(f"/vehicles/{v3_id}/maintenance", json={
                "date": old_date,
                "description": "Cambio de aceite",
                "cost": 80.0,
                "mileage": 6000,
                "category": "Oil Change",
            })
            if maint_resp.status_code in (200, 201):
                print(f"   ✓ Mantenimiento del {old_date} registrado")
            else:
                print(f"   ✗ Falló: {maint_resp.status_code} {maint_resp.text}")

        # ── 5. Ejecutar check-now ─────────────────────────────
        print("\n⚡ Ejecutando check-now...")
        check_resp = await client.post("/notifications/check-now")
        assert check_resp.status_code == 200
        count = check_resp.json()["count"]
        print(f"   ✓ {count} notificaciones generadas\n")

        # ── 6. Mostrar notificaciones generadas ───────────────
        print("📬 Notificaciones generadas:")
        notifs_resp = await client.get("/notifications?skip=0&limit=20")
        notifications = notifs_resp.json()["items"]

        type_icons = {"warning": "⚠️ ", "error": "🔴", "info": "ℹ️ ", "success": "✅"}

        for n in notifications:
            icon = type_icons.get(n["type"], "🔔")
            read_label = "  (leída)" if n["is_read"] else "  ← NUEVA"
            print(f"\n   {icon}  [{n['type'].upper()}]{read_label}")
            print(f"      Título:  {n['title']}")
            print(f"      Mensaje: {n['message'][:80]}...")

        print(f"\n📊 Resumen:")
        summary = notifs_resp.json()
        print(f"   Total notificaciones: {summary['total']}")
        print(f"   No leídas (badge):    {summary['unread_count']}")

        # ── 7. Limpiar vehículos de prueba ────────────────────
        print("\n🧹 Limpiando vehículos de prueba...")
        for v in created_vehicles:
            del_resp = await client.delete(f"/vehicles/{v['id']}")
            if del_resp.status_code == 204:
                print(f"   ✓ Eliminado: {v['plate']}")

        print("\n✅ Setup y test completados correctamente\n")


if __name__ == "__main__":
    asyncio.run(setup_and_test())
