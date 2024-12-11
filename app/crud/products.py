from typing import Any, Sequence

import sqlalchemy as sa

import models
from crud.base_crud import BaseCrud, BaseCrudRestrict


class ProductCrud(BaseCrud):
    def __init__(self, session):
        super().__init__(session)
        self.model = models.Product


class CategoryCrud(BaseCrudRestrict):
    def __init__(self, session):
        super().__init__(session)
        self.model = models.Category

    async def get_category(
        self, categories_id: list[int]
    ) -> Sequence[models.Category]:
        stmt_cat = sa.select(self.model).where(
            self.model.id.in_(categories_id)
        )
        categories_product = await self.session.scalars(stmt_cat)
        return categories_product.all()


class ParametrProductCrud(BaseCrud):
    def __init__(self, session):
        super().__init__(session)
        self.model = models.ParametrProduct

    async def create_parametr_product(
        self, parametrs: list[dict[str, Any]]
    ) -> None:

        stmt_paramert_product = sa.insert(self.model).values(parametrs)
        await self.session.execute(stmt_paramert_product)

    async def update_parametr_product(
        self, parametr: dict[str, Any], product_id: int
    ):
        stmt = (
            sa.update(self.model)
            .values(value=parametr["value"])
            .where(
                (self.model.parametr_id == parametr["parametr_id"])
                & (self.model.product_id == product_id)
            )
        )
        await self.session.execute(stmt)


class ParametrCrud(BaseCrudRestrict):
    def __init__(self, session):
        super().__init__(session)
        self.model = models.Parametr
