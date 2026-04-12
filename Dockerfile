# Usa la imagen base oficial ultra-ligera de Python 3.14
FROM python:3.14-slim

# Evita que Python escriba archivos .pyc y no se congele el output en los logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Instala librerías a nivel de sistema que puedan necesitar algunas de nuestras dependencias (.e.g psycopg2 u otros)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Crea el grupo y usuario de la aplicación asegurando el UID 1000 (tu usuario local).
# Esto previene errores de "Permission denied" al leer/escribir tu base de datos SQLite montada
RUN addgroup --gid 1000 appgroup && adduser --uid 1000 --gid 1000 --disabled-password --gecos "" appuser

# Establece el directorio de trabajo y asegura propiedad desde el inicio
WORKDIR /app
RUN chown appuser:appgroup /app

# Copia `uv` directamente de su imagen oficial
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Nos cambiamos al usuario sin privilegios ANTES de crear el entorno
USER appuser

# Copiamos archivos transfiriendo propiedad
COPY --chown=appuser:appgroup pyproject.toml uv.lock ./

# Sincroniza al nombre del appuser (previene Error 13)
RUN uv sync --frozen --no-dev

# Ahora copiamos el resto transfiriendo permisos nativos
COPY --chown=appuser:appgroup . .

# Hacemos el script de arranque ejecutable
RUN chmod +x /app/entrypoint.sh

# Exponemos el puerto de la API
EXPOSE 8000

# Arrancamos con el script
ENTRYPOINT ["/app/entrypoint.sh"]
