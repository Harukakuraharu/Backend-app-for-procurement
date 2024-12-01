import json

import sqlalchemy as sa
from fastapi import Depends, HTTPException, status
from fastapi.routing import APIRouter

import models
from api import crud, utils
from core import dependency
from core.celery_app import send_email
from core.redis_cli import redis_client
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
    product = await utils.check_exists(
        session, models.Product, models.Product.id, order_product["product_id"]
    )
    await utils.check_shop_status(product.shop.active)
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
    if not redis_client.get(user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shopping cart is empty",
        )
    orderlist = json.loads(redis_client.get(user.id))
    return orderlist


@orderlist_routers.delete("/")
async def clear_orderlist(user: dependency.GetCurrentUserDependency):
    """Очистка корзины"""
    redis_client.delete(user.id)
    return {"status": "orderlist is clear"}


@order_routers.post("/", response_model=schemas.OrderResponse)
async def create_order(  # pylint: disable=R0914
    session: dependency.AsyncSessionDependency,
    user: dependency.GetCurrentUserDependency,
    data: schemas.OrderCreate,
):
    """Создание заказа"""
    if not redis_client.get(user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shopping cart is empty",
        )
    stmt_emails = sa.select(models.User.email).where(
        models.User.status == models.UserStatus.MANAGER
    )
    manager_emails = await session.scalars(stmt_emails)
    email = manager_emails.all()
    if len(email) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error. Shop do not have a manager",
        )
    address = await utils.check_current_item(
        session,
        models.UserAddress,
        models.UserAddress.id,
        data.address_id,
        user.id,
    )
    products = json.loads(redis_client.get(user.id))
    order = await crud.create_item(
        session,
        {
            "user_id": user.id,
            "status": models.OrderStatus.INPROGRES,
            "address_id": address.id,
        },
        models.Order,
    )
    await session.flush()
    for product in products:
        product["order_id"] = order.id
        await crud.create_item(session, product, models.OrderList)
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
    await utils.check_user_status(user.status)  # type: ignore[arg-type]
    if order_status is not None:
        stmt = sa.select(models.Order).where(
            models.Order.status == order_status
        )
        orders = await session.scalars(stmt)
        return orders.unique().all()
    orders = await crud.get_item(session, models.Order)
    return orders


@order_routers.get("/{order_id}", response_model=schemas.OrderResponse)
async def get_orders_by_id(
    session: dependency.AsyncSessionDependency,
    order_id: int,
    user: dependency.GetCurrentUserDependency,
):
    """Просмотр определенного заказа"""
    await utils.check_user_status(user.status)  # type: ignore[arg-type]
    order = await crud.get_item_id(session, models.Order, order_id)
    return order


@order_routers.get("/me/", response_model=list[schemas.OrderResponse])
async def get_orders_youself(
    session: dependency.AsyncSessionDependency,
    user: dependency.GetCurrentUserDependency,
):
    """Просмотр своих заказов"""
    stmt = sa.select(models.Order).where(models.Order.user_id == user.id)
    orders = await session.scalars(stmt)
    return orders.unique().all()


@order_routers.delete("/me/{order_id}")
async def cancel_order(
    session: dependency.AsyncSessionDependency,
    user: dependency.GetCurrentUserDependency,
    order_id: int,
):
    """Отмена заказа"""
    order = await utils.check_current_item(
        session, models.Order, models.Order.id, order_id, user.id
    )
    if order.status in (models.OrderStatus.SENT, models.OrderStatus.DELIVERED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can not cancel order",
        )
    stmt_emails = sa.select(models.User.email).where(
        models.User.status == models.UserStatus.MANAGER
    )
    manager_emails = await session.scalars(stmt_emails)
    emails = manager_emails.all()
    order.status = models.OrderStatus.CANCELED
    celery_data = {
        "emails": emails,
        "msg": f"Заказ номер {order.id} отменен пользователем",
        "subject": "Отмена заказа",
    }
    send_email.delay(celery_data)
    await session.commit()
    return {"status": "Successfully canceled"}


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
    await utils.check_user_status(user.status)  # type: ignore[arg-type]
    order = await utils.check_exists(
        session, models.Order, models.Order.id, order_id
    )
    if order.status == models.OrderStatus.CANCELED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order is canceled",
        )
    data = update_data.model_dump()
    data["id"] = order_id
    order = await crud.update_item(session, models.Order, data)
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
