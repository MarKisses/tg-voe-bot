import asyncio

from aiogram import Router, types
from aiogram.filters import BaseFilter
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from bot.keyboards import back_to_main_menu_keyboard, main_menu_keyboard
from bot.states.admin_state import AdminState
from bot.utils import tg_sem_replace_service_menu, tg_sem_show_service_menu
from config import settings
from logger import create_logger
from storage import user_storage

logger = create_logger(__name__)


class IsAdmin(BaseFilter):
    def __init__(self, admin_id: int | None):
        self.admin_id = admin_id

    async def __call__(self, message: Message) -> bool:
        if self.admin_id is None:
            return False
        return message.from_user.id == self.admin_id


router = Router(name=__name__)


@router.message(Command("notify_users"), IsAdmin(settings.admin_id))
async def admin_command(message: types.Message, state: FSMContext):
    await message.delete()
    logger.info(f"User {message.from_user.id} initiated admin command.")
    await tg_sem_show_service_menu(
        bot=message.bot,
        chat_id=message.chat.id,
        text="Надішліть повідомлення яке ви хочете надіслати всім користувачам бота:",
        reply_markup=back_to_main_menu_keyboard(),
        old_msg_id=message.message_id,
    )

    await state.set_state(
        AdminState.waiting_for_broadcast
    )  # Set state to wait for broadcast message


@router.message(AdminState.waiting_for_broadcast)
async def broadcast_message_handler(message: types.Message, state: FSMContext):
    await message.delete()
    logger.info(f"Broadcasting message from admin {message.from_user.id} to all users.")

    if not message.text and not message.caption:
        return await tg_sem_show_service_menu(
            bot=message.bot,
            chat_id=message.chat.id,
            text="Будь ласка, надішліть текстове повідомлення для розсилки.",
            reply_markup=back_to_main_menu_keyboard(),
        )

    user_ids = await user_storage.get_all_users_id()
    user_ids.discard(message.from_user.id)  # Exclude admin from broadcast if present
    
    photo = message.photo[-1] if message.photo else None

    if photo:
        content_to_log = f"[photo] caption={message.caption!r}"
    else:
        content_to_log = f"[text] {message.text!r}"
    logger.info(f"Broadcast message content: {content_to_log}")
    
    message_tasks = []
    menu_tasks = []
    for user_id in user_ids:
        
        if photo:
            message_tasks.append(
                message.bot.send_photo(
                    chat_id=user_id,
                    photo=photo.file_id,
                    caption=message.caption,
                    parse_mode="HTML",
                )
            )
        else:
            message_tasks.append(
                message.bot.send_message(
                    chat_id=user_id,
                    text=message.text,
                    parse_mode="HTML",
                )
            )

        menu_tasks.append(
            tg_sem_replace_service_menu(
                bot=message.bot,
                chat_id=user_id,
                text="Головне меню бота:",
                reply_markup=main_menu_keyboard(),
            )
        )

    await asyncio.gather(*message_tasks)
    await asyncio.gather(*menu_tasks)
    await state.clear()  # Clear state after broadcasting

    await tg_sem_show_service_menu(
        bot=message.bot,
        chat_id=message.chat.id,
        text="Повідомлення було надіслано всім користувачам бота.",
        reply_markup=main_menu_keyboard(),
    )

