import inspect
import json
from typing import Optional

from redis.asyncio import Redis

from services.models import Address, ScheduleResponse


class UserStorage:
    def __init__(self, redis: Redis) -> None:
        self.r = redis

    def _key(self, user_id: int) -> str:
        return f"user:{user_id}:addresses"

    async def get_addresses(self, user_id: int) -> list[Address]:
        key = self._key(user_id)

        if inspect.isawaitable(raw_items := self.r.lrange(key, 0, -1)):
            raw_items = await raw_items

        if not raw_items:
            return []

        addresses: list[Address] = []
        for item in raw_items:
            try:
                addresses.append(Address.model_validate_json(item))
            except json.JSONDecodeError:
                continue
        return addresses

    async def add_address(self, user_id: int, address: Address) -> None:
        key = self._key(user_id)
        addr_id = address.id

        current = await self.get_addresses(user_id)

        # убираем дубликаты
        filtered = [a for a in current if a.id != addr_id]
        filtered.append(address)

        pipe = self.r.pipeline()
        await pipe.delete(key)

        for a in filtered:
            if inspect.isawaitable(rpush := pipe.rpush(key, a.model_dump_json())):
                await rpush

        await pipe.execute()

    async def get_address_by_id(
        self, user_id: int, address_id: str
    ) -> Optional[Address]:
        addresses = await self.get_addresses(user_id)
        for addr in addresses:
            if addr.id == address_id:
                return addr
        return None

    async def remove_address(self, user_id: int, address_id: str) -> None:
        """
        Удалить адрес по id. Если его нет — тихо ничего не делаем.
        """
        key = self._key(user_id)
        current = await self.get_addresses(user_id)
        filtered = [a for a in current if a.id != address_id]

        pipe = self.r.pipeline()
        await pipe.delete(key)
        if filtered:
            for a in filtered:
                if inspect.isawaitable(rpush := pipe.rpush(key, a.model_dump_json())):
                    await rpush
        await pipe.execute()

    async def clear_all(self, user_id: int) -> None:
        """
        Полностью удалить все адреса пользователя.
        """
        key = self._key(user_id)
        await self.r.delete(key)

    async def set_cached_schedule(self, addr_id: str, data: dict, ttl=3600):
        await self.r.set(f"schedule:{addr_id}", json.dumps(data), ex=ttl)
        
    async def get_cached_schedule(self, addr_id: str) -> dict | None:
        raw = await self.r.get(f"schedule:{addr_id}")
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None
