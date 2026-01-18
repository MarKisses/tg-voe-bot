from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    InlineKeyboardMarkup,
)
from logger import create_logger
from storage import user_storage

logger = create_logger(__name__)


async def show_service_menu(
    bot: Bot | None,
    chat_id: int,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
    old_msg_id: int | None = None,
):
    if bot is None:
        return False

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
            logger.info(f"Service message {msg_id} not found in chat {chat_id}")
            return False

        logger.error(f"Failed to edit service message {msg_id} for chat {chat_id}: {e}")
        return False

    except Exception:
        logger.exception(
            f"Unexpected error while editing service message "
            f"{msg_id} for chat {chat_id}"
        )
        return False


async def replace_service_menu(
    bot: Bot | None,
    chat_id: int,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
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
        disable_notification=True,
    )
    await user_storage.set_service_msg(chat_id, msg.message_id)
    return msg.message_id
