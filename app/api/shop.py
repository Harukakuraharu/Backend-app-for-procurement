import sqlalchemy as sa
from fastapi import HTTPException, status
from fastapi.routing import APIRouter

import models
from api import crud
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
    if user.status != models.UserStatus.SHOP:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Create shop can only Shop",
        )
    shop_data = data.model_dump()
    shop_data["user_id"] = user.id
    shop = await crud.create_item(session, shop_data, models.Shop)
    await session.commit()
    await session.refresh(shop)
    return shop


@shop_routers.get("/", response_model=list[schemas.ShopsResponse])
async def get_shops(session: AsyncSessionDependency):
    """Get active shop"""
    stmt = sa.select(models.Shop).where(
        models.Shop.active == True  # pylint: disable=C0121
    )
    response = await session.scalars(stmt)
    return response.unique().all()


@shop_routers.get("/{shop_id}", response_model=schemas.ShopResponse)
async def get_shop_by_id(session: AsyncSessionDependency, shop_id: int):
    """Получение определенного магазина по id"""
    shop = await crud.get_item_id(session, models.Shop, shop_id)
    return shop


# если нет своего магазина, нечего обновлять
@shop_routers.patch("/update/", response_model=schemas.ShopsResponse)
async def update_shop(
    session: AsyncSessionDependency,
    user: GetCurrentUserDependency,
    data: schemas.ShopUpdate,
):
    """Обновление информации о своем магазине"""
    update_data = data.model_dump(exclude_unset=True)
    if user.shop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Shop is not exists"
        )
    update_data["id"] = user.shop.id
    shop = await crud.update_item(session, models.Shop, update_data)
    await session.commit()
    await session.refresh(shop)
    return shop


@shop_routers.delete("/delete/")
async def delete_shop(
    session: AsyncSessionDependency,
    user: GetCurrentUserDependency,
):
    """Удаление своего магазина"""
    if user.shop is None:  # type:ignore[attr-defined]
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Shop is not exists"
        )
    await crud.delete_item(
        session, models.Shop, user.shop.id  # type:ignore[attr-defined]
    )
    return {"status": "deleted"}
