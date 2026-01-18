import logging

from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.chat_action import ChatActionSender
from bot.keyboards import back_to_main_menu_keyboard
from bot.keyboards.address_list import (
    cities_list_keyboard,
    houses_list_keyboard,
    streets_list_keyboard,
)
from bot.states.AddressState import AddressState
from bot.utils import tg_sem_show_service_menu
from config import settings
from exceptions import VoeDownException
from services.fetcher import fetch_cities, fetch_houses, fetch_streets
from services.models import City, House, Street

logger = logging.getLogger(__name__)

router = Router(name=__name__)


@router.message(AddressState.choosing_city, F.text)
async def choose_city_handler(message: Message, state: FSMContext):
    bot = message.bot
    await message.delete()
    city_name = message.text.strip()

    state_data = await state.get_data()
    msg_id, chat_id = state_data.get("msg_id"), state_data.get("chat_id")

    logger.info(f"User {message.from_user.id} is searching for city: {city_name}")
    async with ChatActionSender(bot=bot, chat_id=chat_id, action=ChatAction.TYPING):
        await message.bot.edit_message_text(
            text=settings.messages_loading.loading_city,
            chat_id=chat_id,
            message_id=msg_id,
        )
        try:
            response = await fetch_cities(city_name)
        except VoeDownException:
            return await tg_sem_show_service_menu(
                bot=message.bot,
                chat_id=message.chat.id,
                text="VOE впав 😢. Спробуйте пізніше...",
                reply_markup=back_to_main_menu_keyboard(),
            )

    cities = [City.from_api(data) for data in response]

    await state.update_data(cities=[city.model_dump() for city in cities])
    return await message.bot.edit_message_text(
        text="Оберіть місто зі списку:",
        reply_markup=cities_list_keyboard(cities),
        chat_id=chat_id,
        message_id=msg_id,
    )


@router.message(AddressState.choosing_street)
async def choose_street_handler(message: Message, state: FSMContext):
    await message.delete()
    street_name = message.text.strip()

    data = await state.get_data()
    msg_id, chat_id = data.get("msg_id"), int(data.get("chat_id"))

    chosen_city_data = data.get("chosen_city")
    if not chosen_city_data:
        return await tg_sem_show_service_menu(
            bot=message.bot,
            chat_id=chat_id,
            text="Сталася помилка. Спробуйте ще раз.",
            old_msg_id=msg_id,
            reply_markup=back_to_main_menu_keyboard(),
        )
    chosen_city = City.model_validate(chosen_city_data)

    logger.info(f"User {message.from_user.id} is searching for street: {street_name}")
    async with ChatActionSender(
        bot=message.bot, chat_id=chat_id, action=ChatAction.TYPING
    ):
        await message.bot.edit_message_text(
            text=settings.messages_loading.loading_street,
            chat_id=chat_id,
            message_id=msg_id,
        )

        try:
            response = await fetch_streets(chosen_city.id, street_name)
        except VoeDownException:
            return await tg_sem_show_service_menu(
                bot=message.bot,
                chat_id=chat_id,
                text="VOE впав 😢",
                reply_markup=back_to_main_menu_keyboard(),
            )
    if not response:
        await tg_sem_show_service_menu(
            bot=message.bot,
            chat_id=message.chat.id,
            text="Вулицю не знайдено. Спробуйте ще раз.\n"
            "Введіть виключно назву вулиці без номеру будинку.\n"
            "Перевірте чи існує така вулиця в базі VOE.",
            old_msg_id=msg_id,
            reply_markup=back_to_main_menu_keyboard(),
        )
        return

    streets = [Street.from_api(data) for data in response]
    await state.update_data(streets=[street.model_dump() for street in streets])

    return await tg_sem_show_service_menu(
        bot=message.bot,
        text="Оберіть вулицю зі списку",
        reply_markup=streets_list_keyboard(streets),
        chat_id=chat_id,
        old_msg_id=msg_id,
    )


@router.message(AddressState.choosing_house)
async def choose_house_handler(message: Message, state: FSMContext):
    await message.delete()
    data = await state.get_data()
    house_name = message.text.strip()

    data = await state.get_data()
    msg_id, chat_id = data.get("msg_id"), data.get("chat_id")

    chosen_street_data = data.get("chosen_street")
    if not chosen_street_data:
        return await tg_sem_show_service_menu(
            bot=message.bot,
            chat_id=message.chat.id,
            text="Сталася помилка. Спробуйте ще раз.",
            old_msg_id=chat_id,
            reply_markup=back_to_main_menu_keyboard(),
        )
    chosen_street = Street.model_validate(chosen_street_data)

    logger.info(f"User {message.from_user.id} is searching for house: {house_name}")
    async with ChatActionSender(
        bot=message.bot, chat_id=chat_id, action=ChatAction.TYPING
    ):
        await tg_sem_show_service_menu(
            bot=message.bot,
            text=settings.messages_loading.loading_house,
            chat_id=chat_id,
            old_msg_id=msg_id,
        )
        try:
            response = await fetch_houses(street_id=chosen_street.id, query=house_name)
        except VoeDownException:
            return await tg_sem_show_service_menu(
                bot=message.bot,
                chat_id=chat_id,
                text="VOE впав 😢",
                reply_markup=back_to_main_menu_keyboard(),
            )
    if not response:
        return await tg_sem_show_service_menu(
            bot=message.bot,
            chat_id=message.chat.id,
            text="Будинок не знайдено. Спробуйте ще раз.\n"
            "Перевірте чи існує такий номер будинку в базі VOE.",
            old_msg_id=msg_id,
            reply_markup=back_to_main_menu_keyboard(),
        )

    houses = [House.from_api(h) for h in response]
    await state.update_data(houses=[house.model_dump() for house in houses])

    return await tg_sem_show_service_menu(
        bot=message.bot,
        text="Оберіть будинок зі списку",
        reply_markup=houses_list_keyboard(houses),
        chat_id=chat_id,
        old_msg_id=msg_id,
    )
