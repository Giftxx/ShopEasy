from datetime import timedelta

from minio import Minio

from app.core.config import get_settings


settings = get_settings()

minio_client = Minio(
    settings.minio_endpoint,
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    secure=settings.minio_use_ssl,
)


def ensure_bucket_exists() -> None:
    if not minio_client.bucket_exists(settings.minio_bucket_name):
        minio_client.make_bucket(settings.minio_bucket_name)


def generate_presigned_upload_url(object_name: str, expiration_hours: int = 1) -> str:
    """
    Generates a presigned URL for uploading a file to MinIO.
    """
    ensure_bucket_exists()
    return minio_client.presigned_put_object(
        bucket_name=settings.minio_bucket_name,
        object_name=object_name,
        expires=timedelta(hours=expiration_hours),
    )


def generate_presigned_download_url(object_name: str, expiration_hours: int = 24) -> str:
    """
    Generates a presigned URL for downloading a file from MinIO.
    """
    return minio_client.presigned_get_object(
        bucket_name=settings.minio_bucket_name,
        object_name=object_name,
        expires=timedelta(hours=expiration_hours),
    )


def remove_object(object_name: str):
    """
    Removes an object from the MinIO bucket.
    """
    minio_client.remove_object(
        bucket_name=settings.minio_bucket_name,
        object_name=object_name,
    )
