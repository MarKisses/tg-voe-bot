from aiogram import Router
from aiogram.filters.command import Command
from aiogram import types
from aiogram.fsm.context import FSMContext

from aiogram.types import Message
from aiogram.filters import BaseFilter
from config import settings

from logging import getLogger

logger = getLogger(__name__)

class IsAdmin(BaseFilter):
    def __init__(self, admin_id: int):
        self.admin_id = admin_id

    async def __call__(self, message: Message) -> bool:
        return message.from_user.id == self.admin_id


router = Router(name=__name__)


@router.message(Command("/add_cookie"), IsAdmin(settings.admin_id))
async def add_cookie(message: types.Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} initiated add_cookie command.")
    await message.answer("Please send me the cookie value.")

