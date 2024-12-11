from typing import Sequence

import sqlalchemy as sa

import models
from crud.base_crud import BaseCrudRestrict


class ShopCrud(BaseCrudRestrict):
    def __init__(self, session):
        super().__init__(session)
        self.model = models.Shop

    async def get_shop_active(
        self, shop_active: bool
    ) -> Sequence[models.Shop]:
        stmt = sa.select(self.model).where(
            self.model.active == shop_active  # pylint: disable=C0121
        )
        shop = await self.session.scalars(stmt)
        return shop.unique().all()
