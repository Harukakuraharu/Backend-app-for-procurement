import json

import sqlalchemy as sa
from fastapi import Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter

import crud.orders as crud
import models
from api import utils
from core import dependency
from core.celery_app import send_email
from core.redis_cli import redis_client
from crud.products import ProductCrud
from crud.users import UserAddressCrud, UserCrud
from schemas import schemas


order_routers = APIRouter(
    prefix="/order",
    tags=["Order"],
    dependencies=[Depends(dependency.get_current_user)],
)
orderlist_routers = APIRouter(prefix="/orderlist", tags=["Orderlist"])


@orderlist_routers.post("/", response_model=list[schemas.OrderProductResponse])
async def create_orderlist(
    session: dependency.AsyncSessionDependency,
    data: schemas.OrderProduct,
    user: dependency.GetCurrentUserDependency,
):
    """Создание корзины"""
    order_product = data.model_dump()
    product = await ProductCrud(session).get_item_id(
        order_product["product_id"]
    )
    utils.check_shop_status(product.shop.active)
    if product.remainder < order_product["quantity"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product quantity exceeded",
        )
    if redis_client.get(user.id):
        order_list = json.loads(redis_client.get(user.id))
        prod_ind = None
        for ind, order in enumerate(order_list):
            if order["product_id"] == order_product["product_id"]:
                prod_ind = ind
                break
        if prod_ind is not None:
            if order_product["quantity"] != 0:
                order_list[prod_ind]["quantity"] += order_product["quantity"]
            else:
                order_list.pop(prod_ind)
        else:
            order_list.append(order_product)

        if len(order_list) == 0:
            redis_client.delete(user.id)
        else:
            redis_client.set(user.id, json.dumps(order_list))
        return order_list
    order_list = [order_product]
    redis_client.set(user.id, json.dumps(order_list))
    return order_list


@orderlist_routers.get("/", response_model=list[schemas.OrderProductResponse])
async def get_orderlist(user: dependency.GetCurrentUserDependency):
    """Просмотр корзины"""
    utils.check_orderlist(user.id)
    orderlist = json.loads(redis_client.get(user.id))
    return orderlist


@orderlist_routers.delete("/")
async def clear_orderlist(user: dependency.GetCurrentUserDependency):
    """Очистка корзины"""
    redis_client.delete(user.id)
    return JSONResponse(
        content="Successfully deleted", status_code=status.HTTP_204_NO_CONTENT
    )


@order_routers.post("/", response_model=schemas.OrderResponse)
async def create_order(  # pylint: disable=R0914
    session: dependency.AsyncSessionDependency,
    user: dependency.GetCurrentUserDependency,
    data: schemas.OrderCreate,
):
    """Создание заказа"""
    utils.check_orderlist(user.id)
    email = await UserCrud(session).get_manager_emails()
    if len(email) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error. Shop do not have a manager",
        )
    address = await UserAddressCrud(session).check_owner(
        data.address_id, user.id
    )
    products = json.loads(redis_client.get(user.id))
    order = await crud.OrderCrud(session).create_item(
        {
            "user_id": user.id,
            "status": models.OrderStatus.INPROGRES,
            "address_id": address.id,
        }
    )
    await session.flush()
    for product in products:
        product["order_id"] = order.id
    await crud.OrderlistCrud(session).create_orderlist(products)
    await session.commit()
    await session.refresh(order)
    order_list = [str(orderlist.product) for orderlist in order.orderlist]
    msg = (
        f"Создан новый заказ номер {order.id}\n"
        f"Детали заказа: \n{"\n".join(order_list)}\n"
        f"id заказчика {order.user_id}.\nАдрес доставки: "
        f"город {address.city}, адрес {address.address}"
    )

    celery_data = {
        "emails": email,
        "msg": msg,
        "subject": "Новый заказ",
    }
    send_email.delay(celery_data)
    redis_client.delete(user.id)
    order_dict = {
        orderlist.product_id: orderlist.quantity
        for orderlist in order.orderlist
    }
    stmt = sa.select(models.Product).where(
        models.Product.id.in_(set(product_id for product_id in order_dict))
    )
    products = await session.scalars(stmt)
    for product in products.unique().all():
        quantity = order_dict[product.id]
        product.remainder -= quantity
        if product.remainder < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product quantity exceeded",
            )
    await session.commit()
    await session.refresh(order)
    return order


@order_routers.get("/", response_model=list[schemas.OrderResponse])
async def get_orders(
    session: dependency.AsyncSessionDependency,
    user: dependency.GetCurrentUserDependency,
    order_status: models.OrderStatus | None = None,
):
    """Просмотр всех заказов для менеджеров"""
    utils.check_user_status(user.status, models.UserStatus.MANAGER)
    if order_status is not None:
        return crud.OrderCrud(session).get_order_status(order_status)
    orders = await crud.OrderCrud(session).get_items()
    return orders


@order_routers.get("/{order_id}", response_model=schemas.OrderResponse)
async def get_orders_by_id(
    session: dependency.AsyncSessionDependency,
    order_id: int,
    user: dependency.GetCurrentUserDependency,
):
    """Просмотр определенного заказа"""
    utils.check_user_status(user.status, models.UserStatus.MANAGER)
    order = await crud.OrderCrud(session).get_item_id(order_id)
    return order


@order_routers.get("/me/", response_model=list[schemas.OrderResponse])
async def get_orders_youself(
    session: dependency.AsyncSessionDependency,
    user: dependency.GetCurrentUserDependency,
):
    """Просмотр своих заказов"""
    return await crud.OrderCrud(session).get_user_items(user.id)


@order_routers.delete("/me/{order_id}")
async def cancel_order(
    session: dependency.AsyncSessionDependency,
    user: dependency.GetCurrentUserDependency,
    order_id: int,
):
    """Отмена своего заказа"""
    order = await crud.OrderCrud(session).check_owner(order_id, user.id)
    if order.status in (models.OrderStatus.SENT, models.OrderStatus.DELIVERED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can not cancel order",
        )
    emails = await UserCrud(session).get_manager_emails()
    if len(emails) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error. Shop do not have a manager",
        )
    order.status = models.OrderStatus.CANCELED
    celery_data = {
        "emails": emails,
        "msg": f"Заказ номер {order.id} отменен пользователем",
        "subject": "Отмена заказа",
    }
    send_email.delay(celery_data)
    await session.commit()
    return JSONResponse(
        content="Successfully canceled", status_code=status.HTTP_200_OK
    )


@order_routers.patch(
    "/status/{order_id}",
    response_model=schemas.OrderResponse,
)
async def update_orders_status(
    session: dependency.AsyncSessionDependency,
    order_id: int,
    update_data: schemas.OrderUpdate,
    user: dependency.GetCurrentUserDependency,
):
    """Обновление статуса заказа для менеджеров"""
    utils.check_user_status(user.status, models.UserStatus.MANAGER)
    order = await crud.OrderCrud(session).get_item_id(order_id)
    if order.status == models.OrderStatus.CANCELED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order is canceled",
        )
    data = update_data.model_dump()
    data["id"] = order_id
    order = await crud.OrderCrud(session).create_item(data)
    msg = f"Заказ номер {order.id}\n" f"Статус заказа: {order.status.value}\n"
    celery_data = {
        "emails": order.user.email,
        "msg": msg,
        "subject": "Информация по заказу",
    }
    send_email.delay(celery_data)
    await session.commit()
    await session.refresh(order)
    return order
