from fastapi import FastAPI

from api.products import product_routers
from api.shop import shop_routers
from api.users import user_routers


app = FastAPI()

app.include_router(user_routers)
app.include_router(product_routers)
app.include_router(shop_routers)
