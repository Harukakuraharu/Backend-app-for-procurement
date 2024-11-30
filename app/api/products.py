import sqlalchemy as sa
from fastapi import Depends
from fastapi.routing import APIRouter

import models
from api import crud, utils
from core import dependency
from schemas import schemas


product_routers = APIRouter(prefix="/product", tags=["Product"])
category_routers = APIRouter(prefix="/category", tags=["Category"])
parametr_routers = APIRouter(
    prefix="/parametr",
    tags=["Parametr"],
    dependencies=[Depends(dependency.get_current_user)],
)


@product_routers.get("/", response_model=list[schemas.ProductsResponse])
async def get_products(session: dependency.AsyncSessionDependency):
    """Просмотр списка всех товаров"""
    products = await crud.get_item(session, models.Product)
    return products


@product_routers.get("/{product_id}", response_model=schemas.ProductsResponse)
async def get_products_by_id(
    session: dependency.AsyncSessionDependency, product_id: int
):
    """Просмотр определенного продукта"""
    product = await crud.get_item_id(session, models.Product, product_id)
    return product


@product_routers.post("/", response_model=schemas.ProductsResponse)
async def create_products(
    session: dependency.AsyncSessionDependency,
    data: schemas.ProductCreate,
    user: dependency.GetCurrentUserDependency,
):
    """Создание товара. Категории и параметры могут быть пустым списком"""
    product_data = data.model_dump()
    shop = await utils.check_current_item(
        session, models.Shop, models.Shop.id, product_data["shop_id"], user.id
    )
    await utils.check_shop_status(shop.active)
    await session.flush()
    categories = product_data.pop("categories")
    parametrs = product_data.pop("parametrs")
    product = await crud.create_item(session, product_data, models.Product)

    if len(categories) >= 1:
        stmt_cat = sa.select(models.Category).where(
            models.Category.id.in_(categories)
        )
        categories_product = await session.scalars(stmt_cat)
        product.categories = categories_product.all()

    if len(parametrs) >= 1:
        for parametr in parametrs:
            parametr["product_id"] = product.id
        stmt_paramert_product = sa.insert(models.ParametrProduct).values(
            parametrs
        )
        await session.execute(stmt_paramert_product)
    await session.commit()
    await session.refresh(product)
    return product


@product_routers.delete("/{product_id}")
async def delete_products(
    session: dependency.AsyncSessionDependency,
    product_id: int,
    user: dependency.GetCurrentUserDependency,
):
    """Удаление товара"""
    product = await crud.get_item_id(session, models.Product, product_id)
    await utils.check_owner_product(user.id, product)
    await crud.delete_item(session, models.Product, product.id)
    return {"status": "Successfully deleted"}


@product_routers.patch(
    "/{product_id}", response_model=schemas.ProductsResponse
)
async def update_product(  # pylint: disable=R0914
    session: dependency.AsyncSessionDependency,
    data: schemas.ProductUpdate,
    product_id: int,
    user: dependency.GetCurrentUserDependency,
):
    """
    Изменение информации о товаре и категорий.
    Если изменять категории, то с новыми категориями
    нужно передавать список существующих категорий,
    при пустом списке или несуществующих id категорий - они обнуляются.
    """
    update_data = data.model_dump(exclude_unset=True)
    product = await crud.get_item_id(session, models.Product, product_id)
    await utils.check_owner_product(user.id, product)
    if update_data.get("categories") is not None:
        categories = update_data.pop("categories")
        stmt_cat = sa.select(models.Category).where(
            models.Category.id.in_(categories)
        )
        categories_product = await session.scalars(stmt_cat)
        product.categories = categories_product.all()
    if update_data:
        update_data["id"] = product_id
        await crud.update_item(session, models.Product, update_data)
    await session.commit()
    await session.refresh(product)
    return product


@product_routers.patch(
    "/parameters/{product_id}", response_model=schemas.ProductsResponse
)
async def update_or_create_product_parametrs(
    session: dependency.AsyncSessionDependency,
    data: schemas.ParametrProductUpdate,
    product_id: int,
    user: dependency.GetCurrentUserDependency,
):
    """
    Обновление параметров для продукты и/или добавление новых параметров
    """
    update_data = data.model_dump(exclude_unset=True)
    product = await crud.get_item_id(session, models.Product, product_id)
    await utils.check_owner_product(user.id, product)
    if update_data.get("parametrs") is not None:
        parametrs = update_data.pop("parametrs")
        for parametr in parametrs:
            parametr_id = parametr["parametr_id"]
            await utils.check_exists(
                session, models.Parametr, models.Parametr.id, parametr_id
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
    "/parameters/{product_id}", response_model=schemas.ProductsResponse
)
async def delete_parametrs_product(
    session: dependency.AsyncSessionDependency,
    data: schemas.ProductParametrsDelete,
    product_id: int,
    user: dependency.GetCurrentUserDependency,
):
    """Удаление параметров у товара"""
    update_data = data.model_dump(exclude_unset=True)
    product = await crud.get_item_id(session, models.Product, product_id)
    await utils.check_owner_product(user.id, product)
    if update_data.get("parametrs"):
        parametrs = update_data.pop("parametrs")
        for parametr in parametrs:
            await crud.delete_item(session, models.ParametrProduct, parametr)
    await session.commit()
    await session.refresh(product)
    return product


@category_routers.post(
    "/",
    response_model=schemas.CategoryCreateResponse,
    dependencies=[Depends(dependency.get_current_user)],
)
async def create_category(
    session: dependency.AsyncSessionDependency, data: schemas.Category
):
    """Создание категории"""
    category_data = data.model_dump()
    category = await crud.create_item(session, category_data, models.Category)
    await session.commit()
    await session.refresh(category)
    return category


@category_routers.get("/", response_model=list[schemas.CategoryResponse])
async def get_categories(session: dependency.AsyncSessionDependency):
    """Просмотр всех категорий"""
    categories = await crud.get_item(session, models.Category)
    return categories


@parametr_routers.post("/", response_model=schemas.ParametrResponse)
async def create_parametr(
    session: dependency.AsyncSessionDependency, data: schemas.Parametr
):
    """Создание параметров"""
    parametr_data = data.model_dump()
    parametr = await crud.create_item(session, parametr_data, models.Parametr)
    await session.commit()
    await session.refresh(parametr)
    return parametr


@parametr_routers.get("/", response_model=list[schemas.ParametrResponse])
async def get_parametrs(session: dependency.AsyncSessionDependency):
    """Просмотр всех параметров"""
    parametr = await crud.get_item(session, models.Parametr)
    return parametr
