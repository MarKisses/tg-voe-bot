from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery
from storage import user_storage

from bot.keyboards import address_list_keyboard


async def show_address_list(source: CallbackQuery):
    addresses = await user_storage.get_addresses(source.from_user.id)
    if not addresses:
        await source.message.edit_text(
            text="У вас немає збережених адрес.",
            reply_markup=address_list_keyboard(None),
        )
        return

    try:
        # await source.message.
        await source.message.edit_text(
            text="Список ваших адрес:", reply_markup=address_list_keyboard(addresses)
        )
        await source.answer()
    except TelegramBadRequest:
        await source.message.reply(
            text="Список ваших адрес:", reply_markup=address_list_keyboard(addresses)
        )
