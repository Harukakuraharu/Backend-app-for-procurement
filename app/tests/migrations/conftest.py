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
    Формирование URL для тестовой БД с localhost
    """
    config.DB_HOST = "localhost"
    return config.dsn


@pytest.fixture(name="postgres")
def postgres_fixture(pg_url: str) -> Iterator[str]:
    """
    На вход принимается pg_url из предыдущей фикстуры с localhost.
    Эти параметры передаем в контекстный менеджер tmp_database,
    возвращаем - новый URL с новым именем для тестовой БД
    """
    with tmp_database(pg_url, db_name="test_db") as tmp_url:
        yield tmp_url


@pytest.fixture(name="postgres_engine")
def postgres_engine_fixture(
    postgres: str,
) -> Iterator[Engine]:
    """
    На вход принимается полностью сформированный тестовый URL
    из предыдущей фикстуры и создается engine
    """
    engine = create_engine(postgres, echo=True)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture(name="alembic_config")
def alembic_config_fixture(postgres: str) -> Config:
    """
    На вход принимаем полностью сформированный тестовый URL
    и передается в функцию, которая преобразовывает alembic 
    как тестовый для тестов с миграциями
    """
    return make_alembic_config(postgres, "app")
