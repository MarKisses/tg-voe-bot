from datetime import datetime, timedelta

from aiogram import Router
from aiogram.enums import ChatAction
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery
from aiogram.utils.chat_action import ChatActionSender
from bot.keyboards.address_list import (
    address_list_keyboard,
    day_list_keyboard,
    full_address_keyboard,
)
from bot.states.address_state import AddressState
from bot.utils import tg_sem_replace_service_menu, tg_sem_show_service_menu, tg_sem_send_photo
from config import settings
from exceptions import VoeDownException
from logger import create_logger
from services import fetch_schedule, parse_schedule, render_schedule_image
from services.models import Address, City, House, ScheduleResponse, Street
from storage import subscription_storage, user_storage

logger = create_logger(__name__)

router = Router(name=__name__)


@router.callback_query(lambda c: c.data.startswith("city:"))
async def city_callback(callback: CallbackQuery, state: FSMContext):
    if callback.bot is None:
        return

    logger.info(f"User {callback.from_user.id} selected city: {callback.data}")
    _, city = callback.data.split(":", 1)

    await state.update_data(
        msg_id=callback.message.message_id, chat_id=callback.message.chat.id
    )
    if city == "vinnytsia":
        city = City(id=510100000, name="м. Вінниця")
        await state.update_data(chosen_city=city.model_dump())
        await state.set_state(AddressState.choosing_street)
        return await tg_sem_show_service_menu(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            text="Введіть назву вулиці",
            old_msg_id=callback.message.message_id,
        )
    await state.set_state(AddressState.choosing_city)
    return await tg_sem_show_service_menu(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        text="Введіть назву міста",
        old_msg_id=callback.message.message_id,
    )


@router.callback_query(lambda c: c.data.startswith("city_select:"))
async def city_select_callback(callback: CallbackQuery, state: FSMContext):
    if callback.bot is None:
        return

    logger.info(f"User {callback.from_user.id} selected city: {callback.data}")
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
        return await tg_sem_show_service_menu(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            text="Вибране місто не знайдено. Спробуйте ще раз.",
            old_msg_id=callback.message.message_id,
        )
    await state.update_data(chosen_city=city.model_dump())
    await state.set_state(AddressState.choosing_street)
    await state.update_data(
        msg_id=callback.message.message_id, chat_id=callback.message.chat.id
    )
    return await tg_sem_show_service_menu(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        text="Введіть назву вулиці",
        old_msg_id=callback.message.message_id,
    )


@router.callback_query(lambda c: c.data.startswith("street_select:"))
async def street_select_callback(callback: CallbackQuery, state: FSMContext):
    if callback.bot is None:
        return

    logger.info(f"User {callback.from_user.id} selected street: {callback.data}")
    _, street_id = callback.data.split(":", 1)
    street_id = int(street_id)
    data = await state.get_data()
    streets_data = data.get("streets", [])
    street = next(
        (Street.model_validate(st) for st in streets_data if st["id"] == street_id),
        None,
    )
    if not street:
        return await tg_sem_show_service_menu(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            text="Вибрану вулицю не знайдено. Спробуйте ще раз.",
            old_msg_id=callback.message.message_id,
        )
    await state.update_data(chosen_street=street.model_dump())
    await state.update_data(
        msg_id=callback.message.message_id, chat_id=callback.message.chat.id
    )
    await state.set_state(AddressState.choosing_house)
    return await tg_sem_show_service_menu(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        text="Введіть номер будинку",
        old_msg_id=callback.message.message_id,
    )


@router.callback_query(lambda c: c.data.startswith("house_select:"))
async def house_select_callback(callback: CallbackQuery, state: FSMContext):
    if callback.bot is None:
        return

    logger.info(f"User {callback.from_user.id} selected house: {callback.data}")
    _, house_id = callback.data.split(":", 1)
    house_id = int(house_id)
    data = await state.get_data()
    houses_data = data.get("houses", [])
    house = next(
        (House.model_validate(hs) for hs in houses_data if hs["id"] == house_id),
        None,
    )
    if not house:
        return await tg_sem_show_service_menu(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            text="Вибраний будинок не знайдено. Спробуйте ще раз.",
            old_msg_id=callback.message.message_id,
        )
    await state.update_data(chosen_house=house.model_dump())
    await state.update_data(
        msg_id=callback.message.message_id, chat_id=callback.message.chat.id
    )

    city = City.model_validate(data.get("chosen_city"))
    street = Street.model_validate(data.get("chosen_street"))

    address = Address(city=city, street=street, house=house)
    await user_storage.add_address(callback.from_user.id, address)

    await state.clear()
    return await tg_sem_show_service_menu(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        text=f"{address.name}",
        reply_markup=address_list_keyboard([address]),
        old_msg_id=callback.message.message_id,
    )


@router.callback_query(lambda c: c.data.startswith("select_address:"))
async def address_menu_callback(callback: CallbackQuery, state: FSMContext):
    if callback.bot is None:
        return

    logger.info(f"User {callback.from_user.id} selected address: {callback.data}")
    _, address_id = callback.data.split(":", 1)
    address = await user_storage.get_address_by_id(callback.from_user.id, address_id)
    if not address:
        return await tg_sem_show_service_menu(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            text="Вибрана адреса не знайдено. Спробуйте ще раз.",
            old_msg_id=callback.message.message_id,
        )

    return await tg_sem_show_service_menu(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        text=f"{address.name}",
        reply_markup=full_address_keyboard(address.id),
        old_msg_id=callback.message.message_id,
    )


