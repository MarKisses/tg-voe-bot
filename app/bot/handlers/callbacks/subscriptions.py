from logging import getLogger

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InaccessibleMessage
from storage import subscription_storage, user_storage

from bot.keyboards.subcriptions import build_subscription_menu
from bot.utils.message_editor import edit_message_with_fallback

logger = getLogger(__name__)

router = Router(name=__name__)


@router.callback_query(lambda c: c.data.startswith("subscriptions:"))
async def subscriptions_callback(callback: CallbackQuery, state: FSMContext):
    if not callback.data:
        return

    logger.info(
        f"User {callback.from_user.id} opened subscriptions for address: {callback.data}"
    )
    _, addr_id = callback.data.split(":", 1)

    address = await user_storage.get_address_by_id(callback.from_user.id, addr_id)

    user_id = callback.from_user.id
    data = await subscription_storage.get_subscription_status(user_id, addr_id)

    if not address:
        await edit_message_with_fallback(
            callback, text="Вибрана адреса не знайдена. Спробуйте ще раз."
        )
        return

    await edit_message_with_fallback(
        callback,
        text=f"{address.name}",
        reply_markup=build_subscription_menu(address.id, data=data),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("sub:"))
async def toggle_subscription(callback: CallbackQuery, state: FSMContext):
    if (
        not callback.data
        or not callback.message
        or isinstance(callback.message, InaccessibleMessage)
    ):
        return

    logger.info(
        f"User {callback.from_user.id} toggled subscription for address: {callback.data}"
    )
    """
    Подписка/отписка по конкретному типу.
    data: sub:{kind}:{addr_id}
    """
    _, kind, addr_id = callback.data.split(":", 2)
    user_id = callback.from_user.id
    if kind in ("today", "tomorrow"):
        kind = kind
    else:
        await callback.answer("Невідомий тип підписки.", show_alert=True)
        return

    status, text = await subscription_storage.toggle_subscription(
        user_id, addr_id, kind
    )
    data = await subscription_storage.get_subscription_status(user_id, addr_id)

    await callback.answer(text, show_alert=True)

    # Можем просто обновить то же меню

    await callback.message.edit_reply_markup(
        reply_markup=build_subscription_menu(addr_id, data=data),
    )
