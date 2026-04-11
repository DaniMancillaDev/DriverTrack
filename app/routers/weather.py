"""Router de clima — proxy seguro a OpenWeatherMap.

Este módulo actúa como un intermediario (proxy) para las peticiones de clima.
Permite que el frontend consulte datos meteorológicos sin necesidad de
almacenar la API Key de OpenWeatherMap, centralizando la seguridad en el backend.
"""

from fastapi import APIRouter, HTTPException, Query, status, Path

from app.core.deps import CurrentUser
from app.services.weather import (
    WeatherServiceError,
    fetch_weather_by_city,
    fetch_weather_by_coords,
)

router = APIRouter(prefix="/weather", tags=["Clima"])


@router.get(
    "/current",
    summary="Clima actual por coordenadas",
    response_description="JSON crudo de OpenWeatherMap (Current Weather)",
)
async def get_current_weather(
    _current_user: CurrentUser,
    lat: float = Query(..., ge=-90, le=90, description="Latitud"),
    lon: float = Query(..., ge=-180, le=180, description="Longitud"),
):
    """Obtiene el clima actual para las coordenadas dadas.

    Actúa como proxy: reenvía la petición a OWM con la API key
    del servidor y devuelve la respuesta sin modificarla.
    """
    try:
        return await fetch_weather_by_coords(lat=lat, lon=lon)
    except WeatherServiceError as exc:
        raise HTTPException(
            status_code=exc.status_code or status.HTTP_502_BAD_GATEWAY,
            detail=exc.message,
        )


@router.get(
    "/city/{city_name}",
    summary="Clima actual por nombre de ciudad",
    response_description="JSON crudo de OpenWeatherMap (Current Weather)",
)
async def get_weather_by_city(
    _current_user: CurrentUser,
    city_name: str = Path(..., min_length=1, max_length=100, pattern=r"^[a-zA-Z\s\-,]+$"),
):
    """Obtiene el clima actual para la ciudad especificada.

    Actúa como proxy: reenvía la petición a OWM con la API key
    del servidor y devuelve la respuesta sin modificarla.
    """
    try:
        return await fetch_weather_by_city(city_name=city_name)
    except WeatherServiceError as exc:
        raise HTTPException(
            status_code=exc.status_code or status.HTTP_502_BAD_GATEWAY,
            detail=exc.message,
        )
