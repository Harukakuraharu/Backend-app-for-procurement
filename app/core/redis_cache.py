from cache_fastapi.Backends import base_backend  # type: ignore[import-untyped]
from redis import asyncio as aioredis

from core.settings import config


class RedisBackend(base_backend.BaseBackend):
    def __init__(self):
        super().__init__()
        self.cache = aioredis.from_url(config.redis_cache_url)

    async def create(  # pylint: disable=W0236
        self, resp, key: str, ex: int = 60
    ):
        await self.cache.set(key, resp, ex=ex)

    async def retrieve(self, key: str):  # pylint: disable=W0236
        data = await self.cache.get(key)
        if not data:
            return None
        expire = await self.cache.ttl(key)
        return data, expire

    async def invalidate(self, key: str):  # pylint: disable=W0236
        await self.cache.delete(key)

    async def clear(self):  # pylint: disable=W0236
        await self.cache.flushdb()
