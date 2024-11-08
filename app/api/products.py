import sqlalchemy as sa
from fastapi import HTTPException, status
from fastapi.routing import APIRouter

import models
from api import crud
from core.dependency import AsyncSessionDependency, GetCurrentUserDependency
from schemas import products as schema_product


product_routers = APIRouter(prefix="/products", tags=["Products"])


@product_routers.get("/", response_model=list[schema_product.ProductResponse])
async def get_products(session: AsyncSessionDependency):
    """Вывод списка всех товаров"""
    products = await crud.get_item(session, models.Product)
    return products


@product_routers.post("/", response_model=schema_product.ProductResponse)
async def create_products(
    session: AsyncSessionDependency,
    data: schema_product.ProductCreate,
    user: GetCurrentUserDependency,
):
    """Создание товара"""
    product_data = data.model_dump()
    if product_data["shop_id"] == user.shop.id:  # type:ignore[attr-defined]
        categories = product_data.pop("categories")
        stmt = sa.select(models.Category).where(
            models.Category.id.in_(categories)
        )
        categories_product = await session.scalars(stmt)
        product = await crud.create_item(session, product_data, models.Product)
        await session.flush()

        product.categories = categories_product.all()
        await session.commit()
        await session.refresh(product)
        return product
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Сначала нужно открыть магазин",
    )


@product_routers.post(
    "/category/", response_model=schema_product.CategoryResponse
)
async def create_category(
    session: AsyncSessionDependency, data: schema_product.Category
):
    """Создание категории"""
    category_data = data.model_dump()
    category = await crud.create_item(session, category_data, models.Category)
    await session.commit()
    await session.refresh(category)
    return category
