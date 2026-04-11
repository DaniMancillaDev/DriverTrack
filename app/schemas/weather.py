"""Schemas de validación para el servicio de clima."""

from pydantic import BaseModel, Field


class WeatherCoordsQuery(BaseModel):
    """Parámetros de query para obtener clima por coordenadas."""

    lat: float = Field(..., ge=-90, le=90, description="Latitud (-90 a 90)")
    lon: float = Field(..., ge=-180, le=180, description="Longitud (-180 a 180)")
