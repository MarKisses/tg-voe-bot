import asyncio
from typing import Literal

from aiogram import Bot
from aiogram.types.input_file import BufferedInputFile
from bot.keyboards.main_menu import main_menu_keyboard
from logger import create_logger
from services.fetcher import fetch_schedule
from services.models import ScheduleResponse
from services.parser import parse_schedule
from services.renderer import render_schedule_image
from storage import subscription_storage, user_storage
from bot.utils import show_service_menu, replace_service_menu

SubscriptionKinds = Literal["today", "tomorrow"]

logger = create_logger(__name__)


def _calc_hash(obj: dict) -> str:
    """Calculate a simple hash for a dictionary object."""
    import hashlib
    import json

    obj_str = json.dumps(obj, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(obj_str.encode("utf-8")).hexdigest()


async def _update_hashes_for_address(addr_id: str, schedule: ScheduleResponse):
    disconnections = schedule.disconnections
    changed = []

    today_old = await subscription_storage.get_last_hash(addr_id, "today")
    tomorrow_old = await subscription_storage.get_last_hash(addr_id, "tomorrow")

    if today_old is not None:
        today_old = today_old
    if tomorrow_old is not None:
        tomorrow_old = tomorrow_old

    # today
    if len(disconnections) >= 1:
        today = disconnections[0].model_dump()
        today_hash = _calc_hash(today)

        # If user just added subscription, do not send notification immediately
        if today_old is None:
            await subscription_storage.set_last_hash(addr_id, "today", today_hash)
        elif today_hash != today_old:
            await subscription_storage.set_last_hash(addr_id, "today", today_hash)
            changed.append("today")

    # tomorrow
    if len(disconnections) >= 2:
        tomorrow = disconnections[1]
        tomorrow_data = tomorrow.model_dump()
        tomorrow_hash = _calc_hash(tomorrow_data)

        # If user just added subscription, do not send notification immediately
        if tomorrow_old is None:
            await subscription_storage.set_last_hash(addr_id, "tomorrow", tomorrow_hash)
        elif tomorrow_hash != tomorrow_old and tomorrow.has_disconnections:
            await subscription_storage.set_last_hash(addr_id, "tomorrow", tomorrow_hash)
            changed.append("tomorrow")

    # When new today is same as old tomorrow, we consider that there is no change in today
    if today_hash and tomorrow_old:
        if today_hash == tomorrow_old and "today" in changed:
            changed.remove("today")
    return changed


async def _process_for_address(
    bot: Bot,
    addr_id: str,
    subscribers_today: list[int],
    subscribers_tomorrow: list[int],
):
    city_id, street_id, house_id = map(int, addr_id.split("-"))

    raw = await fetch_schedule(city_id, street_id, house_id)
    if not raw:
        logger.critical("Can't get info from VOE site")
        return

    address = await user_storage.get_address_by_id(
        subscribers_today[0] if subscribers_today else subscribers_tomorrow[0], addr_id
    )
    if not address:
        logger.warning(f"Address {addr_id} not found in user storage")
        return
    schedule = parse_schedule(raw, address.name, max_days=2)

    if not schedule.disconnections:
        logger.warning(f"No disconnections for {addr_id} for 2 days")
        return

    changed = await _update_hashes_for_address(addr_id, schedule)

    # 4) sending messages
    if "today" in changed:
        msg = f"⚡ Оновлено графік відключень на сьогодні за адресою {address.name}."
        buffered_file = BufferedInputFile(
            render_schedule_image(
                day=schedule.disconnections[0],
                queue=schedule.disconnection_queue,
                date=schedule.disconnections[0].date,
                address=schedule.address,
            ).getvalue(),
            filename="schedule.png",
        )
        for uid in subscribers_today:
            # await bot.send_message(uid, msg)
            await bot.send_photo(
                uid, photo=buffered_file, caption=msg, show_caption_above_media=True
            )
            await replace_service_menu(
                bot=bot,
                chat_id=uid,
                text="Головне меню",
                reply_markup=main_menu_keyboard(),
            )
            logger.info(
                f"Sent notification to user {uid} for address {addr_id} today ({schedule.address})"
            )

    if "tomorrow" in changed:
        msg = f"📅 З'явився/оновився графік на завтра за адресою {address.name}."
        buffered_file = BufferedInputFile(
            render_schedule_image(
                day=schedule.disconnections[1],
                queue=schedule.disconnection_queue,
                date=schedule.disconnections[1].date,
                address=schedule.address,
            ).getvalue(),
            filename="schedule.png",
        )
        for uid in subscribers_tomorrow:
            await bot.send_photo(
                uid, photo=buffered_file, caption=msg, show_caption_above_media=True
            )
            await replace_service_menu(
                bot=bot,
                chat_id=uid,
                text="Головне меню",
                reply_markup=main_menu_keyboard(),
            )
            logger.info(
                f"Sent notification to user {uid} for address {addr_id} tomorrow ({schedule.address})"
            )


async def _process_address_safe(bot, addr_id: str):
    subs_today = await subscription_storage.get_subscribers(addr_id, "today")
    subs_tomorrow = await subscription_storage.get_subscribers(addr_id, "tomorrow")

    if not subs_today and not subs_tomorrow:
        return

    await _process_for_address(bot, addr_id, subs_today, subs_tomorrow)


async def notification_worker(bot: Bot, interval_seconds: int = 900) -> None:
    while True:
        try:
            addr_ids = await subscription_storage.get_all_addresses()
            tasks = []
            for addr_id in addr_ids:
                tasks.append(_process_address_safe(bot, addr_id=addr_id))

            await asyncio.gather(*tasks)
        except Exception as e:
            logger.exception("Notification worker tick failed %s", e)

        await asyncio.sleep(interval_seconds)
