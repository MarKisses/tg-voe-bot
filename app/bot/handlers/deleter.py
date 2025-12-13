from aiogram import Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from logger import create_logger

logger = create_logger(__name__)

router = Router(name=__name__)


@router.message()
async def delete_dangling_message(message: types.Message, state: FSMContext):
    """
    Handler to delete any message that does not correspond to the current state.
    This helps keep the chat clean from irrelevant messages.
    """
    current_state = await state.get_state()
    if current_state is None:
        try:
            await message.delete()
            logger.info(f"Deleted dangling message from user {message.from_user.id}.")
        except TelegramBadRequest as e:
            logger.warning(
                f"Failed to delete message from user {message.from_user.id}: {e}"
            )
