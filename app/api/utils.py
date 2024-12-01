from typing import Any

import sqlalchemy as sa
from fastapi import HTTPException, status
from sqlalchemy.engine import ScalarResult

import models
from core import dependency


async def check_owner_product(
    user_id: int, product: models.Product
) -> models.Product:
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product is not exists",
        )
    if product.shop.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="It is not your product",
        )
    return product


async def check_current_item(
    session: dependency.AsyncSessionDependency,
    model: models.TypeModel,
    item_in,
    item_out: str | int,
    user_id: int,
) -> models.TypeModel:
    """To check item exists and owner"""
    stmt = sa.select(model).where(item_in == item_out)
    item = await session.scalar(stmt)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{model.__name__} is not exists",
        )
    if item.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{model.__name__} is not yours",
        )
    return item


async def check_owner(
    session: dependency.AsyncSessionDependency,
    model: models.TypeModel,
    user_id: int,
) -> ScalarResult[Any]:
    """To check item owner"""
    stmt = sa.select(model).where(model.user_id == user_id)
    response = await session.scalars(stmt)
    return response


async def check_exists(
    session: dependency.AsyncSessionDependency,
    model: models.TypeModel,
    item_in,
    item_out: str | int,
) -> models.TypeModel:
    """To check item exists"""
    stmt = sa.select(model).where(item_in == item_out)
    item = await session.scalar(stmt)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{model.__name__} is not exists",
        )
    return item


async def check_shop_status(shop_status: bool):
    """To check status of shop"""
    if shop_status is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shop would be active",
        )
    return shop_status


async def check_user_status(user_status: bool):
    """To check status of user"""
    if user_status != models.UserStatus.MANAGER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order can get or update only manager",
        )
    return user_status


async def check_user_shop_status(user_status: bool):
    """To check status of user shop"""
    if user_status != models.UserStatus.SHOP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only shop",
        )
    return user_status