@router.callback_query(lambda c: c.data.startswith("schedule:"))
async def select_address_callback(callback: CallbackQuery, state: FSMContext):
    if callback.bot is None:
        return

    logger.info(f"User {callback.from_user.id} selected address: {callback.data}")
    _, address_id = callback.data.split(":", 1)
    address = await user_storage.get_address_by_id(callback.from_user.id, address_id)
    if not address:
        return await tg_sem_show_service_menu(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            text="Вибрана адреса не знайдена. Спробуйте ще раз.",
            old_msg_id=callback.message.message_id,
        )

    async with ChatActionSender(
        bot=callback.bot, chat_id=callback.message.chat.id, action=ChatAction.TYPING
    ):
        await tg_sem_show_service_menu(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            text=settings.messages_loading.loading_schedule,
            old_msg_id=callback.message.message_id,
        )

        try:
            raw = await fetch_schedule(
                address.city.id, address.street.id, address.house.id
            )
        except VoeDownException:
            return await tg_sem_show_service_menu(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                text="VOE впав 😢",
                reply_markup=full_address_keyboard(address_id),
                old_msg_id=callback.message.message_id,
            )

        parsed = parse_schedule(raw, address.name, max_days=2)

        if not parsed.disconnections:
            return await tg_sem_show_service_menu(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                text=f"Графік відключень для {address.name} відсутній.",
                reply_markup=full_address_keyboard(address_id),
                old_msg_id=callback.message.message_id,
            )

    await user_storage.set_cached_schedule(address.id, parsed.model_dump(), ttl=600)

    await tg_sem_show_service_menu(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        text=f"{address.name}",
        reply_markup=day_list_keyboard(address.id),
        old_msg_id=callback.message.message_id,
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("day_select:"))
async def day_select_callback(callback: CallbackQuery, state: FSMContext):
    if callback.bot is None:
        return

    logger.info(f"User {callback.from_user.id} selected day: {callback.data}")
    _, day_offset, addr_id = callback.data.split(":", 2)
    day_offset = int(day_offset)
    date = (datetime.now() + timedelta(days=day_offset)).date().isoformat()

    schedule_data = await user_storage.get_cached_schedule(addr_id)

    if not schedule_data:
        return await tg_sem_show_service_menu(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            text="Графік відключень не знайдено в кеші. Будь ласка, завантажте його знову.",
            reply_markup=full_address_keyboard(addr_id),
            old_msg_id=callback.message.message_id,
        )

    schedule = ScheduleResponse.model_validate(schedule_data)

    async with ChatActionSender(
        bot=callback.bot, chat_id=callback.message.chat.id, action=ChatAction.TYPING
    ):
        await tg_sem_show_service_menu(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            text=settings.messages_loading.loading_schedule,
            old_msg_id=callback.message.message_id,
        )

        logger.debug(schedule)
        day = schedule.get_day_schedule(date)

        if not day:
            return await tg_sem_show_service_menu(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                text=f"На цей день графік відключень для {schedule.address} поки недоступний.",
                reply_markup=day_list_keyboard(addr_id),
            )

        if not day.has_disconnections:
            return await tg_sem_show_service_menu(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                text=f"Відключень для {schedule.address} на цей день немає.",
                reply_markup=day_list_keyboard(addr_id),
            )

        buffered_file = BufferedInputFile(
            render_schedule_image(
                day=day,
                queue=schedule.disconnection_queue,
                date=date,
                address=schedule.address,
            ).getvalue(),
            filename="schedule.png",
        )

        await tg_sem_send_photo(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            photo=buffered_file,
        )

        return await tg_sem_replace_service_menu(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            text=f"{schedule.address}",
            reply_markup=day_list_keyboard(addr_id),
        )


@router.callback_query(lambda c: c.data.startswith("delete_address:"))
async def delete_address_callback(callback: CallbackQuery, state: FSMContext):
    if callback.bot is None:
        return

    logger.info(
        f"User {callback.from_user.id} requested to delete address: {callback.data}"
    )
    _, address_id = callback.data.split(":", 1)
    address = await user_storage.get_address_by_id(callback.from_user.id, address_id)
    if not address:
        return await tg_sem_show_service_menu(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            text="Вибрана адреса не знайдена. Спробуйте ще раз.",
            old_msg_id=callback.message.message_id,
        )

    await user_storage.remove_address(callback.from_user.id, address_id)
    await subscription_storage.remove_subscription(
        callback.from_user.id, address_id, "today"
    )
    await subscription_storage.remove_subscription(
        callback.from_user.id, address_id, "tomorrow"
    )

    addresses = await user_storage.get_addresses(callback.from_user.id)
    if not addresses:
        return await tg_sem_show_service_menu(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            text="У вас немає збережених адрес.",
            reply_markup=address_list_keyboard(None),
            old_msg_id=callback.message.message_id,
        )

    return await tg_sem_show_service_menu(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        text="Список ваших адрес:",
        reply_markup=address_list_keyboard(addresses),
        old_msg_id=callback.message.message_id,
    )
