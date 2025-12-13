import asyncio

from aiogram import Bot, Dispatcher
from bot.handlers import register_handlers
from config import settings
from logger import create_logger
from services.notification_worker import notification_worker
from storage import create_redis_client, create_storage
from aiohttp.web import Application
from watchfiles import run_process
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

logger = create_logger(__name__)


async def setup_bot() -> tuple[Bot, Dispatcher]:
    redis = create_redis_client()
    storage = create_storage(redis)

    if not settings.bot_token:
        logger.error("Bot token is not set. Please set BOT_TOKEN environment variable.")
        raise ValueError("BOT_TOKEN is required")

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher(storage=storage)

    logger.info("Starting bot...")
    register_handlers(dp)
    asyncio.create_task(notification_worker(bot, interval_seconds=900))

    return bot, dp


async def run_polling():
    bot, dp = await setup_bot()
    await dp.start_polling(bot)
    logger.info("Starting polling...")


async def run_webhook():
    bot, dp = await setup_bot()

    await bot.delete_webhook(drop_pending_updates=True)

    app = Application()

    SimpleRequestHandler(dp, bot, secret_token=settings.webhook.secret_token).register(
        app, path=settings.webhook.full_url
    )

    setup_application(app, dp, bot=bot)
    
    await bot.set_webhook(
        url=settings.webhook.full_url,
        secret_token=settings.webhook.secret_token,
    )
    
    logger.info("Starting webhook server...")


async def main():
    if settings.bot_mode == "polling":
        await run_polling()
    elif settings.bot_mode == "webhook":
        await run_webhook()
        


def run():
    asyncio.run(main())


if __name__ == "__main__":
    if settings.bot_mode == "polling":
        run_process("app/", target=run)
    elif settings.bot_mode == "webhook":
        run()
