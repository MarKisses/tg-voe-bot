from aiogram import Router
from aiogram.filters.command import Command
from aiogram import types
from aiogram.fsm.context import FSMContext

from bot.menus import show_main

router = Router(name=__name__)

@router.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await show_main(message)