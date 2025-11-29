from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def choose_city_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Вінниця", callback_data="city:vinnytsia"), InlineKeyboardButton(text="Інше місто", callback_data="city:other"))
    kb.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="back:address_list"),
    )
    return kb.as_markup()