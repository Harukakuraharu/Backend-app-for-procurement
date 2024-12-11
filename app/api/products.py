from fastapi import Depends, status
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter

import crud.products as crud
import models
from api import utils
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
    return await crud.ProductCrud(session).get_items()


@product_routers.get("/{product_id}", response_model=schemas.ProductsResponse)
async def get_products_by_id(
    session: dependency.AsyncSessionDependency, product_id: int
):
    """Просмотр определенного продукта"""
    return await crud.ProductCrud(session).get_item_id(product_id)


@product_routers.post("/", response_model=schemas.ProductsResponse)
async def create_products(
    session: dependency.AsyncSessionDependency,
    data: schemas.ProductCreate,
    user: dependency.GetCurrentUserDependency,
):
    """Создание товара. Категории и параметры могут быть пустым списком"""
    utils.check_user_status(user.status, models.UserStatus.SHOP)
    utils.check_shop_exists(user)
    product_data = data.model_dump()
    product_data["shop_id"] = user.shop.id  # type: ignore[union-attr]
    utils.check_shop_status(user.shop.active)  # type: ignore[union-attr]
    categories = product_data.pop("categories")
    parametrs = product_data.pop("parametrs")
    product = await crud.ProductCrud(session).create_item(product_data)
    await session.flush()
    if len(categories) >= 1:
        product.categories = await crud.CategoryCrud(session).get_category(
            categories
        )

    if len(parametrs) >= 1:
        for parametr in parametrs:
            parametr["product_id"] = product.id
        await crud.ParametrProductCrud(session).create_parametr_product(
            parametrs
        )
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
    product_crud = crud.ProductCrud(session)
    product = await product_crud.get_item_id(product_id)
    utils.check_owner_product(user.id, product)
    await product_crud.delete_item(product_id)
    return JSONResponse(
        content="Successfully deleted", status_code=status.HTTP_204_NO_CONTENT
    )


@product_routers.patch(
    "/{product_id}", response_model=schemas.ProductsResponse
)
async def update_product(
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
    product_crud = crud.ProductCrud(session)
    product = await product_crud.get_item_id(product_id)
    utils.check_owner_product(user.id, product)
    if update_data.get("categories") is not None:
        categories = update_data.pop("categories")
        product.categories = await crud.CategoryCrud(session).get_category(
            categories
        )
    if update_data:
        update_data["id"] = product_id
        await product_crud.update_item(update_data)
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
    Обновление параметров для продуктов и/или добавление новых параметров
    """
    parametrs = data.model_dump()["parametrs"]
    product = await crud.ProductCrud(session).get_item_id(product_id)
    utils.check_owner_product(user.id, product)
    parametrs_id_request = set(
        parametr["parametr_id"] for parametr in parametrs
    )
    parametrs_id_not = parametrs_id_request.difference(
        set(parametr.parametr_id for parametr in product.parametrs)
    )
    parametrs_create = [
        parametr
        for parametr in parametrs
        if parametr["parametr_id"] in parametrs_id_not
    ]
    if len(parametrs_create) > 0:
        for parametr in parametrs_create:
            await crud.ParametrCrud(session).get_item_id(
                parametr["parametr_id"]
            )
            parametr["product_id"] = product.id
        await crud.ParametrProductCrud(session).create_parametr_product(
            parametrs_create
        )
    parametrs_update = [
        parametr
        for parametr in parametrs
        if parametr["parametr_id"] not in parametrs_id_not
    ]
    if len(parametrs_update) > 0:
        for parametr in parametrs_update:
            await crud.ParametrProductCrud(session).update_parametr_product(
                parametr, product.id
            )
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
    parametrs = data.parametrs
    product = await crud.ProductCrud(session).get_item_id(product_id)
    utils.check_owner_product(user.id, product)
    for parametr in parametrs:
        await crud.ParametrProductCrud(session).delete_item(parametr)
    await session.commit()
    await session.refresh(product)
    return product


@category_routers.post("/", response_model=schemas.CategoryCreateResponse)
async def create_category(
    session: dependency.AsyncSessionDependency,
    data: schemas.Category,
    user: dependency.GetCurrentUserDependency,
):
    """Создание категории"""
    utils.check_user_status(user.status, models.UserStatus.SHOP)
    category = await crud.CategoryCrud(session).create_or_update(
        data.model_dump(), "create"
    )
    await session.commit()
    await session.refresh(category)
    return category


@category_routers.get("/", response_model=list[schemas.CategoryCreateResponse])
async def get_categories(session: dependency.AsyncSessionDependency):
    """Просмотр всех категорий"""
    return await crud.CategoryCrud(session).get_items()


@parametr_routers.post("/", response_model=schemas.ParametrResponse)
async def create_parametr(
    session: dependency.AsyncSessionDependency,
    data: schemas.Parametr,
    user: dependency.GetCurrentUserDependency,
):
    """Создание параметров"""
    utils.check_user_status(user.status, models.UserStatus.SHOP)
    parametr = await crud.ParametrCrud(session).create_or_update(
        data.model_dump(), "create"
    )
    await session.commit()
    await session.refresh(parametr)
    return parametr


@parametr_routers.get(
    "/",
    response_model=list[schemas.ParametrResponse],
    dependencies=[Depends(dependency.get_current_user)],
)
async def get_parametrs(session: dependency.AsyncSessionDependency):
    """Просмотр всех параметров"""
    return await crud.ParametrCrud(session).get_items()
