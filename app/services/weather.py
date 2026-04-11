"""Servicio integrador para la API de OpenWeatherMap.

Actúa como un proxy seguro que encapsula la API Key del proveedor en el backend.
Retorna las respuestas originales de OWM para mantener la compatibilidad con
los modelos de datos del frontend.
"""

import httpx

from app.core.config import settings

_OWM_BASE = "https://api.openweathermap.org/data/2.5"
_TIMEOUT = 10.0


async def fetch_weather_by_coords(lat: float, lon: float) -> dict:
    """Obtiene el clima actual por coordenadas geográficas.

    Siempre solicita unidades métricas (°C, m/s).
    Retorna el JSON crudo de OWM tal cual.

    Raises:
        WeatherServiceError: Si OWM responde con error o hay fallo de red.
    """
    params = {
        "lat": lat,
        "lon": lon,
        "appid": settings.openweather_api_key,
        "units": "metric",
    }
    return await _call_owm(params)


async def fetch_weather_by_city(city_name: str) -> dict:
    """Obtiene el clima actual por nombre de ciudad.

    Retorna el JSON crudo de OWM tal cual.

    Raises:
        WeatherServiceError: Si la ciudad no existe o hay error de red.
    """
    params = {
        "q": city_name,
        "appid": settings.openweather_api_key,
        "units": "metric",
    }
    return await _call_owm(params)


async def _call_owm(params: dict) -> dict:
    """Ejecuta la petición HTTP hacia OpenWeatherMap y gestiona errores comunes.

    Nota de Seguridad: Los errores 401 de OWM (clave inválida) se transforman en
    502 Bad Gateway. Esto evita que el cliente confunda un error de configuración
    del servidor con un fallo de su propia sesión de usuario.
    """
    # Guard: si la API key no está configurada, fallar rápido con 502
    api_key = params.get("appid", "")
    if not api_key or api_key.startswith("<"):
        raise WeatherServiceError(
            "Servicio de clima no configurado (API key ausente en el servidor)",
            status_code=502,
        )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_OWM_BASE}/weather", params=params)
    except httpx.RequestError as exc:
        raise WeatherServiceError(f"Error de red al contactar OWM: {exc}")

    if response.status_code == 200:
        return response.json()

    if response.status_code == 401:
        # OWM rechazó la API key — problema de configuración del servidor,
        # no un error de autenticación del usuario. Usar 502.
        raise WeatherServiceError(
            "API key de OpenWeatherMap inválida o expirada (configurar en el servidor)",
            status_code=502,
        )

    if response.status_code == 404:
        raise WeatherServiceError(
            "Ciudad no encontrada en OpenWeatherMap",
            status_code=404,
        )

    raise WeatherServiceError(
        f"Error del servidor OWM: {response.status_code}",
        status_code=response.status_code,
    )


class WeatherServiceError(Exception):
    """Excepción específica para errores del servicio de clima."""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)
