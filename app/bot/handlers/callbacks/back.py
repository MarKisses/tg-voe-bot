from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from bot.keyboards.main_menu import main_menu_keyboard
from bot.menus.address_list import show_address_list
from bot.utils import show_service_menu

router = Router(name=__name__)


@router.callback_query(lambda c: c.data.startswith("back:"))
async def back_callback(callback: CallbackQuery, state: FSMContext):
    if not callback.data:
        return

    _, action = callback.data.split(":", 1)

    if action == "main_menu":
        await show_service_menu(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            text="Головне меню бота:",
            reply_markup=main_menu_keyboard(),
            old_msg_id=callback.message.message_id,
        )
    if action == "address_list":
        await show_address_list(callback, state)

    await callback.answer()
