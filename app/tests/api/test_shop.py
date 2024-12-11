import pytest
import sqlalchemy as sa
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

import models
from tests.factory import ShopFactory, UserFactory


pytestmark = pytest.mark.anyio


async def test_create_shop(user_client: AsyncClient):
    """Create shop with auth user"""
    data = {"title": "Hehe", "url": "www.test.fastapi"}
    response = await user_client.post("/shop/", json=data)
    assert response.status_code == status.HTTP_200_OK
    if response.json().pop("active"):
        assert response.json()["active"] is True
    if response.json().pop("id"):
        assert response.json()["id"] == 1
    response.json().pop("created_at")
    assert all(
        response.json()[key] == data[key]
        for key in data  # pylint: disable=C0206
    )


@pytest.mark.parametrize(
    "user_status, status_code",
    [
        (models.UserStatus.BUYER.value, status.HTTP_400_BAD_REQUEST),
        (models.UserStatus.MANAGER.value, status.HTTP_400_BAD_REQUEST),
        (models.UserStatus.SHOP.value, status.HTTP_200_OK),
    ],
)
async def test_create_shop_not_shop(
    user_client: AsyncClient, user_status, status_code
):
    """Create shop when user status is not shop"""
    response = await user_client.patch(
        "/user/me/", json={"status": user_status}
    )
    response = await user_client.post("/shop/", json={"title": "Shop"})
    assert response.status_code == status_code


async def test_create_shop_not_auth(client: AsyncClient):
    """Create shop with not auth user"""
    data = {"title": "Hehe", "url": "www.test.fastapi", "user_id": 5}
    response = await client.post("/shop/", json=data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize("shop_active, count", [(False, 0), (True, 3)])
async def test_get_all_shop(
    factory,
    client: AsyncClient,
    async_session: AsyncSession,
    shop_active: bool,
    count: int,
):
    """Get list all active shop"""
    users = await factory(UserFactory, 3)
    for user in users:
        await async_session.refresh(user)
        await factory(ShopFactory, user_id=user.id, active=shop_active)
    response = await client.get("/shop/")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == count


async def test_get_shop_by_id(
    user_client: AsyncClient,  # pylint: disable=W0613
    factory,
    client: AsyncClient,
):
    """Get shop by id with not auth user"""
    await factory(ShopFactory)
    response = await client.get("/shop/1")
    assert response.status_code == status.HTTP_200_OK


async def test_get_not_exists_shop(
    client: AsyncClient,
    factory,
    user_client: AsyncClient,  # pylint: disable=W0613
):
    """Get not exists shop with not auth user"""
    await factory(ShopFactory)
    response = await client.get("/shop/5")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_get_youself_shop(user_client: AsyncClient, factory):
    """Get for youself shop"""
    await factory(ShopFactory)
    response = await user_client.get("/shop/me/")
    assert response.status_code == status.HTTP_200_OK


async def test_get_youself_not_exists_shop(user_client: AsyncClient):
    """Get for youself shop if user has not shop"""
    response = await user_client.get("/shop/me/")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_update_shop(user_client: AsyncClient, factory):
    """Update info field for youself shop"""
    await factory(ShopFactory)
    update_data = {"title": "New title"}
    response = await user_client.patch("/shop/me/", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["title"] == update_data["title"]


async def test_delete_shop(
    user_client: AsyncClient, factory, async_session: AsyncSession
):
    """Delete youself shop"""
    shop = await factory(ShopFactory)
    response = await user_client.delete("/shop/me/")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    obj = await async_session.scalar(
        sa.select(models.Shop).where(models.Shop.id == shop.id)
    )
    assert obj is None
