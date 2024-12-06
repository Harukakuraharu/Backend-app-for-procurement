from pathlib import Path

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings


class Config(BaseSettings):

    ROOT_DIR: Path = Path(__file__).parent.parent.resolve()

    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: str = "user"
    POSTGRES_DB: str = "db"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432

    SECRET_KEY: str = Field(default="")
    ALGORITHM: str = Field(default="")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 100

    REDIS_HOST: str = "localhost"

    CORP_EMAIL: str = Field(default="")
    CORP_HOST: str = Field(default="")
    CORP_PORT: int = Field(default=0)
    CORP_KEY: str = Field(default="")

    BASE_URL: str = Field(default="")

    DEBUG: bool = Field(default=True)

    @computed_field
    def redis_url(self) -> str:
        """Формирование url для redis"""
        return f"redis://{self.REDIS_HOST}:6379/1"

    @computed_field
    def celery_url(self) -> str:
        """Формирование url для redis"""
        return f"redis://{self.REDIS_HOST}:6379/2"

    @computed_field
    def async_dsn(self) -> str:
        """Ссылка для асинхронного подключения к БД"""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.DB_HOST}:"
            f"{self.DB_PORT}/{self.POSTGRES_DB}"
        )

    @computed_field
    def dsn(self) -> str:
        """Ссылка для синхронного подключения к БД, для алембика"""
        return (
            f"postgresql://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.DB_HOST}:"
            f"{self.DB_PORT}/{self.POSTGRES_DB}"
        )


config = Config()
