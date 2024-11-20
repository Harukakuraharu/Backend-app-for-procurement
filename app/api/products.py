import sqlalchemy as sa
from fastapi import Depends, HTTPException, status
from fastapi.routing import APIRouter

import models
from api import crud
from core import dependency
from schemas import products as schema_product


product_routers = APIRouter(prefix="/product", tags=["Product"])
category_routers = APIRouter(prefix="/category", tags=["Category"])
parametr_routers = APIRouter(
    prefix="/parametr",
    tags=["Parametr"],
    dependencies=[Depends(dependency.get_current_user)],
)


@product_routers.get("/", response_model=list[schema_product.ProductsResponse])
async def get_products(session: dependency.AsyncSessionDependency):
    """Вывод списка всех товаров"""
    products = await crud.get_item(session, models.Product)
    return products


@product_routers.post("/", response_model=schema_product.ProductsResponse)
async def create_products(
    session: dependency.AsyncSessionDependency,
    data: schema_product.ProductCreate,
    user: dependency.GetCurrentUserDependency,
):
    """Создание товара"""
    product_data = data.model_dump()
    if product_data["shop_id"] == user.shop.id:  # type: ignore[attr-defined]
        await session.flush()
        categories = product_data.pop("categories")
        parametrs = product_data.pop("parametrs")
        product = await crud.create_item(session, product_data, models.Product)
        if len(categories) > 1:
            stmt_cat = sa.select(models.Category).where(
                models.Category.id.in_(categories)
            )
            categories_product = await session.scalars(stmt_cat)
            product.categories = categories_product.all()
        if len(parametrs) > 1:
            for parametr in parametrs:
                parametr["product_id"] = product.id

            stmt_paramert_product = sa.insert(models.ParametrProduct).values(
                parametrs
            )
            await session.execute(stmt_paramert_product)
        await session.commit()
        await session.refresh(product)
        return product

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Сначала нужно открыть магазин",
    )


@product_routers.delete("/{product_id}")
async def delete_products(
    session: dependency.AsyncSessionDependency,
    product_id: int,
    user: dependency.GetCurrentUserDependency,
):
    """Удаление товара"""
    stmt = sa.select(models.Product).where(models.Product.id == product_id)
    product = await session.scalar(stmt)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product is not exists",
        )
    if product.shop.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="It is not your product",
        )
    await crud.delete_item(session, models.Product, product.id)
    return {"status": "Successfully deleted"}


@product_routers.patch(
    "/{product_id}", response_model=schema_product.ProductsResponse
)
async def update_product(  # pylint: disable=R0914
    session: dependency.AsyncSessionDependency,
    data: schema_product.ProductUpdate,
    product_id: int,
    user: dependency.GetCurrentUserDependency,
):
    """Изменение товара"""
    update_data = data.model_dump(exclude_unset=True)
    product = await crud.get_item_id(session, models.Product, product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product is not exists",
        )
    if product.shop.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="It is not your product",
        )
    if update_data.get("categories"):
        categories = update_data.pop("categories")
        stmt_cat = sa.select(models.Category).where(
            models.Category.id.in_(categories)
        )
        categories_product = await session.scalars(stmt_cat)
        product.categories = categories_product.all()
    if update_data.get("parametrs"):
        parametrs = update_data.pop("parametrs")
        for parametr in parametrs:
            parametr_id = parametr["parametr_id"]
            stmt = sa.select(models.Parametr).where(
                models.Parametr.id == parametr_id
            )
            par_id = await session.scalar(stmt)
            if par_id is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parametr is not exists",
                )
            product_parametrs_id = set(
                parametr.parametr_id for parametr in product.parametrs
            )
            if parametr_id not in product_parametrs_id:
                parametr["product_id"] = product.id
                stmt_paramert_product = sa.insert(
                    models.ParametrProduct
                ).values(parametrs)
                await session.execute(stmt_paramert_product)
            stmt = (
                sa.update(models.ParametrProduct)  # type: ignore[assignment]
                .values(value=parametr["value"])
                .where(
                    (
                        models.ParametrProduct.parametr_id
                        == parametr["parametr_id"]
                    )
                    & (models.ParametrProduct.product_id == product.id)
                )
            )
            await session.execute(stmt)

    if update_data:
        update_data["id"] = product_id
        await crud.update_item(session, models.Product, update_data)
    await session.commit()
    await session.refresh(product)
    return product


@product_routers.delete(
    "parametrs/{product_id}", response_model=schema_product.ProductsResponse
)
async def delete_parametrs_product(
    session: dependency.AsyncSessionDependency,
    data: schema_product.ProductParametrsDelete,
    product_id: int,
    user: dependency.GetCurrentUserDependency,
):
    """Удаление категории и параметров у товара"""
    update_data = data.model_dump(exclude_unset=True)
    stmt = sa.select(models.Product).where(models.Product.id == product_id)
    product = await session.scalar(stmt)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product is not exists",
        )
    if product.shop.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="It is not your product",
        )

    if update_data.get("categories"):
        categories = update_data.pop("categories")
        for category in categories:
            await crud.delete_item(session, models.Category, category)

    if update_data.get("parametrs"):
        parametrs = update_data.pop("parametrs")
        for parametr in parametrs:
            await crud.delete_item(session, models.ParametrProduct, parametr)

    await session.commit()
    await session.refresh(product)
    return product


@category_routers.post(
    "/",
    response_model=schema_product.CategoryCreateResponse,
    dependencies=[Depends(dependency.get_current_user)],
)
async def create_category(
    session: dependency.AsyncSessionDependency, data: schema_product.Category
):
    """Создание категории"""
    category_data = data.model_dump()
    category = await crud.create_item(session, category_data, models.Category)
    await session.commit()
    await session.refresh(category)
    return category


@category_routers.get(
    "/", response_model=list[schema_product.CategoryResponse]
)
async def get_categories(session: dependency.AsyncSessionDependency):
    categories = await crud.get_item(session, models.Category)
    return categories


@parametr_routers.post("/", response_model=schema_product.ParametrResponse)
async def create_parametr(
    session: dependency.AsyncSessionDependency, data: schema_product.Parametr
):
    """Create parametrs fields"""
    parametr_data = data.model_dump()
    parametr = await crud.create_item(session, parametr_data, models.Parametr)
    await session.commit()
    await session.refresh(parametr)
    return parametr


@parametr_routers.get(
    "/", response_model=list[schema_product.ParametrResponse]
)
async def get_parametrs(session: dependency.AsyncSessionDependency):
    categories = await crud.get_item(session, models.Parametr)
    return categories


@parametr_routers.get(
    "/", response_model=list[schema_product.ParametrProductResponse]
)
async def get_parametrs_product(session: dependency.AsyncSessionDependency):
    """Вывод списка всех полей для всех товаров"""
    parametrs = await crud.get_item(session, models.ParametrProduct)
    return parametrs


@parametr_routers.get(
    "/field", response_model=list[schema_product.ParametrResponse]
)
async def get_parametrs_field(session: dependency.AsyncSessionDependency):
    """Вывод списка всех полей для всех товаров"""
    parametrs = await crud.get_item(session, models.Parametr)
    return parametrs
