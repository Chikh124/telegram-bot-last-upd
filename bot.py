from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage  # Для збереження станів

# Токен твого бота
TOKEN = "7714422776:AAH9OmXDxmtyxRp0NFoZX2e-RSUylb9DYJI"

# Ініціалізуємо об'єкти бота та диспетчера
bot = Bot(token=TOKEN)
storage = MemoryStorage()  # Створюємо сховище для FSM (пам'ять)
dp = Dispatcher(storage=storage)
