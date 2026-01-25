from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def build_subscription_menu(
    addr_id: str, data: dict[str, bool]
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="❌ Відписатися від змін на сьогодні"
        if data["today"]
        else "🔔 Підписатися на зміни на сьогодні",
        callback_data=f"sub:today:{addr_id}",
    )
    kb.button(
        text="❌ Відписатися від графіка на завтра"
        if data["tomorrow"]
        else "📆 Підписатися на графік на завтра",
        callback_data=f"sub:tomorrow:{addr_id}",
    )
    kb.button(
        text="⬅ Назад",
        callback_data=f"select_address:{addr_id}",
    )
    kb.adjust(1)
    return kb.as_markup()
