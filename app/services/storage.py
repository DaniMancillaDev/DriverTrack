"""Servicio de almacenamiento de archivos usando MinIO (S3-compatible).

Provee funciones para generar URLs pre-firmadas para upload/download
de fotos de perfil.
"""

import uuid

import boto3
from botocore.config import Config

from app.core.config import settings


def _get_s3_client():
    """Crea un cliente S3 configurado para MinIO."""
    endpoint_url = (
        f"{'https' if settings.minio_secure else 'http'}://{settings.minio_endpoint}"
    )
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def ensure_bucket_exists() -> None:
    """Crea el bucket si no existe."""
    client = _get_s3_client()
    try:
        client.head_bucket(Bucket=settings.minio_bucket)
    except client.exceptions.ClientError:
        client.create_bucket(Bucket=settings.minio_bucket)


def generate_presigned_upload_url_for_vehicle(
    vehicle_id: int,
    content_type: str = "image/jpeg",
    expires_in: int = 3600,
) -> dict:
    """Genera una URL pre-firmada para subir una foto de vehículo.

    El object_key sigue el patrón: vehicles/{vehicle_id}/{uuid32}.jpg
    que es validado por el regex en el router de vehículos.
    """
    object_key = f"vehicles/{vehicle_id}/{uuid.uuid4().hex}.jpg"
    return generate_presigned_upload_url_for_key(object_key, content_type, expires_in)


def generate_presigned_upload_url_for_key(
    object_key: str,
    content_type: str = "image/jpeg",
    expires_in: int = 3600,
) -> dict:
    """Genera una URL pre-firmada genérica usando un object_key crudo."""
    client = _get_s3_client()

    upload_url = client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.minio_bucket,
            "Key": object_key,
            "ContentType": content_type,
        },
        ExpiresIn=expires_in,
    )

    photo_url = client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.minio_bucket,
            "Key": object_key,
        },
        ExpiresIn=86400 * 7,  # 7 días
    )

    return {
        "upload_url": upload_url,
        "photo_url": photo_url,
        "object_key": object_key,
    }

def generate_presigned_upload_url(
    user_id: int,
    filename: str,
    content_type: str = "image/jpeg",
    expires_in: int = 3600,
) -> dict:
    """Genera una URL pre-firmada para subir una foto de perfil."""
    ext = filename.rsplit(".", 1)[-1] if "." in filename else "jpg"
    object_key = f"avatars/{user_id}/{uuid.uuid4().hex}.{ext}"
    
    return generate_presigned_upload_url_for_key(object_key, content_type, expires_in)


def generate_presigned_get_url(object_key: str, expires_in: int = 86400 * 7) -> str:
    """Genera una URL pre-firmada para acceder a un objeto existente."""
    client = _get_s3_client()
    return client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.minio_bucket,
            "Key": object_key,
        },
        ExpiresIn=expires_in,
    )


def delete_object(object_key: str) -> None:
    """Elimina un objeto del bucket."""
    client = _get_s3_client()
    client.delete_object(Bucket=settings.minio_bucket, Key=object_key)
