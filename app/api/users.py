from datetime import timedelta
from uuid import uuid4

from fastapi import Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter

import crud.users as crud
import models
from core import dependency, security
from core.celery_app import send_email
from core.redis_cli import redis_client
from core.settings import config
from schemas import schemas
from tests.factory import faker


user_routers = APIRouter(
    prefix="/user",
    tags=["User"],
)


@user_routers.post("/registration/", response_model=schemas.UserCreateResponse)
async def create_user(
    session: dependency.AsyncSessionDependency, user_data: schemas.UserCreate
):
    """Регистрация пользователей"""
    verify_path = str(uuid4())
    redis_client.set(verify_path, user_data.email)
    user_data.password = security.hash_password(user_data.password)
    user = await crud.UserCrud(session).create_or_update(
        user_data.model_dump(), "create"
    )
    await session.commit()
    await session.refresh(user)
    send_email.delay(
        {
            "msg": (
                "Чтобы завершить регистрацию, перейдите по ссылке: "
                f"{config.BASE_URL}/user/{verify_path}/"
            ),
            "subject": "Подтверждение регистрации",
            "emails": user.email,
        }
    )
    return user


@user_routers.post("/auth/", response_model=schemas.Token)
async def login(
    session: dependency.AsyncSessionDependency, data: schemas.UserLogin
):
    """Вход пользователя в личный кабинет"""
    user = await security.auth(session, data.email, data.password)
    access_token_expires = timedelta(
        minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return schemas.Token(access_token=access_token)


@user_routers.get(
    "/{user_id}",
    response_model=schemas.UserIdResponse,
    dependencies=[Depends(dependency.get_current_user)],
)
async def get_user_by_id(
    session: dependency.AsyncSessionDependency, user_id: int
):
    """Запрос информации о пользователе через id"""
    return await crud.UserCrud(session).get_item_id(user_id)


@user_routers.get("/me/", response_model=schemas.UserResponse)
async def get_users_me(
    current_user: dependency.GetCurrentUserDependency,
):
    """Вывод информации о самом себе"""
    return current_user


@user_routers.get(
    "/buyer/",
    response_model=list[schemas.UserResponse],
    dependencies=[Depends(dependency.get_current_user)],
)
async def get_buyers(session: dependency.AsyncSessionDependency):
    """Запрос всех зарегестрированных пользователей-покупателей"""
    return await crud.UserCrud(session).get_user_buyer(models.UserStatus.BUYER)


@user_routers.patch("/me/", response_model=schemas.UserResponse)
async def update_user(
    session: dependency.AsyncSessionDependency,
    data: schemas.UserUpdate,
    current_user: dependency.GetCurrentUserDependency,
):
    """Обновление информации о себе"""
    update_data = data.model_dump(exclude_unset=True)
    user_status = update_data.get("status")
    if user_status in (models.UserStatus.BUYER, models.UserStatus.MANAGER):
        if current_user.shop:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have a shop",
            )
    update_data["id"] = current_user.id
    user = await crud.UserCrud(session).create_or_update(update_data, "update")
    await session.commit()
    await session.refresh(user)
    return user


@user_routers.delete("/me/")
async def delete_user(
    session: dependency.AsyncSessionDependency,
    current_user: dependency.GetCurrentUserDependency,
):
    """Удаление пользовательского аккаунта"""
    await crud.UserCrud(session).delete_item(current_user.id)
    return JSONResponse(
        content="Successfully deleted", status_code=status.HTTP_204_NO_CONTENT
    )


@user_routers.post("/me/address/", response_model=schemas.UserAddressResponse)
async def create_user_address(
    session: dependency.AsyncSessionDependency,
    data: schemas.UserAddress,
    current_user: dependency.GetCurrentUserDependency,
):
    """Добавление адресов доставки для пользователей"""
    data_address = data.model_dump(exclude_unset=True)
    data_address["user_id"] = current_user.id
    address = await crud.UserAddressCrud(session).create_item(data_address)
    await session.commit()
    await session.refresh(address)
    return address


@user_routers.get(
    "/me/address/", response_model=list[schemas.UserAddressResponse]
)
async def get_user_address(
    session: dependency.AsyncSessionDependency,
    current_user: dependency.GetCurrentUserDependency,
):
    """Просмотр всех своих адресов доставки"""
    return await crud.UserAddressCrud(session).get_user_items(current_user.id)


@user_routers.patch(
    "/me/address/{address_id}", response_model=schemas.UserAddressResponse
)
async def update_user_address(
    session: dependency.AsyncSessionDependency,
    data: schemas.UserAddressUpdate,
    current_user: dependency.GetCurrentUserDependency,
    address_id: int,
):
    """Обновление своих адресов доставки"""
    update_data = data.model_dump(exclude_unset=True)
    update_data["user_id"] = current_user.id
    update_data["id"] = address_id
    address = await crud.UserAddressCrud(session).update_item(update_data)
    await session.commit()
    await session.refresh(address)
    return address


@user_routers.delete("/me/address/{address_id}")
async def delete_user_address(
    session: dependency.AsyncSessionDependency,
    address_id: int,
    current_user: dependency.GetCurrentUserDependency,
):
    """Удаление адресa"""
    await crud.UserAddressCrud(session).delete_address(
        address_id, current_user.id
    )
    return JSONResponse(
        content="Successfully deleted", status_code=status.HTTP_204_NO_CONTENT
    )


@user_routers.patch("/me/password/")
async def update_user_password(
    session: dependency.AsyncSessionDependency,
    data: schemas.PasswordUpdate,
    current_user: dependency.GetCurrentUserDependency,
):
    """Обновление пароля"""
    update_data = data.model_dump()
    if not security.check_password(
        update_data["old_password"],
        current_user.password,  # type: ignore[attr-defined]
    ):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Incorrect password")
    update_data.pop("old_password")
    update_data["id"] = current_user.id
    update_data["password"] = security.hash_password(update_data["password"])
    await crud.UserCrud(session).update_item(update_data)
    await session.commit()
    return JSONResponse(
        content="Password successfully update", status_code=status.HTTP_200_OK
    )


@user_routers.post("/reset_password/")
async def reser_password(
    session: dependency.AsyncSessionDependency,
    data: schemas.PasswordReset,
):
    """Восстановление пароля через почту"""
    update_data = data.model_dump()
    user = await crud.UserCrud(session).get_user(update_data["email"])
    update_data["id"] = user.id
    new_password = faker.password()
    update_data["password"] = security.hash_password(new_password)
    user = await crud.UserCrud(session).update_item(update_data)
    msg = (
        f"Новый пароль для пользователя {user.email}: "
        f"{new_password} \nОбязательно поменяйте пароль в личном кабинете."
    )
    celery_data = {
        "emails": user.email,
        "msg": msg,
        "subject": "Новый пароль",
    }
    await session.commit()
    send_email.delay(celery_data)
    return JSONResponse(content="Send email", status_code=status.HTTP_200_OK)


@user_routers.get("/{verify_path}/")
async def verify_email(
    verify_path: str,
    session: dependency.AsyncSessionDependency,
):
    """Подтверждение почты"""
    if not redis_client.get(verify_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="URL not found",
        )
    email = redis_client.get(verify_path)
    user = await crud.UserCrud(session).get_user(email.decode())
    user.active = True
    await session.commit()
    redis_client.delete(verify_path)
    return JSONResponse(
        content="Successfully verify", status_code=status.HTTP_200_OK
    )
