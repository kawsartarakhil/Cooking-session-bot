import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from connections import init_tables
from handlers.start import router


async def main():
    await init_tables()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

