from datetime import timedelta

from fastapi.routing import APIRouter

import models
from api import crud
from core.dependency import AsyncSessionDependency, GetCurrentUserDependency
from core.security import auth, create_access_token, hash_password
from core.settings import config
from schemas import users as schema_user


user_routers = APIRouter(prefix="/user", tags=["User"])


@user_routers.post("/auth/", response_model=schema_user.Token)
async def login(session: AsyncSessionDependency, data: schema_user.UserLogin):
    user = await auth(session, data.email, data.password)

    access_token_expires = timedelta(
        minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return schema_user.Token(access_token=access_token)


@user_routers.get("/me/", response_model=schema_user.UserResponse)
async def read_users_me(
    current_user: GetCurrentUserDependency,
):
    return current_user


@user_routers.get("/", response_model=list[schema_user.UserResponse])
async def get_users(session: AsyncSessionDependency):
    user = await crud.get_item(session, models.User)
    return user


@user_routers.post("/", response_model=schema_user.UserResponse)
async def create_user(
    session: AsyncSessionDependency, data: schema_user.UserCreate
):
    user_data = data.model_dump()
    user_data["password"] = hash_password(user_data["password"])
    user = await crud.create_item(session, user_data, models.User)
    await session.commit()
    await session.refresh(user)
    return user


@user_routers.patch("/{user_id}", response_model=schema_user.UserResponse)
async def update_user(
    session: AsyncSessionDependency, user_id: int, data: schema_user.UserUpdate
):
    update_data = data.model_dump(exclude_unset=True)
    update_data["id"] = user_id
    user = await crud.update_item(session, models.User, update_data)
    await session.commit()
    await session.refresh(user)
    return user


@user_routers.delete("/{user_id}")
async def delete_user(session: AsyncSessionDependency, user_id: int):
    await crud.delete_item(session, models.User, user_id)
    return {"status": "Successfully deleted"}


@user_routers.get("/{user_id}", response_model=schema_user.UserResponse)
async def get_user_by_id(session: AsyncSessionDependency, user_id: int):
    user = await crud.get_item_id(session, models.User, user_id)
    return user
