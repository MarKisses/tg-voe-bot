import asyncio
import logging

from aiogram import Bot, Dispatcher
from bot.handlers import register_handlers
from config import settings
from services.notification_worker import notification_worker
from storage import create_redis_client, create_storage
from watchfiles import run_process

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", force=True, datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)


async def main():
    redis = create_redis_client()
    storage = create_storage(redis)

    if not settings.bot_token:
        logging.error(
            "Bot token is not set. Please set BOT_TOKEN environment variable."
        )
        return

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher(storage=storage)

    logger.info("Starting bot...")
    register_handlers(dp)
    asyncio.create_task(notification_worker(bot, interval_seconds=900))
    await dp.start_polling(bot)


def run():
    import asyncio

    asyncio.run(main())


if __name__ == "__main__":
    run_process("app/", target=run)
