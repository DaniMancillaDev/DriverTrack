"""Test de integración real contra la API con el usuario admin.

Flujo completo:
1. Login con admin@admin.com → obtiene JWT
2. Llama POST /notifications/check-now → genera notificaciones automáticas
3. Llama GET /notifications → verifica que aparecen en la lista
4. Llama GET /notifications/unread-count → verifica el badge count
5. Marca todas como leídas → verifica que unread_count vuelve a 0

Usa httpx contra el servidor real en http://localhost:8000.
"""

import httpx
import pytest
import pytest_asyncio

BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "Admin1234"  # Contraseña del seed (actualiza si la cambiaste)


# ─── Fixture de cliente HTTP autenticado ─────────────────────

@pytest_asyncio.fixture
async def auth_token():
    """Hace login y retorna el JWT del admin."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        response = await client.post("/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
        })
        assert response.status_code == 200, (
            f"Login fallido ({response.status_code}): {response.text}\n"
            f"¿La contraseña correcta es '{ADMIN_PASSWORD}'?"
        )
        return response.json()["access_token"]


@pytest_asyncio.fixture
async def client(auth_token):
    """Cliente HTTP con Bearer token ya configurado."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    async with httpx.AsyncClient(base_url=BASE_URL, headers=headers, timeout=15.0) as c:
        yield c


# ─── Tests de integración ─────────────────────────────────────

class TestIntegracionAdmin:

    async def test_01_login_exitoso(self):
        """Verifica que el login retorna un JWT válido."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
            response = await client.post("/auth/login", json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD,
            })

        print(f"\n  → Status: {response.status_code}")
        print(f"  → Response: {response.json()}")

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        print(f"  ✓ JWT obtenido correctamente")

    async def test_02_check_now_genera_notificaciones(self, client):
        """Llama al endpoint check-now y verifica la respuesta."""
        response = await client.post("/notifications/check-now")

        print(f"\n  → Status: {response.status_code}")
        print(f"  → Response: {response.json()}")

        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "message" in data
        assert isinstance(data["count"], int)

        print(f"  ✓ Notificaciones generadas: {data['count']}")
        print(f"  ✓ Mensaje: {data['message']}")

    async def test_03_lista_notificaciones(self, client):
        """Verifica que GET /notifications retorna la lista paginada."""
        response = await client.get("/notifications?skip=0&limit=10")

        print(f"\n  → Status: {response.status_code}")

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "unread_count" in data
        assert "has_more" in data

        print(f"  ✓ Total notificaciones: {data['total']}")
        print(f"  ✓ No leídas: {data['unread_count']}")
        print(f"  ✓ Items en esta página: {len(data['items'])}")

        if data["items"]:
            first = data["items"][0]
            print(f"\n  → Primera notificación:")
            print(f"     Título: {first['title']}")
            print(f"     Mensaje: {first['message']}")
            print(f"     Tipo: {first['type']}")
            print(f"     Leída: {first['is_read']}")

    async def test_04_unread_count(self, client):
        """Verifica el endpoint de conteo de no leídas (alimenta el badge)."""
        response = await client.get("/notifications/unread-count")

        print(f"\n  → Status: {response.status_code}")
        print(f"  → Response: {response.json()}")

        assert response.status_code == 200
        data = response.json()
        assert "unread_count" in data
        assert isinstance(data["unread_count"], int)
        assert data["unread_count"] >= 0

        print(f"  ✓ Badge count actual: {data['unread_count']}")

    async def test_05_marcar_todas_como_leidas(self, client):
        """Verifica que marcar todas como leídas reduce el unread_count a 0."""
        # Antes: obtener conteo actual
        before = await client.get("/notifications/unread-count")
        count_before = before.json()["unread_count"]
        print(f"\n  → No leídas antes: {count_before}")

        # Marcar todas como leídas
        response = await client.patch("/notifications/read-all")
        print(f"  → PATCH /read-all status: {response.status_code}")
        print(f"  → Response: {response.json()}")
        assert response.status_code == 200

        # Después: verificar que bajó a 0
        after = await client.get("/notifications/unread-count")
        count_after = after.json()["unread_count"]
        print(f"  → No leídas después: {count_after}")

        assert count_after == 0
        print(f"  ✓ Todas las notificaciones marcadas como leídas")

    async def test_06_check_now_respeta_cooldown(self, client):
        """Segunda ejecución de check-now no debe duplicar notificaciones."""
        # Primera corrida
        r1 = await client.post("/notifications/check-now")
        count1 = r1.json()["count"]

        # Segunda corrida inmediata (cooldown activo)
        r2 = await client.post("/notifications/check-now")
        count2 = r2.json()["count"]

        print(f"\n  → Primera corrida: {count1} notificaciones")
        print(f"  → Segunda corrida (cooldown): {count2} notificaciones")

        assert r2.status_code == 200
        assert count2 == 0  # El cooldown bloquea las duplicadas
        print(f"  ✓ Anti-duplicación funcionando correctamente")

    async def test_07_acceso_sin_token_es_rechazado(self):
        """Sin JWT, los endpoints protegidos deben retornar 401/403."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
            r1 = await client.get("/notifications")
            r2 = await client.post("/notifications/check-now")
            r3 = await client.get("/notifications/unread-count")

        print(f"\n  → GET /notifications sin token: {r1.status_code}")
        print(f"  → POST /check-now sin token: {r2.status_code}")
        print(f"  → GET /unread-count sin token: {r3.status_code}")

        assert r1.status_code in (401, 403)
        assert r2.status_code in (401, 403)
        assert r3.status_code in (401, 403)
        print(f"  ✓ Endpoints protegidos correctamente")
