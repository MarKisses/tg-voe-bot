from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from bot.filters import FromUserRequired
from bot.keyboards.main_menu import main_menu_keyboard
from bot.utils import edit_message_with_fallback
from logger import create_logger

logger = create_logger(__name__)
router = Router(name=__name__)


async def show_main(source):
    try:
        await source.message.edit_text(
            text="Головне меню бота:", reply_markup=main_menu_keyboard()
        )
    except TelegramBadRequest:
        await source.message.reply(
            text="Головне меню бота:", reply_markup=main_menu_keyboard()
        )


@router.message(Command("start"), FromUserRequired())
async def start(message: Message, state: FSMContext):
    await state.clear()
    logger.info(f"User {message.from_user.id} initiated start command.")
    await edit_message_with_fallback(
        message, text="Головне меню бота:", reply_markup=main_menu_keyboard()
    )
