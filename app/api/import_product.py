from fastapi import HTTPException, UploadFile, status
from fastapi.routing import APIRouter

import models
from core import dependency
from core.celery_app import products_import


import_routers = APIRouter(prefix="/import_product", tags=["ImportProduct"])


@import_routers.post("/")
async def import_product(
    file: UploadFile,
    user: dependency.GetCurrentUserDependency,
):
    """Import products from file"""
    if user.status != models.UserStatus.SHOP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only for shop",
        )
    contents = await file.read()
    products_import.delay(contents, user.id)
    return {"status": "file upload"}
