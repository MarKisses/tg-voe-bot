from aiogram.fsm.storage.redis import RedisStorage
from config import settings
from redis.asyncio import ConnectionPool, Redis

from .subscription_storage import SubscriptionStorage
from .user_storage import UserStorage


def create_redis_client() -> Redis:
    connection_pool = ConnectionPool(
        host=settings.redis.host,
        port=settings.redis.port,
        db=settings.redis.db,
        password=settings.redis.password,
        username=settings.redis.username,
        decode_responses=True,
        max_connections=25,
    )

    return Redis(connection_pool=connection_pool)


def create_storage(redis: Redis):
    return RedisStorage(redis=redis)


_redis = create_redis_client()

fsm_storage = create_storage(_redis)
user_storage = UserStorage(_redis)
subscription_storage = SubscriptionStorage(_redis)


__all__ = [
    "create_redis_client",
    "create_storage",
    "user_storage",
    "subscription_storage",
    "fsm_storage",
]
