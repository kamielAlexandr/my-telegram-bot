import os
import logging
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler
)
from database import (
    init_db, 
    create_character, 
    get_character, 
    get_all_races,
    update_character_stats,
    add_experience,
    add_gold,
    log_battle
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
CHOOSE_RACE, ENTER_NAME, MAIN_MENU, BATTLE_MENU = range(4)

# Получение токена из переменных окружения
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# --- КЛАВИАТУРЫ ---

def get_main_menu_keyboard():
    """Клавиатура главного меню"""
    keyboard = [
        [InlineKeyboardButton("👤 Мой профиль", callback_data='profile')],
        [InlineKeyboardButton("⚔️ Отправиться в бой", callback_data='battle_menu')],
        [InlineKeyboardButton("🏪 Магазин", callback_data='shop')],
        [InlineKeyboardButton("📊 Статистика", callback_data='stats')],
        [InlineKeyboardButton("❓ Помощь", callback_data='help')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_race_selection_keyboard():
    """Клавиатура выбора расы"""
    races = get_all_races()
    keyboard = []
    
    for race_key, race_data in races.items():
        keyboard.append([
            InlineKeyboardButton(
                f"{race_data['name']} ({race_data['strength']}/{race_data['agility']}/{race_data['intelligence']})",
                callback_data=f'race_{race_key}'
            )
        ])
    
    # Добавляем кнопку для просмотра подробностей о каждой расе
    keyboard.append([InlineKeyboardButton("📖 Подробнее о расах", callback_data='race_info')])
    return InlineKeyboardMarkup(keyboard)

def get_battle_menu_keyboard():
    """Клавиатура меню боя"""
    keyboard = [
        [InlineKeyboardButton("🐺 Бой с волком", callback_data='battle_wolf')],
        [InlineKeyboardButton("🧟 Бой с зомби", callback_data='battle_zombie')],
        [InlineKeyboardButton("🧙 Бой с магом", callback_data='battle_mage')],
        [InlineKeyboardButton("🐉 Босс: Дракон", callback_data='battle_dragon')],
        [InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_battle_action_keyboard():
    """Клавиатура действий в бою"""
    keyboard = [
        [InlineKeyboardButton("⚔️ Атаковать", callback_data='attack')],
        [InlineKeyboardButton("🛡️ Защищаться", callback_data='defend')],
        [InlineKeyboardButton("✨ Исп. способность", callback_data='use_ability')],
        [InlineKeyboardButton("🏃 Сбежать", callback_data='flee')]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- КОМАНДЫ БОТА ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало работы с ботом"""
    user = update.effective_user
    
    # Проверяем, есть ли у пользователя персонаж
    character = get_character(user.id)
    
    if character:
        # Если персонаж уже есть, показываем главное меню
        await update.message.reply_text(
            f"Добро пожаловать обратно, {character['character_name']}!",
            reply_markup=get_main_menu_keyboard()
        )
        return MAIN_MENU
    else:
        # Если персонажа нет, начинаем создание
        await update.message.reply_text(
            f"Привет, {user.first_name}! Добро пожаловать в RPG мир!\n"
            f"Для начала создайте своего персонажа.\n\n"
            f"Выберите расу:",
            reply_markup=get_race_selection_keyboard()
        )
        return CHOOSE_RACE

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда помощи"""
    await update.message.reply_text(
        "🎮 *РПГ Бот - Помощь*\n\n"
        "Основные команды:\n"
        "/start - Начать игру\n"
        "/profile - Показать профиль\n"
        "/battle - Начать бой\n"
        "/inventory - Инвентарь\n\n"
        "В игре вы можете:\n"
        "• Создать персонажа с уникальной расой\n"
        "• Сражаться с различными противниками\n"
        "• Повышать уровень и характеристики\n"
        "• Зарабатывать золото и опыт\n\n"
        "Удачи в приключениях!",
        parse_mode='Markdown'
    )

# --- ОБРАБОТЧИКИ КНОПОК ---

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    # Обработка выбора расы
    if data.startswith('race_'):
        if data == 'race_info':
            # Показываем информацию о расах
            races = get_all_races()
            race_info_text = "📖 *Характеристики рас:*\n\n"
            
            for race_key, race_data in races.items():
                race_info_text += (
                    f"*{race_data['name']}*\n"
                    f"💪 Сила: {race_data['strength']}\n"
                    f"🏹 Ловкость: {race_data['agility']}\n"
                    f"🧠 Интеллект: {race_data['intelligence']}\n"
                    f"❤️ Здоровье: {race_data['health']}\n"
                    f"🔮 Мана: {race_data['mana']}\n"
                    f"✨ Способность: {race_data['racial_ability']}\n\n"
                )
            
            await query.edit_message_text(
                text=race_info_text,
                parse_mode='Markdown'
            )
            await query.edit_message_reply_markup(get_race_selection_keyboard())
            return CHOOSE_RACE
        
        # Сохраняем выбранную расу в контексте
        context.user_data['selected_race'] = data[5:]  # Убираем 'race_'
        
        await query.edit_message_text(
            text="Отличный выбор! Теперь введите имя вашего персонажа:"
        )
        return ENTER_NAME
    
    # Обработка главного меню
    elif data == 'profile':
        await show_profile(query, user_id)
        return MAIN_MENU
    
    elif data == 'battle_menu':
        await query.edit_message_text(
            text="⚔️ *Выберите противника:*",
            parse_mode='Markdown',
            reply_markup=get_battle_menu_keyboard()
        )
        return BATTLE_MENU
    
    elif data == 'shop':
        await show_shop(query)
        return MAIN_MENU
    
    elif data == 'stats':
        await show_stats(query, user_id)
        return MAIN_MENU
    
    elif data == 'help':
        await query.edit_message_text(
            text="🎮 *РПГ Бот - Помощь*\n\n"
            "Используйте кнопки для навигации по игре.\n"
            "• Профиль - просмотр характеристик\n"
            "• Бой - сражения с монстрами\n"
            "• Магазин - покупка предметов\n"
            "• Статистика - ваши достижения",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard()
        )
        return MAIN_MENU
    
    elif data == 'back_to_main':
        await query.edit_message_text(
            text="Главное меню:",
            reply_markup=get_main_menu_keyboard()
        )
        return MAIN_MENU
    
    # Обработка меню боя
    elif data.startswith('battle_'):
        enemy_type = data[7:]  # Убираем 'battle_'
        await start_battle(query, user_id, enemy_type)
        return MAIN_MENU

async def start_battle(query, user_id, enemy_type):
    """Начало боя"""
    character = get_character(user_id)
    
    if not character:
        await query.edit_message_text(
            text="У вас нет персонажа! Используйте /start для создания.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    # Определяем параметры врага в зависимости от типа
    enemies = {
        'wolf': {'name': 'Волк', 'health': 30, 'damage': 5, 'exp': 10, 'gold': 5},
        'zombie': {'name': 'Зомби', 'health': 50, 'damage': 7, 'exp': 15, 'gold': 8},
        'mage': {'name': 'Маг', 'health': 40, 'damage': 12, 'exp': 20, 'gold': 12},
        'dragon': {'name': 'Дракон', 'health': 100, 'damage': 20, 'exp': 50, 'gold': 30}
    }
    
    enemy = enemies.get(enemy_type, enemies['wolf'])
    
    # Сохраняем данные боя в контексте
    battle_data = {
        'enemy': enemy,
        'enemy_current_health': enemy['health'],
        'character_current_health': character['health'],
        'turn': 'player'
    }
    
    # Начинаем бой
    await query.edit_message_text(
        text=f"⚔️ *БОЙ НАЧАЛСЯ!*\n\n"
             f"Ваш противник: *{enemy['name']}*\n"
             f"Здоровье противника: {enemy['health']}❤️\n\n"
             f"Ваше здоровье: {character['health']}❤️\n"
             f"Ваша мана: {character['mana']}🔮\n\n"
             f"Выберите действие:",
        parse_mode='Markdown',
        reply_markup=get_battle_action_keyboard()
    )
    
    # Сохраняем данные боя для дальнейшего использования
    # В реальном проекте нужно хранить состояние боя для каждого пользователя

async def show_profile(query, user_id):
    """Показ профиля персонажа"""
    character = get_character(user_id)
    
    if not character:
        await query.edit_message_text(
            text="У вас еще нет персонажа!",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    # Получаем расу из констант для отображения имени
    from database import RACES
    race_name = RACES.get(character['race'], {}).get('name', character['race'])
    
    profile_text = (
        f"👤 *ПРОФИЛЬ ПЕРСОНАЖА*\n\n"
        f"🏷️ Имя: {character['character_name']}\n"
        f"🎭 Раса: {race_name}\n"
        f"⭐ Уровень: {character['level']}\n"
        f"📊 Опыт: {character['experience']}/{character['level'] * 100}\n\n"
        f"💪 *Характеристики:*\n"
        f"• Сила: {character['strength']}\n"
        f"• Ловкость: {character['agility']}\n"
        f"• Интеллект: {character['intelligence']}\n\n"
        f"❤️ Здоровье: {character['health']}/{character['max_health']}\n"
        f"🔮 Мана: {character['mana']}/{character['max_mana']}\n"
        f"💰 Золото: {character['gold']}\n\n"
        f"⚔️ Победы/Поражения: {character['battle_wins']}/{character['battle_losses']}\n"
        f"📅 Создан: {character['created_at'].strftime('%d.%m.%Y')}"
    )
    
    await query.edit_message_text(
        text=profile_text,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )

async def show_shop(query):
    """Показ магазина"""
    shop_text = (
        "🏪 *МАГАЗИН*\n\n"
        "Товары:\n"
        "1. 💊 Лечебное зелье (восстанавливает 50 HP) - 20 золота\n"
        "2. 🔮 Зелье маны (восстанавливает 30 MP) - 15 золота\n"
        "3. ⚔️ Меч воина (+5 к силе) - 100 золота\n"
        "4. 🏹 Лук охотника (+5 к ловкости) - 100 золота\n"
        "5. 📖 Книга магии (+5 к интеллекту) - 100 золота\n\n"
        "🛒 Функция покупок скоро будет добавлена!"
    )
    
    await query.edit_message_text(
        text=shop_text,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )

async def show_stats(query, user_id):
    """Показ статистики"""
    character = get_character(user_id)
    
    if not character:
        await query.edit_message_text(
            text="У вас еще нет персонажа!",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    # Рассчитываем рейтинг
    total_battles = character['battle_wins'] + character['battle_losses']
    win_rate = (character['battle_wins'] / total_battles * 100) if total_battles > 0 else 0
    
    stats_text = (
        f"📊 *СТАТИСТИКА*\n\n"
        f"🏆 Уровень: {character['level']}\n"
        f"🌟 Опыт: {character['experience']}\n"
        f"💰 Всего золота: {character['gold']}\n\n"
        f"⚔️ Боевая статистика:\n"
        f"• Побед: {character['battle_wins']}\n"
        f"• Поражений: {character['battle_losses']}\n"
        f"• Всего боев: {total_battles}\n"
        f"• Процент побед: {win_rate:.1f}%\n\n"
        f"🎯 Лучший урон: скоро...\n"
        f"🛡️ Макс. защита: скоро..."
    )
    
    await query.edit_message_text(
        text=stats_text,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )

async def create_character_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создание персонажа после ввода имени"""
    user = update.message.from_user
    character_name = update.message.text.strip()
    
    if len(character_name) < 2 or len(character_name) > 20:
        await update.message.reply_text(
            "Имя должно быть от 2 до 20 символов. Попробуйте еще раз:"
        )
        return ENTER_NAME
    
    # Получаем выбранную расу из контекста
    selected_race = context.user_data.get('selected_race', 'human')
    
    # Создаем персонажа в базе данных
    success, message = create_character(
        user.id,
        user.username or user.first_name,
        character_name,
        selected_race
    )
    
    if success:
        await update.message.reply_text(
            f"🎉 Поздравляем! Персонаж создан!\n\n"
            f"Имя: {character_name}\n"
            f"Раса: {selected_race.capitalize()}\n\n"
            f"Теперь вы можете отправиться в приключения!",
            reply_markup=get_main_menu_keyboard()
        )
        return MAIN_MENU
    else:
        await update.message.reply_text(
            f"❌ Ошибка: {message}\n\n"
            f"Попробуйте еще раз с /start"
        )
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена создания персонажа"""
    await update.message.reply_text(
        "Создание персонажа отменено. Используйте /start чтобы начать заново."
    )
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")
    
    if update.callback_query:
        await update.callback_query.message.reply_text(
            "❌ Произошла ошибка. Пожалуйста, попробуйте еще раз."
        )
    elif update.message:
        await update.message.reply_text(
            "❌ Произошла ошибка. Пожалуйста, попробуйте еще раз."
        )

def main():
    """Запуск бота"""
    print("🚀 Запуск RPG бота...")
    
    # Проверка токена
    if not TOKEN:
        print("❌ ОШИБКА: TELEGRAM_BOT_TOKEN не найден")
        return
    
    # Инициализация базы данных
    print("🔄 Инициализация базы данных...")
    try:
        init_db()
        print("✅ База данных готова")
    except Exception as e:
        print(f"⚠️ Предупреждение: {e}")
    
    # Создание приложения
    application = Application.builder().token(TOKEN).build()
    
    # Создание ConversationHandler для управления состоянием
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSE_RACE: [
                CallbackQueryHandler(button_handler, pattern='^race_')
            ],
            ENTER_NAME: [
                CommandHandler('cancel', cancel),
                CallbackQueryHandler(button_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, create_character_name)
            ],
            MAIN_MENU: [
                CallbackQueryHandler(button_handler)
            ],
            BATTLE_MENU: [
                CallbackQueryHandler(button_handler)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )
    
    # Регистрация обработчиков
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('help', help_command))
    application.add_error_handler(error_handler)
    
    print("🤖 RPG бот запущен!")
    print("📱 Перейдите в Telegram и напишите /start")
    
    # Запуск бота
    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )

if __name__ == '__main__':
    # Для работы с ConversationHandler нужен импорт фильтров
    from telegram.ext import MessageHandler, filters
    main()
