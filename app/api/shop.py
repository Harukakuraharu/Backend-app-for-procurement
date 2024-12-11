from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter

import crud.shops as crud
import models
from api import utils
from core.dependency import AsyncSessionDependency, GetCurrentUserDependency
from schemas import schemas


shop_routers = APIRouter(prefix="/shop", tags=["Shop"])


@shop_routers.post("/", response_model=schemas.ShopCreateResponse)
async def create_shop(
    session: AsyncSessionDependency,
    data: schemas.Shop,
    user: GetCurrentUserDependency,
):
    """Создание магазина"""
    utils.check_user_status(user.status, models.UserStatus.SHOP)
    shop_data = data.model_dump()
    shop_data["user_id"] = user.id
    shop = await crud.ShopCrud(session).create_or_update(shop_data, "create")
    await session.commit()
    await session.refresh(shop)
    return shop


@shop_routers.get("/", response_model=list[schemas.ShopsResponse])
async def get_shops(session: AsyncSessionDependency):
    """Просмотр списка активных магазинов"""
    return await crud.ShopCrud(session).get_shop_active(True)


@shop_routers.get("/{shop_id}", response_model=schemas.ShopResponse)
async def get_shop_by_id(session: AsyncSessionDependency, shop_id: int):
    """Просмотр определенного магазина по id со списком продуктов"""
    return await crud.ShopCrud(session).get_item_id(shop_id)


@shop_routers.get("/me/", response_model=schemas.ShopResponse)
async def get_shop_my(
    user: GetCurrentUserDependency,
):
    """Просмотр своего магазина"""
    utils.check_shop_exists(user)
    return user.shop


@shop_routers.patch("/me/", response_model=schemas.ShopsResponse)
async def update_shop(
    session: AsyncSessionDependency,
    user: GetCurrentUserDependency,
    data: schemas.ShopUpdate,
):
    """Обновление информации о своем магазине"""
    update_data = data.model_dump(exclude_unset=True)
    utils.check_shop_exists(user)
    update_data["id"] = user.shop.id  # type: ignore[union-attr]
    shop = await crud.ShopCrud(session).create_or_update(update_data, "update")
    await session.commit()
    await session.refresh(shop)
    return shop


@shop_routers.delete("/me/")
async def delete_shop(
    session: AsyncSessionDependency,
    user: GetCurrentUserDependency,
):
    """Удаление своего магазина"""
    utils.check_shop_exists(user)
    await crud.ShopCrud(session).delete_item(
        user.shop.id  # type: ignore[union-attr]
    )
    return JSONResponse(
        content="Successfully deleted", status_code=status.HTTP_204_NO_CONTENT
    )
