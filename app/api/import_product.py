import sqlalchemy as sa
import yaml
from fastapi import HTTPException, UploadFile, status
from fastapi.routing import APIRouter

import models
from api import crud
from core import dependency


import_routers = APIRouter(prefix="/import_product", tags=["ImportProduct"])


@import_routers.post("/")
async def import_product(
    session: dependency.AsyncSessionDependency,
    file: UploadFile,
    user: dependency.GetCurrentUserDependency,
):
    """Import products from file"""
    if user.status != models.UserStatus.SHOP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Опция доступна только для магазинов",
        )
    contents = await file.read()
    data = yaml.safe_load(contents)
    if not user.shop:
        shop = await crud.create_item(
            session, {"title": data["shop"], "user_id": user.id}, models.Shop
        )
        shop.active = True
        await session.flush()
        user.shop = shop
    shop_id = user.shop.id  # type: ignore[union-attr]
    for product in data["goods"]:
        parameters = product.pop("parameters")
        categories = product.pop("category")
        product["shop_id"] = shop_id
        product_db = await crud.create_item(session, product, models.Product)
        await session.flush()
        for parametr, value in parameters.items():
            parametr_db = await session.scalar(
                sa.select(models.Parametr).where(
                    models.Parametr.name == parametr
                )
            )
            if not parametr_db:
                parametr_db = await crud.create_item(
                    session, {"name": parametr}, models.Parametr
                )
                await session.flush()
            await crud.create_item(
                session,
                {
                    "product_id": product_db.id,
                    "parametr_id": parametr_db.id,  # type: ignore[union-attr]
                    "value": value,
                },
                models.ParametrProduct,
            )
        await session.commit()
        await session.refresh(product_db)

        category_db = await session.scalar(
            sa.select(models.Category).where(
                models.Category.title == categories
            )
        )
        if not category_db:
            category_db = await crud.create_item(
                session, {"title": categories}, models.Category
            )
            await session.flush()
        product_db.categories = [category_db]
    await session.commit()
    return {"status": "file upload"}
