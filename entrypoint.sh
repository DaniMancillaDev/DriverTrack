#!/bin/bash
set -e

echo "Esperando a que el sistema esté listo..."

# Crear .env desde .env.example si no existe (útil para primer despliegue)
if [ ! -f .env ]; then
    echo "No se encontro .env — copiando desde .env.example..."
    cp .env.example .env
    echo "AVISO: Revisa y edita .env con tus valores reales antes de continuar."
fi

# Crear archivo SQLite vacío si no existe (evita que Docker cree un directorio)
if [ ! -f drivetrack.db ]; then
    echo "Creando archivo drivetrack.db vacio..."
    touch drivetrack.db
fi

echo "Ejecutando migraciones de base de datos..."
# uv run usa el entorno virtual que empacamos durante el build
uv run alembic upgrade head

echo "Iniciando DriveTrack API con Uvicorn en el puerto 8010..."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8010
