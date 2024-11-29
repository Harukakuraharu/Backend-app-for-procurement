from fastapi import HTTPException, status

import models


async def check_owner_product(
    user_id: int, product: models.Product
) -> models.Product:
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product is not exists",
        )
    if product.shop.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="It is not your product",
        )
    return product
