# config.py
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройки бота
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# Настройки базы данных
DB_PATH = 'data/game_bot.db'  # Путь к файлу БД

# Другие настройки
ADMIN_IDS = [123456789]  # ID администраторов

# Проверка обязательных настроек
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не установлен. Проверьте .env файл")
