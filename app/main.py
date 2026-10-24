import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage

from app.bot.routers import cover, edit, finish, upload
from app.config import settings
from app.services.cleanup import cleanup_loop


def make_bot() -> Bot:
    options = {}
    if settings.api_url:
        options["api"] = TelegramAPIServer.from_base(settings.api_url, is_local=True)
    if settings.proxy:
        options["proxy"] = settings.proxy
    return Bot(settings.bot_token, session=AiohttpSession(**options))


async def main():
    logging.basicConfig(level=logging.INFO)

    bot = make_bot()
    if settings.redis_url:
        storage = RedisStorage.from_url(settings.redis_url)
    else:
        storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_routers(edit.router, cover.router, finish.router, upload.router)

    cleanup = asyncio.create_task(
        cleanup_loop(settings.temp_dir, settings.session_ttl, settings.api_data_dir)
    )
    try:
        await dp.start_polling(bot)
    finally:
        cleanup.cancel()


if __name__ == "__main__":
    asyncio.run(main())