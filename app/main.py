from fastapi import FastAPI

from api.import_product import import_routers
from api.orders import order_routers, orderlist_routers
from api.products import category_routers, parametr_routers, product_routers
from api.shop import shop_routers
from api.users import user_routers


app = FastAPI()

app.include_router(user_routers)
app.include_router(product_routers)
app.include_router(shop_routers)
app.include_router(category_routers)
app.include_router(parametr_routers)
app.include_router(order_routers)
app.include_router(orderlist_routers)
app.include_router(import_routers)
