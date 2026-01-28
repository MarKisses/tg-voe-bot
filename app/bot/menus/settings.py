from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

from bot.keyboards.settings import settings_keyboard
from bot.utils import tg_sem_show_service_menu
from storage import user_storage


async def show_settings(source: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = source.from_user.id

    render_text_flag = await user_storage.is_render_text_enabled(user_id)

    return await tg_sem_show_service_menu(
        bot=source.bot,
        chat_id=source.message.chat.id,
        text="Ваші налаштування:",
        reply_markup=settings_keyboard(render_text_flag, user_id)
    )