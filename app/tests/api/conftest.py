from datetime import timedelta
from typing import AsyncIterator, Type

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from core.dependency import get_session
from core.security import create_access_token
from core.settings import config
from main import app
from models import Base
from tests import factory as fc
from tests.utils import async_tmp_database, create_async_engine


@pytest.fixture(scope="package")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="package", name="pg_url")
def pg_url_fixture() -> str:
    """
    Формирование URL для тестовой БД с localhost
    """
    config.DB_HOST = "localhost"
    return config.async_dsn  # type: ignore[return-value]


@pytest.fixture(scope="package", autouse=True, name="postgres_temlate")
async def postgres_temlate_fixture(pg_url: str) -> AsyncIterator[str]:
    """
    Создаем шаблонную БД с миграциями для создания других БД.
    Миграции создаются в run_sync, вызывая metadata.create_all.
    Эта БД создается один раз для всех тестов
    """
    async with async_tmp_database(pg_url, db_name="api_template") as tmp_url:
        engine = create_async_engine(tmp_url)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()
        yield tmp_url


@pytest.fixture(name="postgres")
async def postgres_fixture(postgres_temlate: str) -> AsyncIterator[str]:
    """
    На основе шаблона БД из предыдущей фикстуры, создается тестовая БД,
    где уже есть все миграции
    """
    async with async_tmp_database(
        postgres_temlate, db_name="temp_db", template="api_template"
    ) as tmp_url:
        yield tmp_url


@pytest.fixture(name="postgres_engine")
async def postgres_engine_fixture(postgres: str) -> AsyncIterator[AsyncEngine]:
    """
    Фикстура для создания engine
    """
    engine = create_async_engine(postgres, echo=True)  # type: ignore
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture(name="async_session")
async def async_session_fixture(
    postgres_engine: AsyncEngine,
) -> AsyncIterator[AsyncSession]:
    """
    Создание сессии с подключением к тестовой БД
    """
    async with AsyncSession(postgres_engine) as session:
        yield session


@pytest.fixture(name="test_app")
async def test_app_fixture(
    async_session: AsyncSession,
) -> AsyncIterator[FastAPI]:
    """
    Подмена зависимостей основого приложение на тестовые
    """
    app.dependency_overrides[get_session] = lambda: async_session
    yield app
    app.dependency_overrides = {}


@pytest.fixture(name="client")
async def client_fixture(test_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """
    Создание клиента для отправки запросов без авторизации
    """
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as async_client:
        yield async_client


@pytest.fixture(name="factory")
async def factory_fixture(async_session: AsyncSession):
    async def wrapper(cls: Type[fc.MainFactory], count=1, **kwargs):
        result = await cls(async_session).generate_data(count, **kwargs)
        if len(result) == 1:
            return result[0]
        return result

    return wrapper


# @pytest.fixture(name="product_factory")
# async def product_factory(async_session: AsyncSession, factory):
#     users = await factory(fc.UserFactory, 5)
#     for user in users:
#         await async_session.refresh(user)
#         shops = await factory(fc.ShopFactory, user_id=user.id)
#     for shop in shops:
#         await async_session.refresh(shop)
#         product = await factory(fc.ProductFactory, shop_id=shop.id)
#     return product


@pytest.fixture(name="user_client")
async def user_client_fixture(
    factory, test_app: FastAPI
) -> AsyncIterator[AsyncClient]:
    user = await factory(fc.UserFactory, password="string123")
    # user = users[0]
    access_token_expires = timedelta(
        minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires,
    )
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as async_client:
        yield async_client
