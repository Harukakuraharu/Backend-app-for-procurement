from fastapi.routing import APIRouter

import models
from api.crud import (
    create_item,
    delete_item,
    get_item,
    get_item_id,
    update_item,
)
from core.dependency import AsyncSessionDependency
from core.security import hash_password
from schemas.users import UserCreate, UserResponse, UserUpdate


user_routers = APIRouter(prefix="/user", tags=["User"])


@user_routers.get("/", response_model=list[UserResponse])
async def get_users(session: AsyncSessionDependency):
    user = await get_item(session, models.User)
    return user


@user_routers.post("/", response_model=UserResponse)
async def create_user(session: AsyncSessionDependency, data: UserCreate):
    user_data = data.model_dump()
    user_data["password"] = hash_password(user_data["password"])
    user = await create_item(session, user_data, models.User)
    await session.commit()
    await session.refresh(user)
    return user


@user_routers.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    session: AsyncSessionDependency, user_id: int, data: UserUpdate
):
    update_data = data.model_dump(exclude_unset=True)
    update_data["id"] = user_id
    user = await update_item(session, models.User, update_data)
    await session.commit()
    await session.refresh(user)
    return user


@user_routers.delete("/{user_id}")
async def delete_user(session: AsyncSessionDependency, user_id: int):
    await delete_item(session, models.User, user_id)
    return {"status": "Successfully deleted"}


@user_routers.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(session: AsyncSessionDependency, user_id: int):
    user = await get_item_id(session, models.User, user_id)
    return user
