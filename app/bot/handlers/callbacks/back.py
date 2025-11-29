from aiogram import Router, F
from bot.menus.main import show_main
from aiogram.types import CallbackQuery
from bot.menus.address_list import show_address_list
from bot.menus.main import show_main

router = Router(name=__name__)


@router.callback_query(lambda c: c.data.startswith("back:"))
async def back_callback(callback: CallbackQuery):
    _, action = callback.data.split(":", 1)
    if action == "main_menu":
        await show_main(callback)
    if action == "address_list":
        await show_address_list(callback)

    await callback.answer()
