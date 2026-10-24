import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage

from app.bot.routers import cover, edit, finish, upload
from app.config import settings


async def main():
    logging.basicConfig(level=logging.INFO)

    bot = Bot(settings.bot_token)
    storage = RedisStorage.from_url(settings.redis_url)
    dp = Dispatcher(storage=storage)
    dp.include_routers(edit.router, cover.router, finish.router, upload.router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())