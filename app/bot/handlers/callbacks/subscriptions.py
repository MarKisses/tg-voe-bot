from logging import getLogger

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from storage import subscription_storage, user_storage

from bot.keyboards.subcriptions import build_subscription_menu

logger = getLogger(__name__)

router = Router(name=__name__)

async def _get_subscription_status(
    user_id: int, addr_id: str
) -> dict[str, bool]:
    return {
        "today": user_id in await subscription_storage.get_subscribers(addr_id, "today"),
        "tomorrow": user_id in await subscription_storage.get_subscribers(addr_id, "tomorrow"),
    }


@router.callback_query(lambda c: c.data.startswith("subscriptions:"))
async def subscriptions_callback(callback: CallbackQuery, state: FSMContext):
    logger.info(
        f"User {callback.from_user.id} opened subscriptions for address: {callback.data}"
    )
    _, addr_id = callback.data.split(":", 1)

    address = await user_storage.get_address_by_id(callback.from_user.id, addr_id)
    
    user_id = callback.from_user.id
    data = await _get_subscription_status(user_id, addr_id)
    
    
    if not address:
        await callback.message.edit_text(
            "Вибрана адреса не знайдена. Спробуйте ще раз."
        )
        return

    await callback.message.edit_text(
        text=f"{address.name}", reply_markup=build_subscription_menu(address.id, data=data)
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("sub:"))
async def toggle_subscription(callback: CallbackQuery, state: FSMContext):
    logger.info(
        f"User {callback.from_user.id} toggled subscription for address: {callback.data}"
    )
    """
    Подписка/отписка по конкретному типу.
    data: sub:{kind}:{addr_id}
    """
    _, kind, addr_id = callback.data.split(":", 2)
    user_id = callback.from_user.id

    # Проверяем, подписан ли уже
    current = await subscription_storage.get_subscribers(addr_id, kind)  # type: ignore[arg-type]

    if user_id in current:
        await subscription_storage.remove_subscription(user_id, addr_id, kind)  # type: ignore[arg-type]
        text = (
            "✅ Ви відписались від сповіщень "
            f"({'сьогодні' if kind == 'today' else 'на завтра'})."
        )
    else:
        await subscription_storage.add_subscription(user_id, addr_id, kind)  # type: ignore[arg-type]
        text = (
            "✅ Ви підписались на сповіщення "
            f"({'про зміни сьогодні' if kind == 'today' else 'про графік на завтра'})."
        )
        
    data = await _get_subscription_status(user_id, addr_id)

    await callback.answer(text, show_alert=True)

    # Можем просто обновить то же меню
    await callback.message.edit_reply_markup(
        reply_markup=build_subscription_menu(addr_id, data=data),
    )
