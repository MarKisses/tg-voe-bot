from aiogram import Router, F
from bot.menus.address_list import show_address_list
from aiogram.types import CallbackQuery

router = Router(name=__name__)


@router.callback_query(lambda c: c.data.startswith("go:"))
async def go_callback(callback: CallbackQuery):
    _, action = callback.data.split(":", 1)
    if action == "address_list":
        await show_address_list(callback)
    await callback.answer()