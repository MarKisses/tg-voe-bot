from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.menus.about import show_info
from bot.menus.address_flow.address import ask_city
from bot.menus.address_list import show_address_list
from bot.menus.settings import show_settings

router = Router(name=__name__)


@router.callback_query(lambda c: c.data.startswith("go:"))
async def go_callback(callback: CallbackQuery, state: FSMContext):
    if not callback.data:
        return

    _, action = callback.data.split(":", 1)

    if action == "address_list":
        await show_address_list(callback, state)

    if action == "add_address":
        await ask_city(callback, state)

    if action == "bot_info":
        await show_info(callback)

    if action == "settings":
        await show_settings(callback, state)
    await callback.answer()
