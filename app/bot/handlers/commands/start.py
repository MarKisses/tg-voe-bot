from aiogram import Router
from aiogram.filters.command import Command
from aiogram import types
from aiogram.fsm.context import FSMContext
import logging

from bot.menus import show_main

router = Router(name=__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    logger.info(f"User {message.from_user.id} initiated start command.")
    await show_main(message)