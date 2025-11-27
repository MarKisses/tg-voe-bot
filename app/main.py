import logging

from aiogram import Bot, Dispatcher
from watchfiles import run_process

from config import settings
from storage import create_redis_client, create_storage

from bot.handlers import register_handlers

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


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
    
    register_handlers(dp)
    await dp.start_polling(bot)


def run():
    import asyncio

    asyncio.run(main())


if __name__ == "__main__":
    run_process("app/", target=run)
