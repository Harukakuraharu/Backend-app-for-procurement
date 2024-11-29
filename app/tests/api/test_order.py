import pytest
from fastapi import status
from httpx import AsyncClient

import models
from tests import factory as fc


pytestmark = pytest.mark.anyio


async def test_create_order_product(
    user_client: AsyncClient, factory, clear_redis  # pylint: disable=W0613
):
    """Create order product for current user"""
    await factory(fc.ShopFactory)
    product = await factory(fc.ProductFactory)
    data = {"quantity": 5, "product_id": product.id}
    response = await user_client.post("/orderlist/", json=data)
    assert response.status_code == status.HTTP_200_OK


async def test_get_orderlist(user_client: AsyncClient, factory):
    """Get orderlist for current user"""
    await factory(fc.ShopFactory)
    product = await factory(fc.ProductFactory)
    data = {"quantity": 5, "product_id": product.id}
    response = await user_client.post("/orderlist/", json=data)
    assert response.status_code == status.HTTP_200_OK
    response = await user_client.get("/orderlist/")
    assert response.status_code == status.HTTP_200_OK


async def test_delete_order_product(user_client: AsyncClient, factory):
    """Delete order product for current user"""
    await factory(fc.ShopFactory)
    product = await factory(fc.ProductFactory)
    data = {"quantity": 5, "product_id": product.id}
    response = await user_client.post("/orderlist/", json=data)

    delete_data = {"quantity": 0, "product_id": product.id}
    response = await user_client.post("/orderlist/", json=delete_data)
    assert response.status_code == status.HTTP_200_OK


async def test_create_order(user_client: AsyncClient, factory):
    """Create order for current user"""
    await factory(fc.UserFactory, status=models.UserStatus.MANAGER)
    await factory(fc.ShopFactory)
    product = await factory(fc.ProductFactory)
    data = {"quantity": 5, "product_id": product.id}
    response = await user_client.post("/orderlist/", json=data)
    assert response.status_code == status.HTTP_200_OK
    address = await factory(fc.UserAddressFactory)
    response = await user_client.post("/order/", json={"address": address.id})
    assert response.status_code == status.HTTP_200_OK


async def test_get_orders(user_client: AsyncClient, factory):
    """Get list of all orders for current user"""
    await factory(fc.ShopFactory)
    await factory(fc.UserFactory, status=models.UserStatus.MANAGER)
    product = await factory(fc.ProductFactory)
    data = {"quantity": 5, "product_id": product.id}
    response = await user_client.post("/orderlist/", json=data)
    assert response.status_code == status.HTTP_200_OK
    address = await factory(fc.UserAddressFactory)
    response = await user_client.post("/order/", json={"address": address.id})
    assert response.status_code == status.HTTP_200_OK
    response = await user_client.get("/order/")
    assert response.status_code == status.HTTP_200_OK


async def test_get_order_id(user_client: AsyncClient, factory):
    """Get order by id for current user"""
    await factory(fc.ShopFactory)
    await factory(fc.UserFactory, status=models.UserStatus.MANAGER)
    product = await factory(fc.ProductFactory)
    data = {"quantity": 5, "product_id": product.id}
    response = await user_client.post("/orderlist/", json=data)
    assert response.status_code == status.HTTP_200_OK
    address = await factory(fc.UserAddressFactory)
    response = await user_client.post("/order/", json={"address": address.id})
    assert response.status_code == status.HTTP_200_OK
    response = await user_client.get("/order/1")
    assert response.status_code == status.HTTP_200_OK
