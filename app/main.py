from contextlib import asynccontextmanager

import redis.asyncio as redis
from cache_fastapi.cacheMiddleware import (  # type: ignore[import-untyped]
    CacheMiddleware,
)
from fastapi import Depends, FastAPI
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from sqladmin import Admin

from api.import_product import import_routers
from api.orders import order_routers, orderlist_routers
from api.products import category_routers, parametr_routers, product_routers
from api.shop import shop_routers
from api.users import user_routers
from core import admin as sqladmin
from core.celery_app import engine
from core.redis_cache import RedisBackend
from core.settings import config


@asynccontextmanager
async def lifespan(_: FastAPI):
    redis_connection = redis.from_url(
        config.redis_url, encoding="utf8"  # type: ignore
    )
    await FastAPILimiter.init(redis_connection)
    yield
    await FastAPILimiter.close()


dependencies = []
if config.DEBUG is False:
    dependencies.append(Depends(RateLimiter(times=5, seconds=3)))


app = FastAPI(lifespan=lifespan, dependencies=dependencies)

# main routers for app
app.include_router(user_routers)
app.include_router(product_routers)
app.include_router(shop_routers)
app.include_router(category_routers)
app.include_router(parametr_routers)
app.include_router(order_routers)
app.include_router(orderlist_routers)
app.include_router(import_routers)


# cache
cached_endpoints = [
    "/user/",
    "/product/",
    "/order/",
    "/category",
    "/parametr/",
]
backend = RedisBackend()
app.add_middleware(
    CacheMiddleware, cached_endpoints=cached_endpoints, backend=backend
)


# sqladmin
admin = Admin(
    app, engine, authentication_backend=sqladmin.authentication_backend
)
admin.add_view(sqladmin.UserAdmin)
admin.add_view(sqladmin.ProductAdmin)
admin.add_view(sqladmin.ShopAdmin)
admin.add_view(sqladmin.OrderAdmin)
