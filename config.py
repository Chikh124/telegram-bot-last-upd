# config.py

from dotenv import load_dotenv
import os

# Завантажуємо змінні з .env файлу
load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv('BOT_TOKEN')
