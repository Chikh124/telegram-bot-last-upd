import logging
import asyncio
from bot import bot, dp  # Імпорт бота та диспетчера
from aiogram.types import BotCommand
from database import create_tables, create_ticket_tables, set_admin
from handlers import register_handlers  # Імпорт реєстрації обробників

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def set_default_commands():
    """Функція для налаштування стандартних команд"""
    commands = [
        BotCommand(command="/start", description="Запустити бота"),
        BotCommand(command="/help", description="Отримати допомогу"),
    ]
    await bot.set_my_commands(commands)

async def on_startup():
    """Функція, яка викликається при старті бота"""
    logger.info("Бот запущено та готовий до роботи!")

    # Створення таблиць при старті
    create_tables()
    create_ticket_tables()

    # Призначення користувача адміністратором
    set_admin(5368470517)

    # Встановлення команд для бота
    await set_default_commands()

async def main():
    """Головна функція для запуску бота"""
    logger.info("Запуск бота...")

    # Виклик функції запуску
    await on_startup()

    # Реєстрація всіх обробників
    register_handlers(dp)  # Передаємо dp в register_handlers

    # Запуск полінгу для обробки оновлень
    await dp.start_polling(bot)

if __name__ == '__main__':
    # Запуск асинхронного основного процесу
    asyncio.run(main())

