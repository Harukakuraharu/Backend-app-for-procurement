# import json

# import pytest
# from fastapi import status
# from httpx import AsyncClient

# import models
# from core.redis_cli import redis_client
# from tests import factory as fc


# pytestmark = pytest.mark.anyio


# async def test_create_order_product(
#     user_client: AsyncClient, factory, clear_redis  # pylint: disable=W0613
# ):
#     """Create order product for current user"""
#     await factory(fc.ShopFactory)
#     product = await factory(fc.ProductFactory)
#     data = {"quantity": 5, "product_id": product.id}
#     response = await user_client.post("/orderlist/", json=data)
#     assert response.status_code == status.HTTP_200_OK
#     assert redis_client.get(1) is not None


# async def test_create_order_product_not_auth(client: AsyncClient, factory):
#     """Create order product for not auth user"""
#     user = await factory(fc.UserFactory)
#     shop = await factory(fc.ShopFactory, user_id=user.id)
#     product = await factory(fc.ProductFactory, shop_id=shop.id)
#     data = {"quantity": 5, "product_id": product.id}
#     response = await client.post("/orderlist/", json=data)
#     assert response.status_code == status.HTTP_403_FORBIDDEN


# async def test_get_orderlist(
#     user_client: AsyncClient, factory, clear_redis  # pylint: disable=W0613)
# ):
#     """Get orderlist for current user"""
#     await factory(fc.ShopFactory)
#     product = await factory(fc.ProductFactory)
#     data = {"quantity": 5, "product_id": product.id}
#     response = await user_client.post("/orderlist/", json=data)
#     assert response.status_code == status.HTTP_200_OK
#     response = await user_client.get("/orderlist/")
#     assert response.status_code == status.HTTP_200_OK
#     assert response.json()[0] == data
#     assert redis_client.get(1) is not None


# async def test_delete_order_product(user_client: AsyncClient, factory):
#     """Delete order product for current user"""
#     await factory(fc.ShopFactory)
#     product = await factory(fc.ProductFactory)
#     data = {"quantity": 5, "product_id": product.id}
#     response = await user_client.post("/orderlist/", json=data)

#     delete_data = {"quantity": 0, "product_id": product.id}
#     response = await user_client.post("/orderlist/", json=delete_data)
#     assert response.status_code == status.HTTP_200_OK
#     assert response.json() == []


# async def test_update_order_product(
#     user_client: AsyncClient, factory, clear_redis  # pylint: disable=W0613
# ):
#     """Update order product for current user"""
#     await factory(fc.ShopFactory)
#     product = await factory(fc.ProductFactory)
#     data = {"quantity": 5, "product_id": product.id}
#     response = await user_client.post("/orderlist/", json=data)
#     update_data = {"quantity": 5, "product_id": product.id}
#     response = await user_client.post("/orderlist/", json=update_data)
#     assert response.status_code == status.HTTP_200_OK
#     orderlist = json.loads(redis_client.get(1))
#     assert orderlist[0]["product_id"] == data["product_id"]
#     assert orderlist[0]["quantity"] == 10


# async def test_delete_orderlist(user_client: AsyncClient, factory):
#     """Clear orderlist for current user"""
#     await factory(fc.ShopFactory)
#     product = await factory(fc.ProductFactory)
#     data = {"quantity": 5, "product_id": product.id}
#     response = await user_client.post("/orderlist/", json=data)
#     assert response.status_code == status.HTTP_200_OK
#     response = await user_client.delete("/orderlist/")
#     assert response.status_code == status.HTTP_204_NO_CONTENT
#     assert redis_client.get(1) is None


# @pytest.mark.parametrize(
#     "user_status, status_code",
#     [
#         (models.UserStatus.MANAGER, status.HTTP_200_OK),
#         (models.UserStatus.SHOP, status.HTTP_400_BAD_REQUEST),
#         (models.UserStatus.BUYER, status.HTTP_400_BAD_REQUEST),
#     ],
# )
# async def test_create_order(
#     user_client: AsyncClient, factory, user_status, status_code
# ):
#     """Create order for current user when manager i exsist and not"""
#     await factory(fc.UserFactory, status=user_status)
#     await factory(fc.ShopFactory)
#     product = await factory(fc.ProductFactory)
#     data = {"quantity": 2, "product_id": product.id}
#     response = await user_client.post("/orderlist/", json=data)
#     assert response.status_code == status.HTTP_200_OK
#     address = await factory(fc.UserAddressFactory)
#     response = await user_client.post(
#         "/order/", json={"address_id": address.id}
#     )
#     assert response.status_code == status_code


# async def test_create_order_address(user_client: AsyncClient, factory):
#     """Create order for current user with incorrect address"""
#     await factory(fc.UserFactory, status=models.UserStatus.MANAGER)
#     await factory(fc.ShopFactory)
#     product = await factory(fc.ProductFactory)
#     data = {"quantity": 5, "product_id": product.id}
#     response = await user_client.post("/orderlist/", json=data)
#     assert response.status_code == status.HTTP_200_OK
#     await factory(fc.UserAddressFactory)
#     response = await user_client.post("/order/", json={"address_id": 5})
#     assert response.status_code == status.HTTP_404_NOT_FOUND


# async def test_get_orders(user_client: AsyncClient, factory):
#     """Get list of all orders for current user"""
#     await factory(fc.ShopFactory)
#     await factory(fc.UserFactory, status=models.UserStatus.MANAGER)
#     product = await factory(fc.ProductFactory)
#     data = {"quantity": 5, "product_id": product.id}
#     response = await user_client.post("/orderlist/", json=data)
#     assert response.status_code == status.HTTP_200_OK
#     address = await factory(fc.UserAddressFactory)
#     response = await user_client.post(
#         "/order/", json={"address_id": address.id}
#     )
#     assert response.status_code == status.HTTP_200_OK
#     response = await user_client.get("/order/")
#     assert response.status_code == status.HTTP_400_BAD_REQUEST


# async def test_get_order_id(user_client: AsyncClient, factory):
#     """Get order by id for current user"""
#     await factory(fc.ShopFactory)
#     await factory(fc.UserFactory, status=models.UserStatus.MANAGER)
#     product = await factory(fc.ProductFactory)
#     data = {"quantity": 5, "product_id": product.id}
#     response = await user_client.post("/orderlist/", json=data)
#     assert response.status_code == status.HTTP_200_OK
#     address = await factory(fc.UserAddressFactory)
#     response = await user_client.post(
#         "/order/", json={"address_id": address.id}
#     )
#     assert response.status_code == status.HTTP_200_OK
#     response = await user_client.get("/order/1")
#     assert response.status_code == status.HTTP_400_BAD_REQUEST


# async def test_get_youself_order(user_client: AsyncClient, factory):
#     """Get youself order"""
#     fields = ["id", "created_at", "status", "user_id", "orderlist", "address"]
#     await factory(fc.UserFactory, status=models.UserStatus.MANAGER)
#     await factory(fc.ShopFactory)
#     product = await factory(fc.ProductFactory)
#     data = {"quantity": 5, "product_id": product.id}
#     response = await user_client.post("/orderlist/", json=data)
#     assert response.status_code == status.HTTP_200_OK
#     address = await factory(fc.UserAddressFactory)
#     response = await user_client.post(
#         "/order/", json={"address_id": address.id}
#     )
#     response = await user_client.get("/order/me/")
#     assert response.status_code == status.HTTP_200_OK
#     for key in response.json()[0]:
#         assert key in fields
