from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.states.AddressState import AddressState
from bot.keyboards.city_choose import choose_city_keyboard
from services import fetch_schedule


async def ask_city(source: CallbackQuery, state: FSMContext):
    await source.message.edit_text(
        text="Введіть назву міста", reply_markup=choose_city_keyboard()
    )

async def ask_street(source: CallbackQuery, state: FSMContext):
    await state.set_state(AddressState.choosing_street)
    await source.message.edit_text(
        text="Введіть назву вулиці"
    )
    
async def schedule_info(source: CallbackQuery, state: FSMContext):
    ...