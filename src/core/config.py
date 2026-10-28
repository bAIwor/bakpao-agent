"""Konfigurasi aplikasi (pydantic-settings, baca dari environment/.env)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    MODEL_API_KEY: str = ""
    META_API_BASE_URL: str = "https://api.meta.ai/v1"
    DEFAULT_MODEL: str = "muse-spark-1.3"
    EXECUTIVE_MODEL: str = "muse-wonder-1.0"
    IMAGE_MODEL: str = "muse-image-1.0"

    MODAL_WORKSPACE: str = "baiwormyid"

    STORE_NAME: str = "Bakpao.my.id"
    STORE_BASE_URL: str = "http://localhost:8000"
    MERCHANT_QRIS_IMAGE: str = "static/assets/merchant-qris.jpg"
    MERCHANT_QRIS_PAYLOAD_FILE: str = "src/data/merchant_qris.txt"
    QR_MODE: str = "static"
    PORT: int = 8000
    DEBUG: bool = True
    DATA_DIR: str = "data"


@lru_cache
def get_settings() -> Settings:
    return Settings()
