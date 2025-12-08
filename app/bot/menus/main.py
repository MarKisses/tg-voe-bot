from aiogram.exceptions import TelegramBadRequest

from bot.keyboards import main_menu_keyboard


async def show_main(source):
    try:
        await source.message.edit_text(
            text="Головне меню бота:", reply_markup=main_menu_keyboard()
        )
    except TelegramBadRequest:
        await source.message.reply(
            text="Головне меню бота:", reply_markup=main_menu_keyboard()
        )
