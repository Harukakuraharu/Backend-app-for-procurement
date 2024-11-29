import pytest
from fastapi import status
from httpx import AsyncClient

import models
from tests.factory import UserAddressFactory, UserFactory


pytestmark = pytest.mark.anyio


async def test_create_user(client: AsyncClient):
    """Create user"""
    data = {
        "email": "aabb@ru.ru",
        "password": "qwerty123",
        "name": "Stepan",
        "phone": "",
        "status": "Покупатель",
    }
    response = await client.post("/user/registration/", json=data)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    "password, status_code",
    [
        ("qwerty", status.HTTP_422_UNPROCESSABLE_ENTITY),
        ("qw123", status.HTTP_422_UNPROCESSABLE_ENTITY),
    ],
)
async def test_create_user_incorrect_password(
    client: AsyncClient, password: str, status_code
):
    """Create user with invalid password"""
    data = {
        "email": "aabb@ru.ru",
        "password": password,
        "name": "",
        "phone": "",
        "status": "Покупатель",
    }
    response = await client.post("/user/registration/", json=data)
    assert response.status_code == status_code


async def test_auth_user(client: AsyncClient, factory):
    """Auth user"""
    password = "string123"
    user = await factory(UserFactory, password=password)
    data = {
        "email": user.email,
        "password": password,
    }
    response = await client.post("/user/auth", json=data)
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()


async def test_auth_user_with_invalid_password(client: AsyncClient, factory):
    """Auth with incorrect password"""
    password = "string123"
    user = await factory(UserFactory, password=password)
    data = {
        "email": user.email,
        "password": "string12345",
    }
    response = await client.post("/user/auth", json=data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_get_users(user_client: AsyncClient, factory):
    """Get all buyer"""
    buyer_count = 10
    await factory(UserFactory, buyer_count, status=models.UserStatus.BUYER)
    response = await user_client.get("/user/buyer/")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == buyer_count


async def test_get_current_user(user_client: AsyncClient):
    """Info about youself"""
    response = await user_client.get("/user/me/")
    assert response.status_code == status.HTTP_200_OK


async def test_update_info(user_client: AsyncClient):
    """Update info field about youself"""
    update_data = {"name": "Hehehe"}
    response = await user_client.patch("/user/me/", json=update_data)
    assert response.status_code == status.HTTP_200_OK


async def test_delete_current_user(user_client: AsyncClient):
    """Delete youself"""
    response = await user_client.delete("/user/me/")
    assert response.status_code == status.HTTP_200_OK


async def test_get_user_id_not_exist(client: AsyncClient):
    """Get not exists user"""
    response = await client.get("user/5")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_get_user_id(client: AsyncClient, factory):
    """Get user by id"""
    name = "Hehehe"
    user = await factory(UserFactory, name=name)
    await factory(UserFactory, 5)
    response = await client.get(f"user/{user.id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("name") == name


async def test_create_address(user_client: AsyncClient):
    """Create address for current user"""
    data_1 = {
        "city": "Tula",
        "address": "address, 5",
    }
    data_2 = {
        "city": "Tula",
        "address": "address, 6",
    }
    response = await user_client.post("user/me/address", json=data_1)
    assert response.status_code == status.HTTP_200_OK
    response = await user_client.post("user/me/address", json=data_2)
    assert response.status_code == status.HTTP_200_OK


async def test_update_address(user_client: AsyncClient, factory):
    """Update address for current user"""
    address = await factory(UserAddressFactory)
    update_data = {"city": "Pskov"}
    response = await user_client.patch(
        f"user/me/address/{address.id}", json=update_data
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["city"] == update_data["city"]


async def test_delete_address(user_client: AsyncClient, factory):
    """Delete address for current user"""
    address = await factory(UserAddressFactory)
    response = await user_client.delete(f"user/me/address/{address.id}")
    assert response.status_code == status.HTTP_200_OK
