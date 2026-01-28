import logging
from typing import Callable, Type

from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, Message
from aiogram.utils.chat_action import ChatActionSender
from bot.keyboards import back_to_main_menu_keyboard
from bot.keyboards.address_list import (
    cities_list_keyboard,
    houses_list_keyboard,
    streets_list_keyboard,
)
from bot.states.address_state import AddressState
from bot.utils import tg_sem_show_service_menu
from config import settings
from exceptions import VoeDownException
from services.fetcher import fetch_cities, fetch_houses, fetch_streets
from services.models import City, House, ItemBase, Street

logger = logging.getLogger(__name__)

router = Router(name=__name__)


async def address_search_step(
    *,
    message: Message,
    state: FSMContext,
    loading_text: str,
    looking_for: str,
    empty_result_text: str,
    fetcher: Callable,
    fetch_kwargs: dict,
    model_cls: Type[ItemBase],
    state_key: str,
    keyboard_builder: Callable[[list], InlineKeyboardMarkup],
):
    logger.info(f"Address search step started for chat_id={message.chat.id}")
    
    try:
        await message.delete()
    except TelegramBadRequest:
        logger.warning("Failed to delete message in address_search_step")
        pass

    query = message.text.strip()
    data = await state.get_data()

    message_id, chat_id = data.get("msg_id"), data.get("chat_id")
    if not chat_id:
        chat_id = message.chat.id

    bot = message.bot
    if not bot:
        return None

    async with ChatActionSender(bot=bot, chat_id=chat_id, action=ChatAction.TYPING):
        await tg_sem_show_service_menu(
            bot=bot,
            chat_id=chat_id,
            text=loading_text,
            old_msg_id=message_id,
        )

        try:
            response = await fetcher(**fetch_kwargs, query=query)
        except VoeDownException:
            return await tg_sem_show_service_menu(
                bot=bot,
                chat_id=chat_id,
                text="VOE впав 😢. Спробуйте пізніше...",
                reply_markup=back_to_main_menu_keyboard(),
            )

    if not response:
        return await tg_sem_show_service_menu(
            bot=bot,
            chat_id=chat_id,
            text=empty_result_text,
            reply_markup=back_to_main_menu_keyboard(),
            old_msg_id=message_id,
        )

    logger.info(f"Fetched {len(response)} items for \"{query}\" {looking_for} search in chat_id={chat_id}")
    objects = [model_cls.from_api(data) for data in response]
    await state.update_data({state_key: [obj.model_dump() for obj in objects]})

    return await tg_sem_show_service_menu(
        bot=bot,
        chat_id=chat_id,
        text=f"Оберіть {looking_for} зі списку:",
        reply_markup=keyboard_builder(objects),
        old_msg_id=message_id,
    )


@router.message(AddressState.choosing_city, F.text)
async def choose_city_handler(message: Message, state: FSMContext):
    logger.info(f"Handling choose_city_handler for chat_id={message.chat.id}")
    return await address_search_step(
        message=message,
        state=state,
        loading_text=settings.messages_loading.loading_city,
        looking_for="місто",
        empty_result_text="Місто не знайдено. <i>Напишіть ще раз назву міста</i>.",
        fetcher=fetch_cities,
        fetch_kwargs={},
        model_cls=City,
        state_key="cities",
        keyboard_builder=cities_list_keyboard,
    )


@router.message(AddressState.choosing_street, F.text)
async def choose_street_handler(message: Message, state: FSMContext):
    logger.info(f"Handling choose_street_handler for chat_id={message.chat.id}")
    data = await state.get_data()
    city = City.model_validate(data.get("chosen_city"))

    return await address_search_step(
        message=message,
        state=state,
        loading_text=settings.messages_loading.loading_street,
        looking_for="вулицю",
        empty_result_text="Вулицю не знайдено. <i>Напишіть ще раз назву вулиці</i>.\n"
        "Введіть виключно назву вулиці без номеру будинку.\n"
        "Перевірте чи існує така вулиця в базі VOE.",
        fetcher=fetch_streets,
        fetch_kwargs={"city_id": city.id},
        model_cls=Street,
        state_key="streets",
        keyboard_builder=streets_list_keyboard,
    )


@router.message(AddressState.choosing_house, F.text)
async def choose_house_handler(message: Message, state: FSMContext):
    logger.info(f"Handling choose_house_handler for chat_id={message.chat.id}")
    data = await state.get_data()
    chosen_street = Street.model_validate(data.get("chosen_street"))

    return await address_search_step(
        message=message,
        state=state,
        loading_text=settings.messages_loading.loading_house,
        looking_for="будинок",
        empty_result_text="Будинок не знайдено. <i>Напишіть ще раз номер будинку</i>.\n"
        "Перевірте чи існує такий номер будинку в базі VOE.",
        fetcher=fetch_houses,
        fetch_kwargs={"street_id": chosen_street.id},
        model_cls=House,
        state_key="houses",
        keyboard_builder=houses_list_keyboard,
    )
