"""Application settings loaded from environment variables via Pydantic."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Postgres
    postgres_host: str = Field("localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(5432, env="POSTGRES_PORT")
    postgres_db: str = Field("market_ai", env="POSTGRES_DB")
    postgres_user: str = Field("market_ai", env="POSTGRES_USER")
    postgres_password: str = Field("secret", env="POSTGRES_PASSWORD")

    # Redis
    redis_host: str = Field("localhost", env="REDIS_HOST")
    redis_port: int = Field(6379, env="REDIS_PORT")
    redis_db: int = Field(0, env="REDIS_DB")

    # Storage roots
    data_root: str = Field("/data", env="DATA_ROOT")
    artifact_root: str = Field("/artifacts", env="ARTIFACT_ROOT")

    # Service ports
    dataset_platform_port: int = Field(8001, env="DATASET_PLATFORM_PORT")
    inference_gateway_port: int = Field(8002, env="INFERENCE_GATEWAY_PORT")
    eval_control_plane_port: int = Field(8003, env="EVAL_CONTROL_PLANE_PORT")

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings singleton."""
    return Settings()
