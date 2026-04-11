#!/bin/bash
set -e

echo "⏳ Esperando a que el sistema esté listo..."

echo "🔄 Ejecutando migraciones de base de datos..."
# uv run usa el entorno virtual que empacamos durante el build
uv run alembic upgrade head

echo "🚀 Iniciando DriveTrack API con Uvicorn en el puerto 8010 para evitar conflictos..."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8010
