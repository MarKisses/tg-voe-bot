from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    CallbackQuery,
    InaccessibleMessage,
    InlineKeyboardMarkup,
    Message,
)
from logger import create_logger
from storage import user_storage

logger = create_logger(__name__)


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


async def show_service_menu(
    bot: Bot,
    chat_id: int,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
    old_msg_id: int | None = None,
):
    msg_id = await user_storage.get_service_msg(chat_id)

    if not msg_id and old_msg_id:
        msg_id = old_msg_id
        await user_storage.set_service_msg(chat_id, msg_id)
        
    if not msg_id:
        return False

    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=int(msg_id),
            text=text,
            reply_markup=reply_markup,
        )
        return True
    except TelegramBadRequest as e:
        msg = str(e)

        if "message is not modified" in msg:
            return True

        if "message to edit not found" in msg:
            logger.info(
                f"Service message {msg_id} not found in chat {chat_id}"
            )
            return False

        logger.error(
            f"Failed to edit service message {msg_id} "
            f"for chat {chat_id}: {e}"
        )
        return False

    except Exception as e:
        logger.exception(
            f"Unexpected error while editing service message "
            f"{msg_id} for chat {chat_id}"
        )
        return False

async def send_new_service_menu(
    bot: Bot,
    chat_id: int,
    text: str,
    reply_markup: InlineKeyboardMarkup,
) -> int:
    msg = await bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup,
    )
    await user_storage.set_service_msg(chat_id, msg.message_id)
    return msg.message_id

async def replace_service_menu(
    bot: Bot,
    chat_id: int,
    text: str,
    reply_markup: InlineKeyboardMarkup,
) -> int:
    msg_id = await user_storage.get_service_msg(chat_id)

    if msg_id:
        try:
            await bot.delete_message(chat_id, int(msg_id))
        except TelegramBadRequest as e:
            logger.warning(
                f"Failed to delete service message {msg_id} for chat {chat_id}: {e}"
            )
        except Exception:
            logger.exception(
                f"Unexpected error while deleting service message "
                f"{msg_id} for chat {chat_id}"
            )

    msg = await bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup,
    )
    await user_storage.set_service_msg(chat_id, msg.message_id)
    return msg.message_id