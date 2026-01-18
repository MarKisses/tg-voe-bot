from aiogram import Router
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from bot.filters import FromUserRequired
from bot.keyboards.main_menu import main_menu_keyboard, back_to_main_menu_keyboard
from bot.utils import tg_sem_replace_service_menu, tg_sem_show_service_menu
from bot.menus.about import text
from logger import create_logger

logger = create_logger(__name__)
router = Router(name=__name__)


@router.message(Command("start"), FromUserRequired())
async def start(message: Message, state: FSMContext):
    await state.clear()
    logger.info(f"User {message.from_user.id} initiated start command.")
    
    await message.delete()

    await tg_sem_replace_service_menu(
        bot=message.bot,
        chat_id=message.chat.id,
        text="Головне меню бота:",
        reply_markup=main_menu_keyboard(),
    )

# TODO: add /help handler    
@router.message(Command("about"), FromUserRequired())
async def info(message: Message, state: FSMContext):
    await state.clear()
    logger.info(f"User {message.from_user.id} requested info command.")

    await message.delete()

    await tg_sem_show_service_menu(
        bot=message.bot,
        chat_id=message.chat.id,
        text=text,
        reply_markup=back_to_main_menu_keyboard(),
        old_msg_id=message.message_id,
    )
