from typing import Annotated

import jwt
import sqlalchemy as sa
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from core.settings import config
from models import User
from schemas.users import UserResponse


async def get_session():
    async with AsyncSession(create_async_engine(config.async_dsn)) as session:
        yield session


AsyncSessionDependency = Annotated[
    AsyncSession, Depends(get_session, use_cache=True)
]


async def get_user(session: AsyncSessionDependency, email: str):
    stmt = sa.select(User).where(User.email == email)
    user = await session.scalar(stmt)
    return user


async def get_current_user(
    # pylint: disable=C0301
    token: Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())],
    session: AsyncSessionDependency,
) -> UserResponse:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token.credentials, config.SECRET_KEY, algorithms=[config.ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except InvalidTokenError as err:
        raise credentials_exception from err
    user = await get_user(session, email)
    if user is None:
        raise credentials_exception
    return user


GetCurrentUserDependency = Annotated[UserResponse, Depends(get_current_user)]
