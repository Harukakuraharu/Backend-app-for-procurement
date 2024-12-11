from typing import Any, Literal, Sequence

import sqlalchemy as sa
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models import TypeModel


class BaseCrud:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.model: TypeModel

    async def create_item(self, data: dict[str, Any]):
        stmt = sa.insert(self.model).returning(self.model).values(**data)
        response = await self.session.scalar(stmt)
        return response

    async def get_items(self):
        stmt = sa.select(self.model)
        response = await self.session.scalars(stmt)
        return response.unique().all()

    async def update_item(self, data: dict[str, Any]):
        item_id = data.pop("id")
        stmt = (
            sa.update(self.model)
            .values(**data)
            .where(self.model.id == item_id)
            .returning(self.model)
        )
        response = await self.session.scalar(stmt)
        return response

    async def delete_item(self, item_id: int):
        stmt = sa.delete(self.model).where(self.model.id == item_id)
        await self.session.execute(stmt)

    async def get_item_id(self, item_id: int):
        stmt = sa.select(self.model).where(self.model.id == item_id)
        response = await self.session.scalar(stmt)
        if response is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, f"{self.model.__name__} not found"
            )
        return response

    async def get_user_items(self, user_id: int) -> Sequence[TypeModel]:
        stmt = sa.select(self.model).where(self.model.user_id == user_id)
        result = await self.session.scalars(stmt)
        return result.unique().all()

    async def check_owner(self, item_id: int, user_id: int):
        result = await self.get_item_id(item_id)
        if result.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{self.model.__name__} is not yours",
            )
        return result


class BaseCrudRestrict(BaseCrud):
    def __init__(self, session):
        super().__init__(session)
        self.action = {"create": self.create_item, "update": self.update_item}

    async def create_or_update(
        self, data: dict[str, Any], action: Literal["create", "update"]
    ):
        try:
            model = await self.action[action](data)
        except IntegrityError as error:
            if error.orig is not None and "uq_" in error.orig.args[0]:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    f"{self.model.__name__} already exists",
                ) from error
            raise error
        return model
