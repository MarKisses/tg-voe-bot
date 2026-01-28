from logging import getLogger

from aiogram import Router
from aiogram.filters import callback_data
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InaccessibleMessage

from bot.menus.settings import show_settings
from storage import subscription_storage, user_storage

from bot.keyboards import build_subscription_menu
from bot.utils import tg_sem_show_service_menu

logger = getLogger(__name__)

router = Router(name=__name__)

@router.callback_query(lambda c: c.data.startswith("settings:"))
async def toggle_render_flag(callback: CallbackQuery, state: FSMContext):
    if not callback.data:
        return await callback.answer()

    logger.info(f"User toggled render flag: {callback.data}")

    _, render_flag, user_id = callback.data.split(":", 2)
    render_flag = int(render_flag)
    user_id = int(user_id)

    logger.info(f"{_}, render_flag: {render_flag}, user_id: {user_id}")

    if render_flag:
        await user_storage.disable_render_text(user_id)
        await callback.answer(
            text="Активовано графіки у вигляді зображень",
            show_alert=True,
        )
        return await show_settings(callback, state)

    await user_storage.enable_render_text(user_id)
    await callback.answer(
        text="Активовано графіки у вигляді тексту",
        show_alert=True,
    )
    return await show_settings(callback, state)