from aiogram import Router
from aiogram.types import CallbackQuery

from bot.keyboards.main_menu import main_menu_keyboard
from bot.menus.address_list import show_address_list
from bot.utils import edit_message_with_fallback
from aiogram.fsm.context import FSMContext

router = Router(name=__name__)


@router.callback_query(lambda c: c.data.startswith("back:"))
async def back_callback(callback: CallbackQuery, state: FSMContext):
    if not callback.data:
        return

    _, action = callback.data.split(":", 1)

    if action == "main_menu":
        await edit_message_with_fallback(
            callback, text="Головне меню бота:", reply_markup=main_menu_keyboard()
        )
    if action == "address_list":
        await show_address_list(callback, state)

    await callback.answer()
