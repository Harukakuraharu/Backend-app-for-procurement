from typing import Iterator

import pytest
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from core.settings import config
from tests.utils import make_alembic_config, tmp_database


@pytest.fixture(scope="package", name="pg_url")
def pg_url_fixture() -> str:
    """
    Provides base PostgreSQL URL for creating temporary databases.
    """
    config.DB_HOST = "localhost"
    return config.dsn


@pytest.fixture(name="postgres")
def postgres_fixture(pg_url: str) -> Iterator[str]:
    """
    Creates empty temporary database.
    """
    with tmp_database(pg_url, suffix="migrations") as tmp_url:
        yield tmp_url


@pytest.fixture(name="postgres_engine")
def postgres_engine_fixture(
    postgres: str,
) -> Iterator[Engine]:
    """
    SQLAlchemy engine, bound to temporary database.
    """
    engine = create_engine(postgres, echo=True)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture(name="alembic_config")
def alembic_config_fixture(postgres: str) -> Config:
    """
    Alembic configuration object, bound to temporary database.
    """
    return make_alembic_config(postgres, "app")
