"""Router de clima — proxy seguro a OpenWeatherMap.

Todos los endpoints requieren autenticación.
Retorna el JSON crudo de OWM para que el frontend
pueda parsearlo con su WeatherModel.fromOwmJson() existente.
"""

from fastapi import APIRouter, HTTPException, Query, status

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
    city_name: str,
    _current_user: CurrentUser,
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
