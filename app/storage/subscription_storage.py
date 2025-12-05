from typing import Literal
from redis.asyncio import Redis
import inspect

SubscriptionKind = Literal["today", "tomorrow"]


class SubscriptionStorage:
    """
    Хранилище подписок на изменения графика.

    Ключи:
    - subs:{kind}:addr:{addr_id} = множество user_id (SET)
    - subs:{kind}:hash:{addr_id} = последний хеш (STR)
    """

    def __init__(self, redis: Redis) -> None:
        self.r = redis

    def _addr_key(self, kind: SubscriptionKind, addr_id: str) -> str:
        return f"subs:{kind}:addr:{addr_id}"

    def _hash_key(self, kind: SubscriptionKind, addr_id: str) -> str:
        return f"subs:{kind}:hash:{addr_id}"

    async def add_subscription(
        self,
        user_id: int,
        addr_id: str,
        kind: SubscriptionKind,
    ) -> None:
        if inspect.isawaitable(sadd := self.r.sadd(self._addr_key(kind, addr_id), user_id)):
            await sadd

    async def remove_subscription(
        self,
        user_id: int,
        addr_id: str,
        kind: SubscriptionKind,
    ) -> None:
        if inspect.isawaitable(srem := self.r.srem(self._addr_key(kind, addr_id), user_id)):
            await srem

    async def get_subscribers(
        self,
        addr_id: str,
        kind: SubscriptionKind,
    ) -> list[int]:
        if inspect.isawaitable(raw := self.r.smembers(self._addr_key(kind, addr_id))):
            raw = await raw
        return [int(x) for x in raw]

    async def get_all_addresses_for_kind(
        self,
        kind: SubscriptionKind,
    ) -> list[str]:
        """
        Возвращает список addr_id, по которым есть подписчики.
        """
        pattern = f"subs:{kind}:addr:*"
        addr_ids: list[str] = []
        async for key in self.r.scan_iter(pattern):
            # key типа b"subs:today:addr:510100000-1444-32599"
            parts = key.decode().split(":")
            addr_ids.append(parts[-1])
        return addr_ids

    async def get_last_hash(
        self,
        addr_id: str,
        kind: SubscriptionKind,
    ) -> str | None:
        return await self.r.get(self._hash_key(kind, addr_id))

    async def set_last_hash(
        self,
        addr_id: str,
        kind: SubscriptionKind,
        value: str,
    ) -> None:
        await self.r.set(self._hash_key(kind, addr_id), value)
