import random
import string
import uuid
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncIterator, Iterator
from urllib.parse import urlsplit, urlunsplit

import sqlalchemy as sa
from alembic.config import Config
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import create_async_engine

from core.settings import config as project_config


def make_alembic_config(
    dsn: str, script_location: str | None = None
) -> Config:
    """
    Make alembic config for tests. Создается новый конфиг
    для алембика,
    потому что основной в енв подвязан под основую
    БДб которая будет использоваться в проекте,
    а нам нужна тестовая
    project_config.ROOT_DIR - папка app
    cначала формируем путь до алембик ини
    потом подменяем тестинг на труб, а базовый
    путь до сгенерированного
    потом указываем папку для миграций, т.к. он сам не видит

    """
    alembic_cfg = Config(f"{project_config.ROOT_DIR}/alembic.ini")
    alembic_cfg.set_main_option("is_testing", "True")
    alembic_cfg.set_main_option("sqlalchemy.url", dsn)
    if script_location:
        alembic_cfg.set_main_option(
            "script_location", f"{script_location}:migrations"
        )

    return alembic_cfg


def create_database(
    url: str,
    template: str = "template1",
    encoding: str = "utf8",
) -> None:
    """
    Create database for tests
    Создание БД с урлом, сформированным в контекстном
    менеджере tmp_database
    make_url формирует урл, который поймет алхимия
    урл с постгрес существует всего, т.е. ее создавать
    не нужно
    main_url содержит урл с именем постгрес для подкючения
    к основной(дефолтной) БД, с помощью которой
    создается движок
    на базе этого движка создается тестовая БД

    """
    url_obj = make_url(url)
    main_url = url_obj._replace(database="postgres")
    engine = sa.create_engine(main_url, isolation_level="AUTOCOMMIT")
    with engine.begin() as conn:
        text = (
            f"CREATE DATABASE {url_obj.database} ENCODING '{encoding}'"
            f"TEMPLATE {template};"
        )

        conn.execute(sa.text(text))
    engine.dispose()


def drop_database(url: str) -> None:
    url_obj = make_url(url)
    main_url = url_obj._replace(database="postgres")
    engine = sa.create_engine(main_url, isolation_level="AUTOCOMMIT")
    with engine.begin() as conn:
        text = f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{url_obj.database}'
            AND pid <> pg_backend_pid();
            """
        conn.execute(sa.text(text))
        text = f"DROP DATABASE {url_obj.database}"
        conn.execute(sa.text(text))
    engine.dispose()


async def async_create_database(
    url: str,
    template: str = "template1",
    encoding: str = "utf8",
) -> None:
    """
    Create database for tests
    """
    url_obj = make_url(url)
    main_url = url_obj._replace(database="postgres")
    engine = create_async_engine(main_url, isolation_level="AUTOCOMMIT")
    async with engine.begin() as conn:
        text = (
            f"CREATE DATABASE {url_obj.database} ENCODING '{encoding}'"
            f"TEMPLATE {template};"
        )

        await conn.execute(sa.text(text))
    await engine.dispose()


async def async_drop_database(url: str) -> None:
    url_obj = make_url(url)
    main_url = url_obj._replace(database="postgres")
    engine = create_async_engine(main_url, isolation_level="AUTOCOMMIT")
    async with engine.begin() as conn:
        text = f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{url_obj.database}'
            AND pid <> pg_backend_pid();
            """
        await conn.execute(sa.text(text))
        text = f"DROP DATABASE {url_obj.database}"
        await conn.execute(sa.text(text))
    await engine.dispose()


@contextmanager
def tmp_database(
    str_url: str, db_name: str = "", suffix: str = "", **kwargs
) -> Iterator[str]:
    """Формирование имени для тестовой БД для миграций,
    на вход передали урл для подключения от фикстур"""
    if db_name == "":
        tmp_db_name = "_".join(
            [
                f"{random.choice(string.ascii_lowercase)}{uuid.uuid4().hex}",
                "temp_db",
                suffix,
            ]
        )
    else:
        tmp_db_name = db_name
    tmp_db_url = urlsplit(str_url)
    str_url = urlunsplit(tmp_db_url._replace(path=f"/{tmp_db_name}"))
    create_database(str_url, **kwargs)

    try:
        yield str_url
    finally:
        drop_database(str_url)


@asynccontextmanager
async def async_tmp_database(
    str_url: str, db_name: str = "", suffix: str = "", **kwargs
) -> AsyncIterator[str]:
    if db_name == "":
        tmp_db_name = "_".join(
            [
                f"{random.choice(string.ascii_lowercase)}{uuid.uuid4().hex}",
                "temp_db",
                suffix,
            ]
        )
    else:
        tmp_db_name = db_name
    tmp_db_url = urlsplit(str_url)
    str_url = urlunsplit(tmp_db_url._replace(path=f"/{tmp_db_name}"))
    try:
        await async_create_database(str_url, **kwargs)
    except ProgrammingError:
        await async_drop_database(str_url)
        await async_create_database(str_url, **kwargs)

    try:
        yield str_url
    finally:
        await async_drop_database(str_url)
