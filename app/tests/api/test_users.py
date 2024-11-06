import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.anyio
async def test_get_users(user_client: AsyncClient):
    response = await user_client.get("/user/")
    assert response.status_code == status.HTTP_200_OK
