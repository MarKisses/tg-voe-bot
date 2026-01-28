from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Мої адреси", callback_data="go:address_list")
    kb.button(text="Налаштування", callback_data="go:settings")
    kb.button(text="Інформація про бота", callback_data="go:bot_info")
    kb.button(text="Допомога", callback_data="go:help")
    kb.adjust(1)
    return kb.as_markup()

def back_to_main_menu_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Назад до головного меню", callback_data="back:main_menu")
    return kb.as_markup()