import asyncio

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup
from config import settings

from .message_editor import replace_service_menu, show_service_menu

TG_SEMAPHORE = asyncio.Semaphore(settings.rate_limit_sem)


async def tg_sem_send_photo(bot: Bot, **kwargs):
    async with TG_SEMAPHORE:
        return await bot.send_photo(**kwargs)


async def tg_sem_show_service_menu(
    bot: Bot | None,
    chat_id: int,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
    old_msg_id: int | None = None,
):
    async with TG_SEMAPHORE:
        return await show_service_menu(
            bot=bot,
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            old_msg_id=old_msg_id,
        )


async def tg_sem_replace_service_menu(
    bot: Bot | None,
    chat_id: int,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
):
    async with TG_SEMAPHORE:
        return await replace_service_menu(
            bot=bot,
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
        )
