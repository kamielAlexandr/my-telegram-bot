import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from database import init_db, save_character, get_character

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получение токена из переменных окружения
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    await update.message.reply_text(
        f'Привет, {user.first_name}! Я бот для сохранения характеристик персонажа.\n'
        'Используй /create <имя> <сила> <ловкость> для создания персонажа.\n'
        'Используй /myprofile для просмотра своего персонажа.'
    )

async def create_character(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создание персонажа"""
    try:
        user_id = update.effective_user.id
        args = context.args
        
        if len(args) < 3:
            await update.message.reply_text(
                'Использование: /create <имя> <сила> <ловкость>\n'
                'Пример: /create Герой 10 8'
            )
            return
        
        name = args[0]
        strength = int(args[1])
        agility = int(args[2])
        
        # Сохраняем в базу данных
        save_character(user_id, name, strength, agility)
        
        await update.message.reply_text(
            f'Персонаж создан!\n'
            f'Имя: {name}\n'
            f'Сила: {strength}\n'
            f'Ловкость: {agility}'
        )
        
    except ValueError:
        await update.message.reply_text('Сила и ловкость должны быть числами!')
    except Exception as e:
        logger.error(f"Error creating character: {e}")
        await update.message.reply_text('Произошла ошибка при создании персонажа')

async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр профиля"""
    user_id = update.effective_user.id
    character = get_character(user_id)
    
    if character:
        await update.message.reply_text(
            f'Ваш персонаж:\n'
            f'Имя: {character["name"]}\n'
            f'Сила: {character["strength"]}\n'
            f'Ловкость: {character["agility"]}\n'
            f'Создан: {character["created_at"].strftime("%d.%m.%Y %H:%M")}'
        )
    else:
        await update.message.reply_text('У вас еще нет персонажа. Используйте /create')

def main():
    """Запуск бота"""
    # Инициализация базы данных
    init_db()
    
    # Создание приложения
    application = Application.builder().token(TOKEN).build()
    
    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("create", create_character))
    application.add_handler(CommandHandler("myprofile", my_profile))
    
    # Запуск бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
