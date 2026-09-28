import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage

from src.bot.handlers import common, tasks
from src.bot.middlewares import DatabaseMiddleware
from src.core.config import settings
from src.core.logging import setup_logging
from src.services import setup_scheduler
from src.bot.middlewares.menu import MenuMiddleware

logger = logging.getLogger(__name__)


async def main() -> None:
    setup_logging()

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML"),
    )

    storage = RedisStorage.from_url(settings.REDIS_DSN)
    dp = Dispatcher(storage=storage)

    dp.update.middleware(DatabaseMiddleware())
    dp.message.middleware(MenuMiddleware())

    dp.include_router(common.router)
    dp.include_router(tasks.router)

    scheduler = setup_scheduler(bot)
    logger.info("Bot started")

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass