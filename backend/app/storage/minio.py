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


def _rewrite_url_for_browser(url: str) -> str:
    """
    Replace the internal Docker hostname in presigned URLs with the
    public endpoint so browsers can reach MinIO directly.

    e.g. http://minio:9000/... → http://localhost:9000/...
    """
    public = settings.minio_public_endpoint.strip()
    if not public:
        return url
    internal = settings.minio_endpoint.strip()
    # Build full internal origin (scheme + host)
    scheme = "https" if settings.minio_use_ssl else "http"
    internal_origin = f"{scheme}://{internal}"
    public_origin = f"{scheme}://{public}"
    return url.replace(internal_origin, public_origin, 1)


def ensure_bucket_exists() -> None:
    if not minio_client.bucket_exists(settings.minio_bucket_name):
        minio_client.make_bucket(settings.minio_bucket_name)


def generate_presigned_upload_url(object_name: str, expiration_hours: int = 1) -> str:
    """
    Generates a presigned URL for uploading a file to MinIO.
    The URL host is rewritten to the public endpoint for browser access.
    """
    ensure_bucket_exists()
    url = minio_client.presigned_put_object(
        bucket_name=settings.minio_bucket_name,
        object_name=object_name,
        expires=timedelta(hours=expiration_hours),
    )
    return _rewrite_url_for_browser(url)


def generate_presigned_download_url(object_name: str, expiration_hours: int = 24) -> str:
    """
    Generates a presigned URL for downloading a file from MinIO.
    The URL host is rewritten to the public endpoint for browser access.
    """
    url = minio_client.presigned_get_object(
        bucket_name=settings.minio_bucket_name,
        object_name=object_name,
        expires=timedelta(hours=expiration_hours),
    )
    return _rewrite_url_for_browser(url)


def remove_object(object_name: str):
    """
    Removes an object from the MinIO bucket.
    """
    minio_client.remove_object(
        bucket_name=settings.minio_bucket_name,
        object_name=object_name,
    )
