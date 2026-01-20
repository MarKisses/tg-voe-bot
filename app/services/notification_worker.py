import asyncio
from datetime import datetime, timedelta
from typing import Literal

from aiogram import Bot
from aiogram.types.input_file import BufferedInputFile
from bot.keyboards.main_menu import main_menu_keyboard
from bot.utils import tg_sem_send_photo, tg_sem_replace_service_menu
from exceptions import VoeDownException
from logger import create_logger
from services.fetcher import fetch_schedule
from services.models import ScheduleResponse
from services.parser import parse_schedule
from services.renderer import render_schedule_image
from storage import subscription_storage, user_storage
from config import settings

logger = create_logger(__name__)

SubscriptionKinds = Literal["today", "tomorrow"]


def _calc_hash(obj: dict) -> str:
    """Calculate a simple hash for a dictionary object."""
    import hashlib
    import json

    obj_str = json.dumps(obj, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(obj_str.encode("utf-8")).hexdigest()


async def _update_hashes_for_address(
    addr_id: str, schedule: ScheduleResponse
) -> set[SubscriptionKinds]:
    """
    Update stored hashes for today's and tomorrow's schedules.
    Return a list of kinds ('today', 'tomorrow') that have changed.
    """
    today_date = datetime.now().date().isoformat()
    tomorrow_date = (datetime.now() + timedelta(days=1)).date().isoformat()

    changed: set[SubscriptionKinds] = set()

    today_old = await subscription_storage.get_last_hash(addr_id, "today")
    tomorrow_old = await subscription_storage.get_last_hash(addr_id, "tomorrow")

    today_hash, tomorrow_hash = None, None

    # --- TODAY ---
    today = schedule.get_day_schedule(today_date)
    if today:
        today_hash = _calc_hash(today.model_dump())

        # If user just added subscription, do not send notification immediately
        if today_old is None:
            await subscription_storage.set_last_hash(addr_id, "today", today_hash)
        elif today_hash != today_old:
            await subscription_storage.set_last_hash(addr_id, "today", today_hash)
            changed.add("today")

    # --- TOMORROW ---
    tomorrow = schedule.get_day_schedule(tomorrow_date)
    if tomorrow:
        tomorrow_hash = _calc_hash(tomorrow.model_dump())

        # On contrary, for tomorrow we always notify on first fetch
        if tomorrow_hash != tomorrow_old and tomorrow.has_disconnections:
            await subscription_storage.set_last_hash(addr_id, "tomorrow", tomorrow_hash)
            changed.add("tomorrow")

    # Avoid notifying both today and tomorrow if they are identical
    if "today" in changed and today and tomorrow_old and today_hash == tomorrow_old:
        changed.remove("today")
        
    if settings.notification.silent_hash_recalculation:
        changed.clear()
    return changed


async def _process_for_address(
    bot: Bot,
    addr_id: str,
    subscribers_today: set[int],
    subscribers_tomorrow: set[int],
) -> set[int]:
    """
    Process schedule for a specific address.
    Send notifications to subscribers if there are changes.
    Distinguish between 'today' and 'tomorrow' subscriptions.
    Return a set of user IDs who were notified.
    """

    city_id, street_id, house_id = map(int, addr_id.split("-"))
    processed_users = set()
    tasks = []

    try:
        raw = await fetch_schedule(city_id, street_id, house_id)
    except VoeDownException:
        logger.error(f"VOE is down, cannot fetch schedule for address {addr_id}")
        return set()

    if not raw:
        logger.critical("Can't get info from VOE site")
        return set()

    # Need to get full address info for message and rendering
    # TODO: refactor this adding separate method to get address info only
    address = await user_storage.get_address_by_id(
        (
            next(iter(subscribers_today))
            if subscribers_today
            else next(iter(subscribers_tomorrow))
        ),
        addr_id,
    )
    if not address:
        logger.critical(f"Address {addr_id} not found in user storage")
        return set()

    schedule = parse_schedule(raw, address.name, max_days=2)
    if not schedule.disconnections:
        logger.warning(f"No disconnections for {addr_id} for 2 days")
        return set()

    changed = await _update_hashes_for_address(addr_id, schedule)

    today = datetime.now().date().isoformat()
    tomorrow = (datetime.now() + timedelta(days=1)).date().isoformat()
    if "today" in changed:
        msg = f"⚡ Оновлено графік відключень на сьогодні за адресою {address.name}."
        day_schedule = schedule.get_day_schedule(today)
        if not day_schedule:
            logger.warning(f"No schedule for today for {addr_id}")
            return processed_users

        image_bytes = render_schedule_image(
            day=day_schedule,
            queue=schedule.disconnection_queue,
            date=today,
            address=schedule.address,
        ).getvalue()
        tasks = []
        for uid in subscribers_today:
            tasks.append(
                tg_sem_send_photo(
                    bot,
                    chat_id=uid,
                    photo=BufferedInputFile(image_bytes, filename="schedule.png"),
                    caption=msg,
                    show_caption_above_media=True,
                )
            )
            processed_users.add(uid)
            logger.info(
                f"Sent notification to user {uid} for address {addr_id} today ({schedule.address})"
            )

    if "tomorrow" in changed:
        msg = f"📅 З'явився/оновився графік на завтра за адресою {address.name}."
        day_schedule = schedule.get_day_schedule(tomorrow)
        if not day_schedule:
            logger.warning(f"No schedule for tomorrow for {addr_id}")
            return processed_users

        image_bytes = render_schedule_image(
            day=day_schedule,
            queue=schedule.disconnection_queue,
            date=tomorrow,
            address=schedule.address,
        ).getvalue()
        tasks = []
        for uid in subscribers_tomorrow:
            tasks.append(
                tg_sem_send_photo(
                    bot,
                    chat_id=uid,
                    photo=BufferedInputFile(image_bytes, filename="schedule.png"),
                    caption=msg,
                    show_caption_above_media=True,
                )
            )
            processed_users.add(uid)
            logger.info(
                f"Sent notification to user {uid} for address {addr_id} tomorrow ({schedule.address})"
            )
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
    return processed_users


async def _process_address_safe(bot, addr_id: str) -> set[int]:
    """Wrapper to process address and catch exceptions."""
    subs_today = await subscription_storage.get_subscribers(addr_id, "today")
    subs_tomorrow = await subscription_storage.get_subscribers(addr_id, "tomorrow")

    if not subs_today and not subs_tomorrow:
        return set()

    return await _process_for_address(bot, addr_id, subs_today, subs_tomorrow)


async def notification_worker(bot: Bot, interval_seconds: int = 900) -> None:
    while True:
        try:
            addr_ids = await subscription_storage.get_all_addresses()

            # List of sets of processed users
            tasks = [
                _process_address_safe(bot, addr_id=addr_id) for addr_id in addr_ids
            ]
            result_list_raw = await asyncio.gather(*tasks, return_exceptions=True)
            exceptions = [res for res in result_list_raw if isinstance(res, Exception)]
            for e in exceptions:
                logger.error("Error during processing address: %s", e)

            result_list = [res for res in result_list_raw if isinstance(res, set)]
            processed_users: set[int] = set().union(*result_list)

            # Finally, update service menus for all processed users once
            messages_tasks = [
                tg_sem_replace_service_menu(
                    bot=bot,
                    chat_id=uid,
                    text="Головне меню",
                    reply_markup=main_menu_keyboard(),
                )
                for uid in processed_users
            ]
            await asyncio.gather(*messages_tasks, return_exceptions=True)
            exceptions = [res for res in messages_tasks if isinstance(res, Exception)]
            for e in exceptions:
                logger.error("Error during updating service menu: %s", e)

            logger.info(
                f"Notification worker tick completed. Processed {len(processed_users)} users."
            )
            
            if settings.notification.silent_hash_recalculation:
                logger.info("Silent hash recalculation mode is ON. No notifications were sent.")
                settings.notification.silent_hash_recalculation = False
                logger.info("Silent hash recalculation mode is now OFF.")

        except Exception as e:
            logger.exception("Notification worker tick failed %s", e)

        await asyncio.sleep(interval_seconds)
