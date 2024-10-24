from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from core.settings import config


async def get_session():
    async with AsyncSession(create_async_engine(config.dsn)) as session:
        yield session


AsyncSessionDependency = Annotated[
    AsyncSession, Depends(get_session, use_cache=True)
]
