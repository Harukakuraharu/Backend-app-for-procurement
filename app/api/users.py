from datetime import timedelta

import sqlalchemy as sa
from fastapi import Depends
from fastapi.routing import APIRouter

import models
from api import crud
from core.dependency import (
    AsyncSessionDependency,
    GetCurrentUserDependency,
    get_current_user,
)
from core.security import auth, create_access_token, hash_password
from core.settings import config
from schemas import products as schema


user_routers = APIRouter(prefix="/user", tags=["User"])


@user_routers.post("/registration/", response_model=schema.UserCreateResponse)
async def create_user(
    session: AsyncSessionDependency, data: schema.UserCreate
):
    """Регистрация пользователей"""
    user_data = data.model_dump()
    user_data["password"] = hash_password(user_data["password"])
    user = await crud.create_item(session, user_data, models.User)
    await session.commit()
    await session.refresh(user)
    return user


@user_routers.post("/auth", response_model=schema.Token)
async def login(session: AsyncSessionDependency, data: schema.UserLogin):
    """Вход пользователя в личный кабинет"""
    user = await auth(session, data.email, data.password)

    access_token_expires = timedelta(
        minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return schema.Token(access_token=access_token)


@user_routers.get("/me/", response_model=schema.UserResponse)
async def read_users_me(
    current_user: GetCurrentUserDependency,
):
    """Вывод информации о самом себе"""
    return current_user


@user_routers.get(
    "/buyer/",
    response_model=list[schema.UserResponse],
    dependencies=[Depends(get_current_user)],
)
async def get_buyers(session: AsyncSessionDependency):
    """Запрос всех зарегестрированных пользователей-покупателей"""
    stmt = sa.select(models.User).where(
        models.User.status == models.UserStatus.BUYER
    )
    result = await session.scalars(stmt)
    return result.unique().all()


@user_routers.patch("/me/", response_model=schema.UserResponse)
async def update_user(
    session: AsyncSessionDependency,
    data: schema.UserUpdate,
    current_user: GetCurrentUserDependency,
):
    """Обновление информации о себе"""
    update_data = data.model_dump(exclude_unset=True)
    update_data["id"] = current_user.id
    user = await crud.update_item(session, models.User, update_data)
    await session.commit()
    await session.refresh(user)
    return user


@user_routers.delete("/me/")
async def delete_user(
    session: AsyncSessionDependency, current_user: GetCurrentUserDependency
):
    """Удаление пользователя"""
    await crud.delete_item(session, models.User, current_user.id)
    return {"status": "Successfully deleted"}


@user_routers.get("/{user_id}", response_model=schema.UserResponse)
async def get_user_by_id(session: AsyncSessionDependency, user_id: int):
    """Запрос информации о пользователе через id"""
    user = await crud.get_item_id(session, models.User, user_id)
    return user
