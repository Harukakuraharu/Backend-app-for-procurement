from typing import Any

import sqlalchemy as sa
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from core.dependency import AsyncSessionDependency
from models import TypeModel


async def get_item(session: AsyncSessionDependency, model: TypeModel):
    stmt = sa.select(model)
    response = await session.scalars(stmt)
    return response.unique().all()


async def create_item(
    session: AsyncSessionDependency, data: dict[str, Any], model: TypeModel
):
    stmt = sa.insert(model).returning(model).values(**data)
    try:
        response = await session.scalar(stmt)
        await session.flush()
    except IntegrityError as error:
        # pylint: disable=C0301
        if "fk_shoppingcart_product_id_product" in error.orig.args[0]:  # type: ignore[union-attr]
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "Product not exists",
            ) from error
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"{model.__name__} already exists",
        ) from error
    return response


def sync_create_item(session, data: dict[str, Any], model: TypeModel):
    stmt = sa.insert(model).returning(model).values(**data)
    response = session.scalar(stmt)
    # session.flush()
    return response


async def update_item(
    session: AsyncSessionDependency, model: TypeModel, data: dict[str, Any]
):
    item_id = data.pop("id")
    stmt = (
        sa.update(model)
        .values(**data)
        .where(model.id == item_id)
        .returning(model)
    )
    response = await session.scalar(stmt)
    await session.flush()
    return response


async def delete_item(
    session: AsyncSessionDependency, model: TypeModel, item_id: int
):
    stmt = sa.delete(model).where(model.id == item_id)
    await session.execute(stmt)
    await session.commit()


async def get_item_id(
    session: AsyncSessionDependency, model: TypeModel, item_id: int
):
    stmt = sa.select(model).where(model.id == item_id)
    response = await session.scalar(stmt)
    if response is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"{model.__name__} not found"
        )
    return response


def sync_get_item_id(session, model: TypeModel, item_id: int):
    stmt = sa.select(model).where(model.id == item_id)
    response = session.scalar(stmt)
    return response
