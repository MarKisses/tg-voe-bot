from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis
from .user_storage import UserStorage
from .subscription_storage import SubscriptionStorage

from config import settings


def create_redis_client() -> Redis:
    return Redis(
        host=settings.redis.host,
        port=settings.redis.port,
        db=settings.redis.db,
        password=settings.redis.password,
        username=settings.redis.username,
        decode_responses=True,
    )


def create_storage(redis: Redis):
    return RedisStorage(redis=redis)

_redis = create_redis_client()

user_storage = UserStorage(_redis)
subscription_storage = SubscriptionStorage(_redis)


__all__ = ["create_redis_client", "create_storage", "user_storage", "subscription_storage"]
