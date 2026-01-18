from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.states.AddressState import AddressState
from bot.keyboards.city_choose import choose_city_keyboard
from services import fetch_schedule
from bot.utils import tg_sem_show_service_menu


async def ask_city(source: CallbackQuery, state: FSMContext):
    return await tg_sem_show_service_menu(
        bot=source.bot,
        chat_id=source.message.chat.id,
        text="Введіть назву міста",
        reply_markup=choose_city_keyboard(),
        old_msg_id=source.message.message_id,
    )

async def ask_street(source: CallbackQuery, state: FSMContext):
    await state.set_state(AddressState.choosing_street)
    
    return await tg_sem_show_service_menu(
        bot=source.bot,
        chat_id=source.message.chat.id,
        text="Введіть назву вулиці",
        old_msg_id=source.message.message_id,
    )
