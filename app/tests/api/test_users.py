import pytest
import sqlalchemy as sa
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

import models
from tests import factory as fc


pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    "user_status",
    [
        (models.UserStatus.BUYER.value),
        (models.UserStatus.MANAGER.value),
        (models.UserStatus.SHOP.value),
    ],
)
async def test_create_user(client: AsyncClient, user_status):
    """Create user with different status"""
    data = {
        "email": "aabb@ru.ru",
        "password": "qwerty123",
        "name": "Stepan",
        "phone": "",
        "status": user_status,
    }
    response = await client.post("/user/registration/", json=data)
    assert response.status_code == status.HTTP_200_OK
    data.pop("password")
    response.json().pop("id")
    assert all(
        response.json()[key] == data[key]
        for key in data  # pylint: disable=C0206
    )


@pytest.mark.parametrize(
    "password, status_code",
    [
        ("qwerty", status.HTTP_422_UNPROCESSABLE_ENTITY),
        ("qw123", status.HTTP_422_UNPROCESSABLE_ENTITY),
        ("qwerty123", status.HTTP_200_OK),
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
    user = await factory(fc.UserFactory, password=password, active=True)
    data = {
        "email": user.email,
        "password": password,
    }
    response = await client.post("/user/auth/", json=data)
    assert response.status_code == status.HTTP_200_OK


async def test_auth_user_with_invalid_password(client: AsyncClient, factory):
    """Auth with incorrect password"""
    password = "string123"
    user = await factory(fc.UserFactory, password=password, active=True)
    data = {
        "email": user.email,
        "password": "string12345",
    }
    response = await client.post("/user/auth/", json=data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_get_user_id(user_client: AsyncClient, factory):
    """Get user by id"""
    name = "Hehehe"
    user = await factory(fc.UserFactory, name=name)
    await factory(fc.UserFactory, 5)
    response = await user_client.get(f"user/{user[0].id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("name") == name


async def test_get_user_id_not_auth(client: AsyncClient, factory):
    """Get user by id if user not auth"""
    user = await factory(fc.UserFactory, 3)
    response = await client.get(f"user/{user[0].id}")
    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_get_user_id_not_exists(user_client: AsyncClient):
    """Get user by id who nit exists"""
    response = await user_client.get("user/5")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_get_buyer(user_client: AsyncClient, factory):
    """Get all buyer"""
    buyer_count = 10
    await factory(fc.UserFactory, buyer_count, status=models.UserStatus.BUYER)
    response = await user_client.get("/user/buyer/")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == buyer_count
    for user in response.json():
        assert user["status"] == models.UserStatus.BUYER.value


async def test_get_current_user(user_client: AsyncClient):
    """Get info about youself"""
    response = await user_client.get("/user/me/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == 1


async def test_update_info(user_client: AsyncClient):
    """Update info field about youself"""
    update_data = {"name": "Hehehe", "status": models.UserStatus.MANAGER.value}
    response = await user_client.patch("/user/me/", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("name") == update_data["name"]
    assert response.json().get("status") == update_data["status"]


@pytest.mark.parametrize(
    "user_status, status_code",
    [
        (models.UserStatus.BUYER.value, status.HTTP_400_BAD_REQUEST),
        (models.UserStatus.MANAGER.value, status.HTTP_400_BAD_REQUEST),
    ],
)
async def test_update_status(
    user_client: AsyncClient, factory, user_status, status_code
):
    """Update status if user have shop"""
    response = await user_client.patch(
        "/user/me/", json={"status": models.UserStatus.SHOP.value}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == models.UserStatus.SHOP.value
    await factory(fc.ShopFactory)
    response = await user_client.patch(
        "/user/me/", json={"status": user_status}
    )
    assert response.status_code == status_code


async def test_delete_current_user(user_client: AsyncClient):
    """Delete youself"""
    response = await user_client.delete("/user/me/")
    assert response.status_code == status.HTTP_204_NO_CONTENT


async def test_create_address(
    user_client: AsyncClient, async_session: AsyncSession
):
    """Create address for current user"""
    data_1 = {
        "city": "Tula",
        "address": "address, 5",
    }
    data_2 = {
        "city": "Tula",
        "address": "address, 6",
    }
    response = await user_client.post("/user/me/address/", json=data_1)
    assert response.status_code == status.HTTP_200_OK
    response = await user_client.post("/user/me/address/", json=data_2)
    assert response.status_code == status.HTTP_200_OK
    user = await async_session.scalar(
        sa.select(models.User).where(models.User.id == 1)
    )
    assert len(user.addresses) == 2  # type: ignore[union-attr]


async def test_get_address(user_client: AsyncClient, factory):
    """Get address for current user"""
    fields = ["city", "address", "id"]
    await factory(fc.UserAddressFactory)
    response = await user_client.get("/user/me/address/")
    assert response.status_code == status.HTTP_200_OK
    for key in response.json()[0]:
        assert key in fields


async def test_update_address(user_client: AsyncClient, factory):
    """Update address for current user"""
    address = await factory(fc.UserAddressFactory)
    update_data = {"city": "Pskov"}
    response = await user_client.patch(
        f"/user/me/address/{address.id}", json=update_data
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["city"] == update_data["city"]


async def test_delete_address(user_client: AsyncClient, factory):
    """Delete address for current user"""
    address = await factory(fc.UserAddressFactory)
    response = await user_client.delete(f"/user/me/address/{address.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.parametrize(
    "old_password, new_password, status_code",
    [
        ("string123", "string321", status.HTTP_200_OK),
        ("string123", "string", status.HTTP_422_UNPROCESSABLE_ENTITY),
        ("string", "string321", status.HTTP_400_BAD_REQUEST),
    ],
)
async def test_update_password(
    user_client: AsyncClient, old_password: str, new_password: str, status_code
):
    """Update password for user"""
    update_data = {
        "old_password": old_password,
        "password": new_password,
    }
    response = await user_client.patch("/user/me/password/", json=update_data)
    assert response.status_code == status_code


@pytest.mark.parametrize(
    "email, status_code",
    [
        ("test@ru.ru", status.HTTP_200_OK),
        ("qwerty@ru.ru", status.HTTP_404_NOT_FOUND),
    ],
)
async def test_reset_password(
    client: AsyncClient, factory, email, status_code
):
    """Reset password"""
    await factory(fc.UserFactory, email="test@ru.ru")
    response = await client.post(
        "/user/reset_password/", json={"email": email}
    )
    assert response.status_code == status_code
