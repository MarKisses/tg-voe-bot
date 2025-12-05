from aiogram.types import CallbackQuery

from bot.keyboards import address_list_keyboard
from storage import user_storage
from aiogram.types import Message


async def show_address_list(source: CallbackQuery):
    addresses = await user_storage.get_addresses(source.from_user.id)
    if not addresses:
        await source.message.edit_text(
            text="У вас немає збережених адрес.",
            reply_markup=address_list_keyboard(None),
        )
        return

    if isinstance(source, CallbackQuery):
        # await source.message.
        await source.message.edit_text(
            text="Список ваших адрес:", reply_markup=address_list_keyboard(addresses)
        )
        await source.answer()
        return

    
