from typing import Any, Sequence

import sqlalchemy as sa

import models
from crud.base_crud import BaseCrud


class OrderCrud(BaseCrud):
    def __init__(self, session):
        super().__init__(session)
        self.model = models.Order

    async def get_order_status(
        self, order_status: models.OrderStatus
    ) -> Sequence[models.Order]:
        stmt = sa.select(self.model).where(self.model.status == order_status)
        order = await self.session.scalars(stmt)
        return order.unique().all()

    # async def get_yours_order(self, user_id: int) -> Sequence[models.Order]:
    #     stmt = sa.select(self.model).where(self.model.user_id == user_id)
    #     orders = await self.session.scalars(stmt)
    #     return orders.unique().all()


class OrderlistCrud(BaseCrud):
    def __init__(self, session):
        super().__init__(session)
        self.model = models.OrderList

    async def create_orderlist(self, orderlist: list[dict[str, Any]]) -> None:
        stmt = sa.insert(self.model).values(orderlist)
        await self.session.execute(stmt)
