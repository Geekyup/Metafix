import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.redis import RedisStorage

from app.bot.routers import cover, edit, finish, upload
from app.config import settings
from app.services.cleanup import cleanup_loop


async def main():
    logging.basicConfig(level=logging.INFO)

    session = AiohttpSession(proxy=settings.proxy) if settings.proxy else None
    bot = Bot(settings.bot_token, session=session)
    storage = RedisStorage.from_url(settings.redis_url)
    dp = Dispatcher(storage=storage)
    dp.include_routers(edit.router, cover.router, finish.router, upload.router)

    cleanup = asyncio.create_task(cleanup_loop(settings.temp_dir, settings.session_ttl))
    try:
        await dp.start_polling(bot)
    finally:
        cleanup.cancel()


if __name__ == "__main__":
    asyncio.run(main())