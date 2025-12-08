from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InaccessibleMessage, Message



async def edit_message_with_fallback(
    source: Message | CallbackQuery, text: str, reply_markup=None
):
    msg: Message

    if isinstance(source, CallbackQuery):
        assert source.message is not None
        if isinstance(source.message, InaccessibleMessage):
            return
        msg = source.message
    else:
        msg = source

    try:
        await msg.edit_text(text=text, reply_markup=reply_markup)
    except TelegramBadRequest:
        await msg.reply(text=text, reply_markup=reply_markup)
