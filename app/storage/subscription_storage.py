import inspect
from typing import Literal

from redis.asyncio import Redis

SubscriptionKind = Literal["today", "tomorrow"]


class SubscriptionStorage:
    """
    Storage for schedule change subscriptions.

    Keys:
    - subs:{kind}:addr:{addr_id} = set of user_ids (SET)
    - subs:{kind}:hash:{addr_id} = last hash (STR)
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
        """
        Add a subscription for a user to a specific address and kind.
        """
        if inspect.isawaitable(
            sadd := self.r.sadd(self._addr_key(kind, addr_id), user_id)
        ):
            await sadd

    async def remove_subscription(
        self,
        user_id: int,
        addr_id: str,
        kind: SubscriptionKind,
    ) -> None:
        """
        Remove a subscription for a user to a specific address and kind.
        """
        if inspect.isawaitable(
            srem := self.r.srem(self._addr_key(kind, addr_id), user_id)
        ):
            await srem

    async def get_subscribers(
        self,
        addr_id: str,
        kind: SubscriptionKind,
    ) -> set[int]:
        """
        Get a set of user_ids subscribed to a specific address and kind.
        """
        if inspect.isawaitable(raw := self.r.smembers(self._addr_key(kind, addr_id))):
            raw = await raw
        return {int(x) for x in raw}

    async def get_all_addresses(self) -> set[str]:
        """
        Get all address IDs that have any subscriptions.
        returns a set of address IDs.
        """
        return {
            *await self.get_all_addresses_for_kind("today"),
            *await self.get_all_addresses_for_kind("tomorrow"),
        }

    async def get_all_addresses_for_kind(
        self,
        kind: SubscriptionKind,
    ) -> set[str]:
        """
        Get all address IDs that have subscriptions for the given kind.
        returns a set of address IDs.
        """
        pattern = f"subs:{kind}:addr:*"
        addr_ids: set[str] = set()
        async for key in self.r.scan_iter(pattern):
            # key is of type b"subs:today:addr:510100000-1444-32599"
            parts = key.split(":")
            addr_ids.add(parts[-1])
        return addr_ids

    async def get_last_hash(
        self,
        addr_id: str,
        kind: SubscriptionKind,
    ) -> str | None:
        """
        Get the last hash for a specific address and kind.
        """
        return await self.r.get(self._hash_key(kind, addr_id))

    async def set_last_hash(
        self,
        addr_id: str,
        kind: SubscriptionKind,
        value: str,
    ) -> None:
        """
        Set the last hash for a specific address and kind.
        """
        await self.r.set(self._hash_key(kind, addr_id), value)

    async def get_subscription_status(
        self, user_id: int, addr_id: str
    ) -> dict[str, bool]:
        """
        Get subscription status for both 'today' and 'tomorrow' kinds for a user and address.
        """
        return {
            "today": user_id in await self.get_subscribers(addr_id, "today"),
            "tomorrow": user_id in await self.get_subscribers(addr_id, "tomorrow"),
        }
        
    async def toggle_subscription(
        self,
        user_id: int,
        addr_id: str,
        kind: SubscriptionKind,
    ) -> tuple[bool, str]:
        """
        Toggle subscription status. Returns the new status (True - subscribed).
        """
        current = await self.get_subscribers(addr_id, kind)

        if user_id in current:
            await self.remove_subscription(user_id, addr_id, kind)
            return False, "✅ Ви відписались від сповіщень на зміни на сьогодні." if kind == "today" else "✅ Ви відписались від сповіщень на графік на завтра."
        else:
            await self.add_subscription(user_id, addr_id, kind)
            return True, "✅ Ви підписались на сповіщення на зміни на сьогодні." if kind == "today" else "✅ Ви підписались на сповіщення на графік на завтра."
