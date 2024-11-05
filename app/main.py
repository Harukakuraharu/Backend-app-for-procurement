from fastapi import FastAPI

from api.users import user_routers


app = FastAPI()

app.include_router(user_routers)
