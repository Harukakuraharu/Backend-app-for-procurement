import sys
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import Depends, FastAPI
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

from api.import_product import import_routers
from api.orders import order_routers, orderlist_routers
from api.products import category_routers, parametr_routers, product_routers
from api.shop import shop_routers
from api.users import user_routers
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
if "pytest" not in sys.modules:
    dependencies.append(Depends(RateLimiter(times=2, seconds=3)))

app = FastAPI(lifespan=lifespan, dependencies=dependencies)


app.include_router(user_routers)
app.include_router(product_routers)
app.include_router(shop_routers)
app.include_router(category_routers)
app.include_router(parametr_routers)
app.include_router(order_routers)
app.include_router(orderlist_routers)
app.include_router(import_routers)
