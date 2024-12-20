from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import HTTPException, status

from core.dependency import AsyncSessionDependency
from core.settings import config
from crud.users import UserCrud


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(
    password: str,
    hashed_password: str,
) -> bool:
    return bcrypt.checkpw(password.encode(), hashed_password.encode())


async def auth(session: AsyncSessionDependency, email: str, password: str):
    user = await UserCrud(session).get_user(email)
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "User is not exists")
    if user.active is False:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "User is not verify with email"
        )
    if not user or not check_password(password, user.password):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Incorrect password or username"
        )
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM
    )
    return encoded_jwt
