from aiogram.types import Message, CallbackQuery

from bot.keyboards import main_menu_keyboard

async def show_main(source):
    if isinstance(source, CallbackQuery):
        await source.message.edit_text(
            text="Головне меню:", reply_markup=main_menu_keyboard()
        )
        await source.answer()
        return
    
    await source.answer(
        text="Головне меню:", reply_markup=main_menu_keyboard()
    )
