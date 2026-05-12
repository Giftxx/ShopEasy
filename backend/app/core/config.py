from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ShopEasy Backend"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./shopeasy_dev.db"

    # Redis settings
    redis_host: str = "localhost"
    redis_port: int = 6379

    # MinIO settings
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket_name: str = "evidence"
    minio_use_ssl: bool = False
    # Public hostname used in presigned URLs returned to the browser.
    # When running in Docker, internal hostname (minio:9000) must be
    # rewritten to the host-accessible address (localhost:9000).
    minio_public_endpoint: str = ""

    # OpenAI settings
    openai_api_key: str = ""

    # Ollama settings (local LLM)
    ollama_base_url: str = "http://host.docker.internal:11434/v1"
    ollama_model: str = "qwen2.5:1.5b"

    # Google OAuth settings
    google_client_id: str = ""

    # Shopify settings
    shopify_api_key: str = ""
    shopify_api_secret: str = ""
    shopify_webhook_secret: str = ""
    shopify_store_url: str = ""

    # Qdrant settings
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333

    # JWT settings
    secret_key: str = "shopeasy-change-in-production-secret-key-2026"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

