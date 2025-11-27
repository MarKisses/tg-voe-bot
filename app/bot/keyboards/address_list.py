from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from services.models import Address


def address_list_keyboard(addresses: list[Address] | None) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="⬅️", callback_data="back:main_menu"),
        InlineKeyboardButton(
            text="🏠", callback_data="back:main_menu"
        ),
    )
    if addresses:
        for address in addresses:
            kb.button(
                text=f"🏠 {address.city.name}, {address.street.name}, {address.house.name}",
                callback_data=f"select_address:{address.id}",
            )
    kb.row(InlineKeyboardButton(text="➕ Додати нову адресу", callback_data="add_address"))
    return kb.as_markup()
