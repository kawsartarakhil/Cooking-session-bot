import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from connections import init_tables
from handlers.start import router as start_router
from handlers.admin import router as admin_router
from aiogram.fsm.storage.memory import MemoryStorage

async def main():
    await init_tables()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start_router)
    dp.include_router(admin_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

