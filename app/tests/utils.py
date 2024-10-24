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
    Make alembic config for tests
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
