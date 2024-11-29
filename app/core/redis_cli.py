import redis

from core.settings import config


redis_client = redis.Redis().from_url(config.redis_url)  # type: ignore
