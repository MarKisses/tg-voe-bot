from aiogram import Router, F
from bot.menus.address_list import show_address_list
from bot.menus.address_flow.address import ask_city
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.states.AddressState import AddressState


router = Router(name=__name__)


@router.callback_query(lambda c: c.data.startswith("go:"))
async def go_callback(callback: CallbackQuery, state: FSMContext):
    _, action = callback.data.split(":", 1)
    
    if action == "address_list":
        await show_address_list(callback)
        
    if action == "add_address":
        await ask_city(callback, state)
    await callback.answer()