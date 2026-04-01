import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from bot.config import get_settings
from bot.api.client import APIClient
from bot.middlewares.api_client import APIClientMiddleware
from bot.handlers import start, profile, matches, friends
from bot.proxy_session import create_proxy_session

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def main():
    settings = get_settings()

    bot = Bot(
        token=settings.bot_token,
        session=create_proxy_session(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    api_client = APIClient(settings.backend_url)

    dp.message.middleware(APIClientMiddleware(api_client))
    dp.callback_query.middleware(APIClientMiddleware(api_client))

    dp.include_router(start.router)
    dp.include_router(profile.router)
    dp.include_router(matches.router)
    dp.include_router(friends.router)

    logger.info("Starting Football Bot...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
