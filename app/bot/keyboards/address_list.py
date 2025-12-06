from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from services.models import Address, City, Street, House


def address_list_keyboard(addresses: list[Address] | None) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="⬅️", callback_data="back:main_menu"),
        InlineKeyboardButton(text="🏠", callback_data="back:main_menu"),
    )
    if addresses:
        for address in addresses:
            kb.row(
                InlineKeyboardButton(
                    text=f"{address.name}",
                    callback_data=f"select_address:{address.id}",
                )
            )
    kb.row(
        InlineKeyboardButton(
            text="➕ Додати нову адресу", callback_data="go:add_address"
        )
    )
    return kb.as_markup()


def cities_list_keyboard(cities: list[City]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for city in cities:
        kb.button(
            text=f"{city.name}",
            callback_data=f"city_select:{city.id}",
        )
    kb.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back:address_list"))
    return kb.as_markup()


def streets_list_keyboard(streets: list[Street]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for street in streets:
        kb.button(
            text=f"{street.name}",
            callback_data=f"street_select:{street.id}",
        )
    kb.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back:address_list"))
    return kb.as_markup()


def houses_list_keyboard(houses: list[House]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for house in houses:
        kb.button(
            text=f"{house.name}",
            callback_data=f"house_select:{house.id}",
        )
    kb.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back:address_list"))
    return kb.as_markup()


def full_address_keyboard(addr_id: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(
            text="Графік відключень", callback_data=f"schedule:{addr_id}"
        )
    )
    kb.row(
        InlineKeyboardButton(
            text="Сповіщення 🔔",
            callback_data=f"subscriptions:{addr_id}",
        )
    )
    kb.row(InlineKeyboardButton(text="Видалити адресу ❌", callback_data=f"delete_address:{addr_id}"))
    kb.row(InlineKeyboardButton(text="⬅️", callback_data="back:address_list"))
    return kb.as_markup()


def day_list_keyboard(addr_id: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="⬅️", callback_data="back:address_list"),
        InlineKeyboardButton(text="🏠", callback_data="back:main_menu"),
    )
    kb.row(
        InlineKeyboardButton(text="Сьогодні", callback_data=f"day_select:0:{addr_id}")
    )
    kb.row(InlineKeyboardButton(text="Завтра", callback_data=f"day_select:1:{addr_id}"))
    return kb.as_markup()
