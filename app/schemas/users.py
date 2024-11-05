from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr
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


class UserCreate(User):
    password: Password


class UserUpdate(BaseModel):
    status: models.UserStatus
    name: str | None = None
    phone: str | None = None
