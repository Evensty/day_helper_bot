import asyncio
from bot import bot, dp  # Импортируем bot и dp
from handlers import start, user, tasks  # Импортируем все обработчики

async def main():
    dp.include_router(start.router)  # Подключаем Router из start.py
    dp.include_router(user.router)  # Подключаем Router из tasks.py
    dp.include_router(tasks.router)  # Подключаем Router из tasks.py
    await dp.start_polling(bot)  # Запускаем бота

if __name__ == "__main__":
    asyncio.run(main())  # Запуск