import inspect
import json
from typing import Optional

from redis.asyncio import Redis
from services.models import Address
from pydantic import BaseModel


class UserStorage:
    def __init__(self, redis: Redis) -> None:
        self.r = redis

    @staticmethod
    def _key(user_id: int) -> str:
        return f"user:{user_id}:addresses"

    @staticmethod
    def _service_msg_key(chat_id: int) -> str:
        return f"service_msg:{chat_id}"

    @staticmethod
    def _render_text_flag_key(user_id: int) -> str:
        return f"settings:{user_id}:render_text"

    async def is_render_text_enabled(self, user_id: int) -> bool:
        key = self._render_text_flag_key(user_id)
        raw = await self.r.get(key)
        if not raw:
            return False
        return True

    async def enable_render_text(self, user_id: int) -> None:
        key = self._render_text_flag_key(user_id)
        await self.r.set(key, 1)

    async def disable_render_text(self, user_id: int) -> None:
        key = self._render_text_flag_key(user_id)
        await self.r.delete(key)

    async def clear_service_msg(self, chat_id: int) -> None:
        key = self._service_msg_key(chat_id)
        await self.r.delete(key)

    async def set_service_msg(self, chat_id: int, msg_id: int) -> None:
        key = self._service_msg_key(chat_id)
        await self.r.set(key, msg_id)

    async def get_service_msg(self, chat_id: int) -> Optional[int]:
        key = self._service_msg_key(chat_id)
        raw = await self.r.get(key)
        if not raw:
            return None
        return int(raw)

    async def get_addresses(self, user_id: int) -> list[Address]:
        """
        Get all addresses of the user.
        """
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
        """
        Add address to the user's list. If it already exists, it will be updated.
        """
        key = self._key(user_id)
        addr_id = address.id

        current = await self.get_addresses(user_id)

        # Remove duplicates
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
            Remove address from the user's list.
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
        Clear all addresses of the user.
        """
        key = self._key(user_id)
        await self.r.delete(key)

    async def set_cached_schedule(self, addr_id: str, data: BaseModel, ttl=3600):
        await self.r.set(f"schedule:{addr_id}", data.model_dump_json(), ex=ttl)

    async def get_cached_schedule(self, addr_id: str) -> dict | None:
        raw = await self.r.get(f"schedule:{addr_id}")
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    async def get_all_users_id(self) -> set[int]:
        """
        Get all user IDs who have stored addresses.
        """
        pattern = "user:*:addresses"
        user_ids = set()

        async for key in self.r.scan_iter(pattern):
            user_id = int(key.split(":")[1])
            user_ids.add(user_id)
        return user_ids
