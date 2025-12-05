from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis
from .user_storage import UserStorage

from config import settings


def create_redis_client() -> Redis:
    return Redis(
        host=settings.redis.host,
        port=settings.redis.port,
        db=settings.redis.db,
        password=settings.redis.password,
    )


def create_storage(redis: Redis):
    return RedisStorage(redis=redis)


user_storage = UserStorage(create_redis_client())


__all__ = ["create_redis_client", "create_storage", "user_storage"]
