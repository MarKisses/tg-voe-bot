from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def settings_keyboard(
        render_flag: bool,
        user_id: int
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="Надсилати графіки у текстовому форматі ✍"
        if not render_flag
        else "Надсилати графіки у вигляді зображень 🖼️",
        callback_data=f"settings:{int(render_flag)}:{user_id}",
    )
    kb.button(text="⬅️ Назад до головного меню", callback_data="back:main_menu")
    kb.adjust(1)
    return kb.as_markup()
