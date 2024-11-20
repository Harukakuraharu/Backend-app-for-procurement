import pytest
import sqlalchemy as sa
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

import models
from tests.factory import ShopFactory


pytestmark = pytest.mark.anyio


async def test_create_shop(user_client: AsyncClient):
    """Create shop with auth user"""
    data = {"title": "Hehe", "url": "www.test.fastapi", "user_id": 1}
    response = await user_client.post("/shop/", json=data)
    assert response.status_code == status.HTTP_200_OK


async def test_create_shop_not_auth(client: AsyncClient):
    """Create shop with not auth user"""
    data = {"title": "Hehe", "url": "www.test.fastapi", "user_id": 5}
    response = await client.post("/shop/", json=data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


# async def test_get_all_shop(factory, client: AsyncClient):
#     """Get list al shop"""
#     users = await factory(UserFactory, 3)
#     for user in users:
#         await factory(ShopFactory, user_id=user.id)
#     response = await client.get("/shop/")
#     assert response.status_code == status.HTTP_200_OK
#     assert len(response.json()) == 3


async def test_get_shop_by_id(
    user_client: AsyncClient,  # pylint: disable=W0613
    factory,
    client: AsyncClient,
):
    """Get shop by id"""
    await factory(ShopFactory)
    response = await client.get("/shop/1")
    assert response.status_code == status.HTTP_200_OK


async def test_get_not_exists_shop(
    client: AsyncClient,
    factory,
    user_client: AsyncClient,  # pylint: disable=W0613
):
    """Get not exists shop"""
    await factory(ShopFactory)
    response = await client.get("/shop/5")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_update_shop(user_client: AsyncClient, factory):
    """Update info field for youself shop"""
    await factory(ShopFactory)
    update_data = {"title": "New title"}
    response = await user_client.patch("/shop/update/", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["title"] == update_data["title"]


async def test_delete_shop(
    user_client: AsyncClient, factory, async_session: AsyncSession
):
    """Delete youself shop"""
    shop = await factory(ShopFactory)
    response = await user_client.delete("/shop/delete/")
    assert response.status_code == status.HTTP_200_OK
    obj = await async_session.scalar(
        sa.select(models.Shop).where(models.Shop.id == shop.id)
    )
    assert obj is None
