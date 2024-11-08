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
    status: models.UserStatus
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


class ShopProduct(Shop):
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
    products: list["ProductResponse"]
    model_config = ConfigDict(from_attributes=True)


# product
class Product(BaseModel):
    name: str
    price: float = Field(gt=0)
    remainder: int


class CategoryProduct(Category):
    id: int


class ProductCreate(Product):
    categories: list[int]
    shop_id: int


class ProductResponse(Product):
    categories: list[CategoryProduct]
    shop: "ShopProduct"
    id: int
    model_config = ConfigDict(from_attributes=True)


# parametr
class Parametr(BaseModel):
    name: str


class ParametrResponse(Parametr):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ParametrProduct(BaseModel):
    value: str


class ParametrProductResponse(ParametrProduct):
    product: list[Product]
    parametr: list[Parametr]
    model_config = ConfigDict(from_attributes=True)
