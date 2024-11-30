import pytest
import sqlalchemy as sa
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

import models
from tests import factory as fc


pytestmark = pytest.mark.anyio


async def test_get_all_products(
    client: AsyncClient, factory, async_session: AsyncSession
):
    """Get list of all products"""
    count = 3
    users = await factory(fc.UserFactory, count)
    for user in users:
        await async_session.refresh(user)
        shops = await factory(fc.ShopFactory, user_id=user.id)
    for shop in shops:
        await async_session.refresh(shop)
        await factory(fc.ProductFactory, shop_id=shop.id)
    response = await client.get("/product/")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == count


async def test_create_product(factory, user_client: AsyncClient):
    """Create product without categories and parametrs"""
    shop = await factory(fc.ShopFactory)
    data = {
        "name": "Moana",
        "price": 100,
        "remainder": 5,
        "shop_id": shop.id,
        "categories": [],
        "parametrs": [],
    }
    response = await user_client.post("/product/", json=data)
    assert response.status_code == status.HTTP_200_OK


async def test_create_full_products(
    factory, user_client: AsyncClient, async_session: AsyncSession
):
    """Create product with categories and parametrs"""
    shop = await factory(fc.ShopFactory)
    categories = await factory(fc.CategoryFactory)
    parametrs = await factory(fc.ParametrFactory)
    await async_session.refresh(categories)
    await async_session.refresh(parametrs)
    await async_session.refresh(shop)
    data = {
        "name": "New product",
        "price": 10,
        "remainder": 15,
        "categories": [categories.id],
        "parametrs": [{"parametr_id": parametrs.id, "value": "1000"}],
        "shop_id": shop.id,
    }
    response = await user_client.post("/product/", json=data)
    assert response.status_code == status.HTTP_200_OK


async def test_main_update_product(factory, user_client: AsyncClient):
    """Update product without categories and products"""
    shop = await factory(fc.ShopFactory)
    product = await factory(fc.ProductFactory, shop_id=shop.id)
    update_data = {
        "price": 1,
    }
    response = await user_client.patch(
        f"/product/{product.id}", json=update_data
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["price"] == update_data["price"]


async def test_update_product(
    factory, user_client: AsyncClient, async_session: AsyncSession
):
    """Update product with categories and products"""
    await factory(fc.ShopFactory)
    category = await factory(fc.CategoryFactory)
    parametr = await factory(fc.ParametrFactory)
    product = await factory(fc.ProductFactory)
    await async_session.refresh(category)
    await async_session.refresh(parametr)

    assert len(product.categories) == 0
    assert len(product.parametrs) == 0
    update_data = {
        "categories": [category.id],
    }
    response = await user_client.patch(
        f"/product/{product.id}", json=update_data
    )
    assert response.status_code == status.HTTP_200_OK
    assert product.categories is not None
    assert product.parametrs is not None


async def test_delete_products(
    factory, user_client: AsyncClient, async_session: AsyncSession
):
    """Delete product"""
    shop = await factory(fc.ShopFactory)
    product = await factory(fc.ProductFactory, shop_id=shop.id)
    response = await user_client.delete(f"/product/{product.id}")
    assert response.status_code == status.HTTP_200_OK
    obj = await async_session.scalar(
        sa.select(models.Product).where(models.Product.id == product.id)
    )
    assert obj is None


async def test_delete_parametrs_product(
    factory, user_client: AsyncClient, async_session: AsyncSession
):
    """Delete categories or parametrs for product"""
    await factory(fc.ShopFactory)
    parametr = await factory(fc.ParametrFactory)
    product = await factory(fc.ProductFactory)
    await async_session.refresh(parametr)
    update_data = {
        "parametrs": [{"parametr_id": parametr.id, "value": "10"}],
    }
    response = await user_client.patch(
        f"/product/parameters/{product.id}", json=update_data
    )
    assert response.status_code == status.HTTP_200_OK


async def test_get_category(factory, user_client: AsyncClient):
    """Get list all categories"""
    await factory(fc.CategoryFactory, 5)
    response = await user_client.get("/category/")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 5


async def test_create_category_auth(user_client: AsyncClient):
    """Create category by auth user"""
    data = {
        "title": "hophop",
    }
    response = await user_client.post("/category/", json=data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["title"] == data["title"]


async def test_create_category_not_auth(client: AsyncClient):
    """Create category by auth user"""
    data = {
        "title": "hophop",
    }
    response = await client.post("/category/", json=data)
    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_get_parametr_auth(factory, user_client: AsyncClient):
    """Get list all parametr auth user"""
    await factory(fc.ParametrFactory, 5)
    response = await user_client.get("/parametr/")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 5


async def test_get_parametr_not_auth(factory, client: AsyncClient):
    """Get list all parametr not auth user"""
    await factory(fc.ParametrFactory, 5)
    response = await client.get("/parametr/")
    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_create_parametr_auth(user_client: AsyncClient):
    """Create parametr by auth user"""
    data = {
        "name": "Display",
    }
    response = await user_client.post("/parametr/", json=data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == data["name"]


async def test_create_parametr_not_auth(client: AsyncClient):
    """Create parametr by auth user"""
    data = {
        "name": "Display",
    }
    response = await client.post("/parametr/", json=data)
    assert response.status_code == status.HTTP_403_FORBIDDEN
