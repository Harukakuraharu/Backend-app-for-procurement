import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from pydantic.functional_validators import AfterValidator

import models


def validate_password(password: str) -> str:
    assert len(password) >= 8, f"{password} is short"
    assert password.isalnum(), f"{password} must contain numbers and letters"
    return password


Password = Annotated[str, AfterValidator(validate_password)]


class UserAddress(BaseModel):
    city: str
    address: str


class UserAddressResponse(UserAddress):
    id: int
    model_config = ConfigDict(from_attributes=True)


class User(BaseModel):
    email: EmailStr
    status: models.UserStatus
    name: str
    phone: str


class UserResponse(User):
    id: int
    addresses: list[UserAddressResponse]
    model_config = ConfigDict(from_attributes=True)


class UserCreateResponse(User):
    id: int
    model_config = ConfigDict(from_attributes=True)


class UserCreate(User):
    password: Password


class UserUpdate(BaseModel):
    status: models.UserStatus | None = None
    name: str | None = None
    phone: str | None = None


class Token(BaseModel):
    access_token: str


class UserLogin(BaseModel):
    email: str
    password: str


# shop
class Shop(BaseModel):
    title: str
    url: str


class ShopForProduct(Shop):
    id: int


class ShopCreateResponse(Shop):
    id: int
    active: bool = False
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)


class UserShopResponse(BaseModel):
    id: int


class ShopsResponse(Shop):
    id: int
    active: bool
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)
    user: UserShopResponse


class ShopResponse(Shop):
    id: int
    active: bool
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)
    user: UserShopResponse
    products: list["Product"]


class ShopUpdate(BaseModel):
    title: str | None = None
    url: str | None = None
    active: bool | None = None


# category
class Category(BaseModel):
    title: str


class CategoryResponse(Category):
    id: int
    products: list["ProductsResponse"]
    model_config = ConfigDict(from_attributes=True)


class CategoryCreateResponse(Category):
    id: int
    model_config = ConfigDict(from_attributes=True)


# product
class Product(BaseModel):
    name: str
    price: float = Field(gt=0)
    remainder: int


class CategoryProduct(Category):
    id: int


class ParametrProductCreate(BaseModel):
    parametr_id: int
    value: str


class ParametrProductCreateResponse(ParametrProductCreate):
    id: int
    # product_id: int


class ProductCreate(Product):
    categories: list[int]
    parametrs: list[ParametrProductCreate]
    shop_id: int


class ProductsResponse(Product):
    id: int
    categories: list[CategoryProduct]
    shop: "ShopForProduct"
    parametrs: list[ParametrProductCreateResponse]
    model_config = ConfigDict(from_attributes=True)


class ProductUpdate(BaseModel):
    name: str | None = None
    price: float | None = None
    remainder: int | None = None
    parametrs: list["ParametrProductUpdateResponse"] | None = None
    categories: list[int] | None = None


class ParametrProductUpdateResponse(BaseModel):
    parametr_id: int | None = None
    value: str | None = None


class ProductParametrsDelete(BaseModel):
    parametrs: list[int] | None = None
    categories: list[int] | None = None


class ParametrProductDeleteResponse(BaseModel):
    parametr_id: int | None = None


# parametr
class Parametr(BaseModel):
    name: str


class ParametrResponse(Parametr):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ParametrProduct(BaseModel):
    parametr_id: int
    product_id: int
    value: str


class ParametrProductForResponse(BaseModel):
    value: str


class ParametrProductResponse(ParametrProduct):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ParametrProductResponseParametr(ParametrProductForResponse):
    parametr_id: int


class ParametrProductCreateParametr(BaseModel):
    id: int
    product_id: int
    value: str
    parametr_id: int


# orders
class Order(BaseModel):
    pass


class OrderResponse(Order):
    pass
