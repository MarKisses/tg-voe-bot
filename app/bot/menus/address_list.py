from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from storage import user_storage
from bot.utils import tg_sem_show_service_menu

from bot.keyboards import address_list_keyboard


async def show_address_list(source: CallbackQuery, state: FSMContext):
    await state.clear()
    addresses = await user_storage.get_addresses(source.from_user.id)
    if not addresses:
        await tg_sem_show_service_menu(
            bot=source.bot,
            chat_id=source.message.chat.id,
            text="У вас немає збережених адрес.",
            reply_markup=address_list_keyboard(None),
            old_msg_id=source.message.message_id,
        )
        return await source.answer()
        
    await tg_sem_show_service_menu(
        bot=source.bot,
        chat_id=source.message.chat.id,
        text="Список ваших адрес:",
        reply_markup=address_list_keyboard(addresses),
        old_msg_id=source.message.message_id,
    )
    
    await source.answer()
    
