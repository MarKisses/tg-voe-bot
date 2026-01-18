from logging import getLogger

from aiogram import Router, types
from aiogram.filters import BaseFilter
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from bot.keyboards import main_menu_keyboard
from bot.utils import tg_sem_show_service_menu
from config import settings

logger = getLogger(__name__)


class IsAdmin(BaseFilter):
    def __init__(self, admin_id: int | None):
        self.admin_id = admin_id

    async def __call__(self, message: Message) -> bool:
        if self.admin_id is None:
            return False
        return message.from_user.id == self.admin_id


router = Router(name=__name__)


@router.message(Command("/add_cookie"), IsAdmin(settings.admin_id))
async def add_cookie(message: types.Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} initiated add_cookie command.")
    await tg_sem_show_service_menu(
        bot=message.bot,
        chat_id=message.chat.id,
        text="Hello fucker :)))",
        reply_markup=main_menu_keyboard(),
        old_msg_id=message.message_id,
    )
