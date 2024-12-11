from typing import Any, Sequence

import sqlalchemy as sa
from fastapi import HTTPException, status

import models
from crud.base_crud import BaseCrud, BaseCrudRestrict


class UserCrud(BaseCrudRestrict):
    def __init__(self, session):
        super().__init__(session)
        self.model = models.User

    async def get_user(self, email: str) -> models.User:
        stmt = sa.select(self.model).where(self.model.email == email)
        user = await self.session.scalar(stmt)
        if user is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, f"{email} not found"
            )
        return user

    async def get_user_buyer(
        self, user_status: models.UserStatus
    ) -> Sequence[models.User]:
        stmt = sa.select(self.model).where(self.model.status == user_status)
        user = await self.session.scalars(stmt)
        return user.unique().all()

    async def get_manager_emails(self):
        stmt = sa.select(self.model.email).where(
            self.model.status == models.UserStatus.MANAGER
        )
        emails = await self.session.scalars(stmt)
        return emails.all()


class UserAddressCrud(BaseCrud):
    def __init__(self, session):
        super().__init__(session)
        self.model = models.UserAddress

    async def update_item(self, data: dict[str, Any]) -> models.UserAddress:
        await self.check_owner(data["id"], data["user_id"])
        return await super().update_item(data)

    async def delete_address(self, address_id: int, user_id: int):
        await self.check_owner(address_id, user_id)
        await self.delete_item(address_id)
