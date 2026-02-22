import asyncio
import ssl
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.types import (
    BotCommand,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeChat,
    FSInputFile,
)
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from bot.handlers import register_handlers
from config import settings
from logger import create_logger, init_logging
from services.notification_worker import notification_worker
from storage import fsm_storage
from watchfiles import run_process

init_logging()
logger = create_logger(__name__)


async def setup_bot_commands(bot: Bot):
    user_commands = [
        BotCommand(command="start", description="Запустити бота"),
        BotCommand(command="about", description="Інформація про бота"),
        BotCommand(command="help", description="Допомога"),
    ]

    await bot.set_my_commands(
        user_commands,
        scope=BotCommandScopeAllPrivateChats(),
    )

    admin_commands = [
        *user_commands,
        BotCommand(
            command="notify_users",
            description="Надіслати повідомлення всім користувачам бота",
        ),
    ]

    if admin_id := settings.admin_id:
        await bot.set_my_commands(
            admin_commands,
            scope=BotCommandScopeChat(
                chat_id=admin_id,
            ),
        )


async def healthcheck(request):
    return web.Response(text="OK")


def setup_bot() -> tuple[Bot, Dispatcher]:
    if not settings.bot_token:
        logger.error("Bot token is not set. Please set BOT_TOKEN environment variable.")
        raise RuntimeError("BOT_TOKEN is required")

    logger.info("Starting bot...")
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher(storage=fsm_storage)
    register_handlers(dp)

    async def on_startup(bot: Bot) -> None:
        logger.info("Starting notification worker...")

        await setup_bot_commands(bot)
        task = asyncio.create_task(
            notification_worker(bot, interval_seconds=settings.notification.interval)
        )

        dp["notification_worker"] = task

        if settings.bot_mode == "webhook":
            logger.info("Setting webhook...")
            await bot.set_webhook(
                url=settings.webhook.full_url,
                secret_token=settings.webhook.secret_token,
                certificate=FSInputFile(settings.webhook.ssl_cert_path),
            )

    async def on_shutdown(bot: Bot) -> None:
        logger.info("Shutting down bot...")

        task: Optional[asyncio.Task] = dp.get("notification_worker")

        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        await bot.session.close()

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    return bot, dp


async def run_polling():
    bot, dp = setup_bot()
    logger.info("Deleting webhook (if any)...")
    await bot.delete_webhook(drop_pending_updates=True)

    logger.info("Starting polling...")
    await dp.start_polling(bot)


def run_webhook():
    bot, dp = setup_bot()

    app = web.Application()
    app.router.add_get("/", healthcheck)

    webhook_requests_handler = SimpleRequestHandler(
        dp, bot, secret_token=settings.webhook.secret_token
    )
    webhook_requests_handler.register(app, path=settings.webhook.path)

    setup_application(app, dp, bot=bot)

    logger.info("Loading SSL context for webhook...")
    logger.debug("Cert path: %s", settings.webhook.ssl_cert_path)

    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(
        certfile=settings.webhook.ssl_cert_path,
        keyfile=settings.webhook.ssl_key_path,
    )

    logger.info(
        "Starting webhook server on %s:%s",
        "0.0.0.0",
        settings.webhook.port,
    )

    web.run_app(
        app,
        host="0.0.0.0",
        port=settings.webhook.port,
        ssl_context=ssl_context,
    )


def main():
    if settings.bot_mode == "polling":
        asyncio.run(run_polling())
    elif settings.bot_mode == "webhook":
        run_webhook()
    else:
        raise ValueError(
            f"Unknown BOT_MODE: {settings.bot_mode!r} (use 'polling' or 'webhook')"
        )


def run():
    main()


if __name__ == "__main__":
    init_logging()
    if settings.debug and settings.bot_mode == "polling":
        run_process("app", target=run)
    else:
        run()
