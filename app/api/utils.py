from fastapi import HTTPException, status

import models
from core.redis_cli import redis_client
from schemas import schemas


def check_owner_product(user_id: int, product: models.Product) -> None:
    if product.shop.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="It is not your product",
        )


def check_shop_status(shop_status: bool) -> None:
    """To check status of shop"""
    if shop_status is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shop would be active",
        )


def check_user_status(
    user_status: models.UserStatus, common_status: models.UserStatus
) -> None:
    """To check status of user"""
    if user_status != common_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You do not have permission",
        )


def check_shop_exists(user: schemas.UserResponse) -> None:
    if user.shop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Shop is not exists"
        )


def check_orderlist(user_id: int) -> None:
    if not redis_client.get(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shopping cart is empty",
        )
