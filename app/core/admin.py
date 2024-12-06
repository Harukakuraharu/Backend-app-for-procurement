from fastapi import HTTPException, status
from sqladmin import ModelView
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from starlette.requests import Request

import models
from core import security
from core.settings import config


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        email, password = form["username"], form["password"]
        async with AsyncSession(
            create_async_engine(config.async_dsn)  # type: ignore[arg-type]
        ) as session:
            user = await security.auth(
                session, email, password  # type: ignore[arg-type]
            )
            request.session.update({"token": "..."})
            if user.status == models.UserStatus.BUYER:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    "User would be shop or manager",
                )
            return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        if not token:
            return False
        return True


authentication_backend = AdminAuth(secret_key="...")


class UserAdmin(ModelView, model=models.User):
    column_list = [
        models.User.id,
        models.User.email,
        models.User.status,
        models.User.active,
    ]
    column_searchable_list = [models.User.email]
    can_create = False
    can_edit = False
    can_delete = False
    can_view_details = False


class ProductAdmin(ModelView, model=models.Product):
    column_list = [
        models.Product.id,
        models.Product.name,
        models.Product.remainder,
        models.Product.price,
        models.Product.shop,
    ]
    column_searchable_list = [models.Product.name]
    can_create = False
    can_edit = False
    can_delete = False
    can_view_details = False


class ShopAdmin(ModelView, model=models.Shop):
    column_list = [
        models.Shop.id,
        models.Shop.title,
        models.Shop.active,
        models.Shop.user,
    ]
    column_searchable_list = [models.Shop.title]
    can_create = False
    can_edit = False
    can_delete = False
    can_view_details = False


class OrderAdmin(ModelView, model=models.Order):
    column_list = "__all__"
    can_create = False
    can_delete = False
