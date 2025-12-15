from aiogram.filters import BaseFilter
from aiogram.types import Message

class FromUserRequired(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user is not None
