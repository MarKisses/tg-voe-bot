from aiogram import Router
from bot.states.AddressState import AddressState
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from services.models import City, Street, House, Address, ScheduleResponse
from services import fetch_schedule, parse_schedule, render_schedule_image
from storage import user_storage
from bot.keyboards.address_list import address_list_keyboard, day_list_keyboard
from aiogram.types import BufferedInputFile, InputMediaPhoto

router = Router(name=__name__)


@router.callback_query(lambda c: c.data.startswith("city:"))
async def city_callback(callback: CallbackQuery, state: FSMContext):
    _, city = callback.data.split(":", 1)
    await state.update_data(
        msg_id=callback.message.message_id, chat_id=callback.message.chat.id
    )
    if city == "vinnytsia":
        city = City(id=510100000, name="м. Вінниця")
        await state.update_data(chosen_city=city.model_dump())
        await state.set_state(AddressState.choosing_street)
        await callback.message.edit_text(text="Введіть назву вулиці")
        return callback.answer()
    await state.set_state(AddressState.choosing_city)
    await callback.message.edit_text(text="Введіть назву міста")
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("city_select:"))
async def city_select_callback(callback: CallbackQuery, state: FSMContext):
    _, city_id = callback.data.split(":", 1)
    city_id = int(city_id)
    data = await state.get_data()
    cities_data = data.get("cities", [])
    city = next(
        (City.model_validate(cd) for cd in cities_data if cd["id"] == city_id), None
    )
    await state.update_data(
        msg_id=callback.message.message_id, chat_id=callback.message.chat.id
    )
    if not city:
        await callback.message.edit_text("Вибране місто не знайдено. Спробуйте ще раз.")
        return
    await state.update_data(chosen_city=city.model_dump())
    await state.set_state(AddressState.choosing_street)
    await state.update_data(
        msg_id=callback.message.message_id, chat_id=callback.message.chat.id
    )
    await callback.message.edit_text(text="Введіть назву вулиці")
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("street_select:"))
async def street_select_callback(callback: CallbackQuery, state: FSMContext):
    _, street_id = callback.data.split(":", 1)
    street_id = int(street_id)
    data = await state.get_data()
    streets_data = data.get("streets", [])
    street = next(
        (Street.model_validate(st) for st in streets_data if st["id"] == street_id),
        None,
    )
    if not street:
        await callback.message.edit_text(
            "Вибрана вулиця не знайдена. Спробуйте ще раз."
        )
        return
    await state.update_data(chosen_street=street.model_dump())
    await state.update_data(
        msg_id=callback.message.message_id, chat_id=callback.message.chat.id
    )
    await state.set_state(AddressState.choosing_house)
    await callback.message.edit_text(text="Введіть номер будинку")
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("house_select:"))
async def house_select_callback(callback: CallbackQuery, state: FSMContext):
    _, house_id = callback.data.split(":", 1)
    house_id = int(house_id)
    data = await state.get_data()
    houses_data = data.get("houses", [])
    house = next(
        (House.model_validate(hs) for hs in houses_data if hs["id"] == house_id),
        None,
    )
    if not house:
        await callback.message.edit_text(
            "Вибраний будинок не знайдено. Спробуйте ще раз."
        )
        return
    await state.update_data(chosen_house=house.model_dump())
    await state.update_data(
        msg_id=callback.message.message_id, chat_id=callback.message.chat.id
    )
    
    city = City.model_validate(data.get("chosen_city"))
    street = Street.model_validate(data.get("chosen_street"))

    address = Address(city=city, street=street, house=house)
    await user_storage.add_address(callback.from_user.id, address)

    await callback.message.edit_text(
        text=f"{address.name}", reply_markup=day_list_keyboard(addr_id=address.id)
    )
    await callback.answer()
    
    
    
@router.callback_query(lambda c: c.data.startswith("select_address:"))
async def select_address_callback(callback: CallbackQuery, state: FSMContext):
    _, address_id = callback.data.split(":", 1)
    address = await user_storage.get_address_by_id(callback.from_user.id, address_id)
    if not address:
        await callback.message.edit_text(
            "Вибрана адреса не знайдена. Спробуйте ще раз."
        )
        return
    
    raw = await fetch_schedule(address.city.id, address.street.id, address.house.id)
    parsed = parse_schedule(raw, address.name, max_days=2)

    await user_storage.set_cached_schedule(address.id, parsed.model_dump())

    await callback.message.edit_text(
        text=f"{address.name}", reply_markup=day_list_keyboard(address.id)
    )
    await callback.answer()
    
@router.callback_query(lambda c: c.data.startswith("day_select:"))
async def day_select_callback(callback: CallbackQuery, state: FSMContext):
    _, day_offset, addr_id = callback.data.split(":", 2)
    day_offset = int(day_offset)

    schedule_data = await user_storage.get_cached_schedule(addr_id)
    schedule = ScheduleResponse.model_validate(schedule_data)

    buffered_file = BufferedInputFile(render_schedule_image(
        day=schedule.disconnections[day_offset],
        queue=schedule.disconnection_queue,
        date=schedule.disconnections[day_offset].date,
        address=schedule.address,
    ).getvalue(), filename="schedule.png")
    
    new_media = InputMediaPhoto(media=buffered_file)

    await callback.message.edit_media(text=text, media=new_media, reply_markup=day_list_keyboard(addr_id))
