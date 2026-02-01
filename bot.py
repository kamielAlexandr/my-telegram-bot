import os
import logging
import random
import asyncio
import time
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters
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

# Глобальная переменная для хранения данных о боях
battle_sessions = {}

# Ссылки на изображения (можно заменить на свои)
IMAGE_URLS = {
    'human': 'https://i126.fastpic.org/thumb/2026/0130/2c/_d2515d33e45fa7ffb5246cacabdaba2c.jpeg',
    'elf': 'https://i126.fastpic.org/thumb/2026/0130/81/_d3d94be5aa45b9239aeb5adc41443081.jpeg',
    'dwarf': 'https://i126.fastpic.org/thumb/2026/0130/5b/_c188fac4eb6d205bd9fc0486c9b9355b.jpeg',
    'orc': 'https://i126.fastpic.org/thumb/2026/0130/20/_b8c1f666bd21bb415e8fb35145eb3e20.jpeg',
    'wolf': 'https://i.imgur.com/5ZtkB9m.png',
    'zombie': 'https://i.imgur.com/6AulC9n.png',
    'mage': 'https://i.imgur.com/7BvmD0o.png',
    'dragon': 'https://i.imgur.com/8CwnE1p.png',
    'village': 'https://i.imgur.com/9DxoF2q.png',
    'forest': 'https://i.imgur.com/0EzGk3r.png',
    'castle': 'https://i.imgur.com/1FyhL4s.png',
    'dungeon': 'https://i.imgur.com/2GzjM5t.png'
}

# --- КЛАВИАТУРЫ ---

def get_main_menu_keyboard():
    """Клавиатура главного меню"""
    keyboard = [
        [InlineKeyboardButton("👤 Мой профиль", callback_data='profile')],
        [InlineKeyboardButton("⚔️ Отправиться в бой", callback_data='battle_menu')],
        [InlineKeyboardButton("🏪 Магазин", callback_data='shop')],
        [InlineKeyboardButton("📊 Статистика", callback_data='stats')],
        [InlineKeyboardButton("❓ Помощь", callback_data='help')],
        [InlineKeyboardButton("🔄 Перезапустить", callback_data='restart')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_race_selection_keyboard():
    """Клавиатура выбора расы"""
    races = get_all_races()
    keyboard = []
    
    for race_key, race_data in races.items():
        keyboard.append([
            InlineKeyboardButton(
                f"{race_data['name']} (💪{race_data['strength']}/🏹{race_data['agility']}/🧠{race_data['intelligence']})",
                callback_data=f'race_{race_key}'
            )
        ])
    
    keyboard.append([InlineKeyboardButton("📖 Подробнее о расах", callback_data='race_info')])
    return InlineKeyboardMarkup(keyboard)

def get_battle_menu_keyboard():
    """Клавиатура меню боя"""
    keyboard = [
        [InlineKeyboardButton("🐺 Волк (Легко)", callback_data='battle_wolf')],
        [InlineKeyboardButton("🧟 Зомби (Средне)", callback_data='battle_zombie')],
        [InlineKeyboardButton("🧙 Маг (Сложно)", callback_data='battle_mage')],
        [InlineKeyboardButton("🐉 Дракон (Босс)", callback_data='battle_dragon')],
        [InlineKeyboardButton("🔙 Назад в меню", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_battle_action_keyboard():
    """Клавиатура действий в бою"""
    keyboard = [
        [InlineKeyboardButton("⚔️ Атаковать", callback_data='attack')],
        [InlineKeyboardButton("🛡️ Защищаться", callback_data='defend')],
        [InlineKeyboardButton("✨ Способность", callback_data='ability')],
        [InlineKeyboardButton("🏃 Сбежать", callback_data='flee')]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- КОМАНДЫ БОТА ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    return await start(update, context)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало работы с ботом"""
    user = update.effective_user
    
    # Отправляем приветственное изображение
    await update.message.reply_photo(
        photo=IMAGE_URLS['village'],
        caption=f"👋 Привет, {user.first_name}! Добро пожаловать в мир RPG!\n\n"
                f"Ты стоишь на пороге великих приключений.\n"
                f"Мир ждет своего героя!"
    )
    
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
            f"Для начала создай своего персонажа.\n\n"
            f"Выбери расу:",
            reply_markup=get_race_selection_keyboard()
        )
        return CHOOSE_RACE

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда помощи"""
    help_text = """
🎮 *РПГ Бот - Руководство*

*Основные команды:*
/start - Начать игру или вернуться в меню
/help - Показать это руководство

*Создание персонажа:*
1. Выбери расу (у каждой свои бонусы)
2. Придумай имя
3. Начни свои приключения!

*Расы и их особенности:*
• 👤 Человек - Универсал, +1 ко всем статам
• 🧝 Эльф - Мастер лука, +50% к мане
• ⛏️ Дварф - Крепкий, +20% к здоровью
• 👹 Орк - Силач, двойной урон в ярости

*В бою:*
• ⚔️ Атака - Обычная атака
• 🛡️ Защита - Уменьшает получаемый урон
• ✨ Способность - Уникальная способность расы
• 🏃 Сбежать - Попытаться избежать боя

Удачи в приключениях! 🏹🐉
"""
    if update.message:
        await update.message.reply_text(help_text, parse_mode='Markdown')
    elif update.callback_query:
        await update.callback_query.message.reply_text(help_text, parse_mode='Markdown')

# --- ОБРАБОТЧИКИ СОЗДАНИЯ ПЕРСОНАЖА ---

async def choose_race(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора расы"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == 'race_info':
        # Показываем подробную информацию о расах
        races = get_all_races()
        info_text = "📖 *Подробнее о расах:*\n\n"
        
        for race_key, race_data in races.items():
            image_url = IMAGE_URLS.get(race_key, IMAGE_URLS['human'])
            info_text += (
                f"*{race_data['name']}*\n"
                f"💪 Сила: {race_data['strength']}\n"
                f"🏹 Ловкость: {race_data['agility']}\n"
                f"🧠 Интеллект: {race_data['intelligence']}\n"
                f"❤️ Здоровье: {race_data['health']}\n"
                f"🔮 Мана: {race_data['mana']}\n"
                f"✨ Способность: {race_data['racial_ability']}\n\n"
            )
        
        await query.edit_message_text(
            text=info_text + "Выбери расу:",
            parse_mode='Markdown',
            reply_markup=get_race_selection_keyboard()
        )
        return CHOOSE_RACE
    
    # Сохраняем выбранную расу
    race_key = data[5:]  # Убираем 'race_'
    context.user_data['selected_race'] = race_key
    
    races = get_all_races()
    race_data = races[race_key]
    image_url = IMAGE_URLS.get(race_key, IMAGE_URLS['human'])
    
    # Отправляем изображение расы
    await query.message.reply_photo(
        photo=image_url,
        caption=f"🎭 Ты выбрал: *{race_data['name']}*\n\n"
                f"*Характеристики:*\n"
                f"💪 Сила: {race_data['strength']}\n"
                f"🏹 Ловкость: {race_data['agility']}\n"
                f"🧠 Интеллект: {race_data['intelligence']}\n"
                f"❤️ Здоровье: {race_data['health']}\n"
                f"🔮 Мана: {race_data['mana']}\n"
                f"✨ Способность: {race_data['racial_ability']}"
    )
    
    await query.message.reply_text(
        f"Теперь введи имя для своего персонажа (от 2 до 20 символов):"
    )
    return ENTER_NAME

async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ввода имени"""
    user = update.message.from_user
    character_name = update.message.text.strip()
    
    # Валидация имени
    if len(character_name) < 2 or len(character_name) > 20:
        await update.message.reply_text(
            "❌ Имя должно быть от 2 до 20 символов. Попробуй еще раз:"
        )
        return ENTER_NAME
    
    # Получаем выбранную расу
    race_key = context.user_data.get('selected_race', 'human')
    
    # Создаем персонажа
    success, message = create_character(
        user_id=user.id,
        username=user.username or user.first_name,
        character_name=character_name,
        race=race_key
    )
    
    if success:
        races = get_all_races()
        race_data = races[race_key]
        image_url = IMAGE_URLS.get(race_key, IMAGE_URLS['human'])
        
        # Отправляем изображение созданного персонажа
        await update.message.reply_photo(
            photo=image_url,
            caption=f"🎉 *Персонаж создан!*\n\n"
                   f"🏷️ *Имя:* {character_name}\n"
                   f"🎭 *Раса:* {race_data['name']}\n"
                   f"✨ *Способность:* {race_data['racial_ability']}",
            parse_mode='Markdown'
        )
        
        await update.message.reply_text(
            f"Твоё приключение начинается! Выбери действие:",
            reply_markup=get_main_menu_keyboard()
        )
        return MAIN_MENU
    else:
        await update.message.reply_text(
            f"❌ Ошибка: {message}\n\n"
            f"Начни заново с /start"
        )
        return ConversationHandler.END

# --- ОБРАБОТЧИКИ ГЛАВНОГО МЕНЮ ---

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик главного меню"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == 'profile':
        await show_profile(query, user_id)
        return MAIN_MENU
    
    elif data == 'battle_menu':
        await show_battle_menu(query)
        return BATTLE_MENU
    
    elif data == 'shop':
        await show_shop(query)
        return MAIN_MENU
    
    elif data == 'stats':
        await show_stats(query, user_id)
        return MAIN_MENU
    
    elif data == 'help':
        await show_help(query)
        return MAIN_MENU
    
    elif data == 'restart':
        await query.edit_message_text(
            text="🔄 Перезапускаю бота...\nНапиши /start чтобы начать заново."
        )
        return ConversationHandler.END

async def show_profile(query, user_id):
    """Показ профиля персонажа"""
    character = get_character(user_id)
    
    if not character:
        await query.edit_message_text(
            text="❌ У тебя еще нет персонажа!",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    races = get_all_races()
    race_data = races.get(character['race'], {})
    image_url = IMAGE_URLS.get(character['race'], IMAGE_URLS['human'])
    
    # Расчет процентов здоровья и маны
    health_percent = int((character['health'] / character['max_health']) * 100) if character['max_health'] > 0 else 0
    mana_percent = int((character['mana'] / character['max_mana']) * 100) if character['max_mana'] > 0 else 0
    
    # Сначала отправляем изображение персонажа
    await query.message.reply_photo(
        photo=image_url,
        caption=f"👤 *{character['character_name']}*\n"
               f"⭐ Уровень {character['level']} {race_data.get('name', '')}"
    )
    
    profile_text = (
        f"*Характеристики:*\n"
        f"💪 Сила: {character['strength']}\n"
        f"🏹 Ловкость: {character['agility']}\n"
        f"🧠 Интеллект: {character['intelligence']}\n\n"
        f"❤️ Здоровье: {character['health']}/{character['max_health']} ({health_percent}%)\n"
        f"🔮 Мана: {character['mana']}/{character['max_mana']} ({mana_percent}%)\n"
        f"💰 Золото: {character['gold']}\n\n"
        f"🎯 *Статистика:*\n"
        f"🏆 Побед: {character.get('battle_wins', 0)}\n"
        f"💀 Поражений: {character.get('battle_losses', 0)}\n\n"
        f"✨ *Расовая способность:*\n"
        f"{race_data.get('racial_ability', 'Нет информации')}"
    )
    
    await query.message.reply_text(
        text=profile_text,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )

async def show_battle_menu(query):
    """Показ меню выбора противника"""
    await query.message.reply_photo(
        photo=IMAGE_URLS['forest'],
        caption="⚔️ *Кого будем побеждать?*\n\n"
                "Выбери противника:"
    )
    
    await query.message.reply_text(
        text="🐺 Волк - Легкий противник\n"
             "🧟 Зомби - Средней сложности\n"
             "🧙 Маг - Сложный противник\n"
             "🐉 Дракон - Очень сложный босс",
        reply_markup=get_battle_menu_keyboard()
    )

async def show_shop(query):
    """Показ магазина"""
    shop_text = (
        "🏪 *Магазин*\n\n"
        "Здесь ты можешь купить полезные предметы:\n\n"
        "1. 💊 Зелье лечения (+50 HP) - 30 золота\n"
        "2. 🔮 Зелье маны (+30 MP) - 25 золота\n"
        "3. ⚔️ Обычный меч (+2 к силе) - 50 золота\n"
        "4. 🏹 Простой лук (+2 к ловкости) - 50 золота\n"
        "5. 📖 Свиток мудрости (+2 к интеллекту) - 50 золота\n\n"
        "🛒 *В разработке...*\n"
        "Скоро ты сможешь покупать предметы!"
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
            text="❌ У тебя еще нет персонажа!",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    total_battles = character.get('battle_wins', 0) + character.get('battle_losses', 0)
    win_rate = (character.get('battle_wins', 0) / total_battles * 100) if total_battles > 0 else 0
    
    stats_text = (
        f"📊 *Статистика*\n\n"
        f"⭐ *Уровень:* {character['level']}\n"
        f"🌟 *Опыт:* {character['experience']}\n"
        f"💰 *Золото:* {character['gold']}\n\n"
        f"⚔️ *Боевая статистика:*\n"
        f"• Побед: {character.get('battle_wins', 0)}\n"
        f"• Поражений: {character.get('battle_losses', 0)}\n"
        f"• Всего боев: {total_battles}\n"
        f"• Процент побед: {win_rate:.1f}%\n\n"
        f"📅 *Дата создания:*\n"
        f"{character['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
        f"🕐 *Последняя активность:*\n"
        f"{character['last_active'].strftime('%d.%m.%Y %H:%M')}"
    )
    
    await query.edit_message_text(
        text=stats_text,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )

async def show_help(query):
    """Показ помощи"""
    help_text = """
🎮 *РПГ Бот - Помощь*

*Управление:*
Используй кнопки для навигации по игре.

*Основные разделы:*
• 👤 Профиль - характеристики и статистика
• ⚔️ Бой - сражения с монстрами
• 🏪 Магазин - покупка предметов
• 📊 Статистика - твои достижения
• ❓ Помощь - эта справка

*Создание персонажа:*
Выбери расу, которая подходит твоему стилю игры:
• Человек - сбалансированная раса
• Эльф - для магических атак
• Дварф - для защиты и выживания
• Орк - для максимального урона

*Советы:*
1. Начни с легких противников
2. Используй расовые способности
3. Следи за здоровьем и маной
4. Повышай уровень для улучшения характеристик

Удачи в приключениях! 🐉
"""
    await query.edit_message_text(
        text=help_text,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )

# --- ОБРАБОТЧИКИ БОЯ ---

async def battle_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик меню боя"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == 'back_to_main':
        await query.edit_message_text(
            text="Возвращаюсь в главное меню...",
            reply_markup=get_main_menu_keyboard()
        )
        return MAIN_MENU
    
    elif data.startswith('battle_'):
        enemy_type = data[7:]  # Убираем 'battle_'
        await start_battle(query, user_id, enemy_type)

async def start_battle(query, user_id, enemy_type):
    """Начало боя"""
    character = get_character(user_id)
    
    if not character:
        await query.edit_message_text(
            text="❌ У тебя нет персонажа!",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    # Определяем параметры врага
    enemies = {
        'wolf': {
            'name': '🐺 Волк',
            'health': 30,
            'max_health': 30,
            'min_damage': 3,
            'max_damage': 8,
            'exp': 15,
            'gold': 10,
            'description': 'Быстрый и опасный хищник леса',
            'image': IMAGE_URLS['wolf']
        },
        'zombie': {
            'name': '🧟 Зомби',
            'health': 50,
            'max_health': 50,
            'min_damage': 5,
            'max_damage': 12,
            'exp': 25,
            'gold': 20,
            'description': 'Медленный, но живучий нежитик',
            'image': IMAGE_URLS['zombie']
        },
        'mage': {
            'name': '🧙 Маг',
            'health': 40,
            'max_health': 40,
            'min_damage': 8,
            'max_damage': 18,
            'exp': 40,
            'gold': 35,
            'description': 'Опасный противник, использующий магию',
            'image': IMAGE_URLS['mage']
        },
        'dragon': {
            'name': '🐉 Дракон',
            'health': 100,
            'max_health': 100,
            'min_damage': 15,
            'max_damage': 30,
            'exp': 100,
            'gold': 80,
            'description': 'Могучее существо, босс игры',
            'image': IMAGE_URLS['dragon']
        }
    }
    
    enemy = enemies.get(enemy_type, enemies['wolf'])
    
    # Отправляем изображение врага
    await query.message.reply_photo(
        photo=enemy['image'],
        caption=f"⚔️ *БОЙ НАЧИНАЕТСЯ!*\n\n"
               f"Ты встретил: *{enemy['name']}*\n"
               f"📖 {enemy['description']}"
    )
    
    # Создаем сессию боя
    battle_sessions[user_id] = {
        'enemy': enemy.copy(),
        'character': character.copy(),
        'turn': 0,
        'player_defending': False,
        'enemy_defending': False,
        'log': []
    }
    
    battle_log = battle_sessions[user_id]['log']
    battle_log.append(f"❤️ Здоровье врага: {enemy['health']}/{enemy['max_health']}")
    battle_log.append(f"❤️ Твое здоровье: {character['health']}/{character['max_health']}")
    battle_log.append("")
    battle_log.append("Выбери действие:")
    
    await query.message.reply_text(
        text="\n".join(battle_log),
        reply_markup=get_battle_action_keyboard()
    )

async def battle_action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик действий в бою"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if user_id not in battle_sessions:
        await query.edit_message_text(
            text="❌ Бой завершен или не найден!",
            reply_markup=get_main_menu_keyboard()
        )
        return MAIN_MENU
    
    battle_data = battle_sessions[user_id]
    character = battle_data['character']
    enemy = battle_data['enemy']
    battle_log = battle_data['log']
    
    # Очищаем лог для нового хода
    battle_log.clear()
    battle_data['turn'] += 1
    
    # Действие игрока
    if data == 'attack':
        player_damage = random.randint(character['strength'] // 2, character['strength'])
        if battle_data['enemy_defending']:
            player_damage = max(1, player_damage // 2)
            battle_log.append(f"⚔️ Ты атаковал, но враг защищался!")
        else:
            battle_log.append(f"⚔️ Ты нанес {player_damage} урона!")
        enemy['health'] -= player_damage
        
    elif data == 'defend':
        battle_data['player_defending'] = True
        battle_log.append(f"🛡️ Ты встал в защитную стойку!")
        
    elif data == 'ability':
        # Использование расовой способности
        if character['race'] == 'human':
            # Адаптивность: временно увеличивает все характеристики
            bonus = random.randint(1, 3)
            battle_log.append(f"✨ Адаптивность: все твои характеристики увеличены на {bonus}!")
            
        elif character['race'] == 'elf':
            # Магический дар: точная атака с шансом критического урона
            if random.random() < 0.3:  # 30% шанс
                damage = character['intelligence'] * 2
                battle_log.append(f"✨ Магический дар: Критическая атака! Нанесено {damage} урона!")
                enemy['health'] -= damage
            else:
                damage = character['intelligence']
                battle_log.append(f"✨ Магический дар: Точная атака! Нанесено {damage} урона!")
                enemy['health'] -= damage
            
        elif character['race'] == 'dwarf':
            # Каменная кожа: временно увеличивает защиту и восстанавливает здоровье
            heal_amount = random.randint(5, 15)
            character['health'] = min(character['max_health'], character['health'] + heal_amount)
            battle_data['player_defending'] = True
            battle_log.append(f"✨ Каменная кожа: Ты восстанавливаешь {heal_amount} HP и защищаешься!")
            
        elif character['race'] == 'orc':
            # Ярость: сильная атака, но получает урон
            damage = character['strength'] * 2
            self_damage = random.randint(1, 5)
            enemy['health'] -= damage
            character['health'] -= self_damage
            battle_log.append(f"✨ Ярость: Ты наносишь {damage} урона, но теряешь {self_damage} HP!")
            
    elif data == 'flee':
        flee_chance = random.randint(1, 100)
        if flee_chance > 50:  # 50% шанс сбежать
            battle_log.append("🏃 Ты успешно сбежал с поля боя!")
            del battle_sessions[user_id]
            await query.edit_message_text(
                text="\n".join(battle_log),
                reply_markup=get_main_menu_keyboard()
            )
            return MAIN_MENU
        else:
            battle_log.append("🏃 Ты попытался сбежать, но не смог!")
    
    # Действие врага
    if enemy['health'] > 0:
        enemy_action = random.choice(['attack', 'attack', 'defend'])  # 66% атака, 33% защита
        
        if enemy_action == 'attack':
            enemy_damage = random.randint(enemy['min_damage'], enemy['max_damage'])
            if battle_data['player_defending']:
                enemy_damage = max(1, enemy_damage // 2)
                battle_log.append(f"🐺 Враг атаковал, но ты защищался!")
            else:
                battle_log.append(f"🐺 Враг нанес тебе {enemy_damage} урона!")
            character['health'] -= enemy_damage
            battle_data['player_defending'] = False
        else:
            battle_data['enemy_defending'] = True
            battle_log.append(f"🐺 Враг защищается!")
    
    # Сбрасываем защиту врага после его хода
    battle_data['enemy_defending'] = False
    
    # Проверка окончания боя
    if character['health'] <= 0:
        battle_log.append("")
        battle_log.append("💀 *ТЫ ПРОИГРАЛ!*")
        battle_log.append("Ты был повержен в бою...")
        
        # Обновляем статистику в БД
        update_character_stats(user_id, battle_losses=character['battle_losses'] + 1)
        log_battle(user_id, enemy['name'], 'поражение', 0, 0, 0, 0)
        
        del battle_sessions[user_id]
        await query.edit_message_text(
            text="\n".join(battle_log),
            reply_markup=get_main_menu_keyboard()
        )
        return MAIN_MENU
    
    elif enemy['health'] <= 0:
        battle_log.append("")
        battle_log.append("🏆 *ТЫ ПОБЕДИЛ!*")
        battle_log.append(f"Ты победил {enemy['name']}!")
        
        # Награда
        exp_gained = enemy['exp']
        gold_gained = enemy['gold']
        
        battle_log.append(f"🎁 Получено: {exp_gained} опыта и {gold_gained} золота")
        
        # Обновляем данные в БД
        update_character_stats(
            user_id, 
            battle_wins=character['battle_wins'] + 1,
            gold=character['gold'] + gold_gained
        )
        add_experience(user_id, exp_gained)
        add_gold(user_id, gold_gained)
        log_battle(user_id, enemy['name'], 'победа', 0, 0, gold_gained, exp_gained)
        
        del battle_sessions[user_id]
        await query.edit_message_text(
            text="\n".join(battle_log),
            reply_markup=get_main_menu_keyboard()
        )
        return MAIN_MENU
    
    # Продолжение боя
    else:
        battle_log.append("")
        battle_log.append(f"❤️ Твое здоровье: {max(0, character['health'])}/{character['max_health']}")
        battle_log.append(f"❤️ Здоровье врага: {max(0, enemy['health'])}/{enemy['max_health']}")
        battle_log.append(f"🎯 Ход: {battle_data['turn']}")
        battle_log.append("")
        battle_log.append("Выбери действие:")
        
        await query.edit_message_text(
            text="\n".join(battle_log),
            reply_markup=get_battle_action_keyboard()
        )
    return BATTLE_MENU

# --- ОБРАБОТЧИКИ ОШИБОК ---

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена диалога"""
    await update.message.reply_text(
        "Действие отменено. Используй /start чтобы начать заново."
    )
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    error = context.error
    
    if "Conflict: terminated by other getUpdates request" in str(error):
        logger.warning("⚠️ Обнаружен конфликт с другим экземпляром бота.")
        logger.warning("⚠️ Перезапускаю бота через 5 секунд...")
        
        # Ждем 5 секунд и перезапускаем бота
        await asyncio.sleep(5)
        await context.application.stop()
        await asyncio.sleep(2)
        await context.application.initialize()
        await context.application.start()
        await context.application.updater.start_polling()
        return
    
    logger.error(f"Ошибка: {error}", exc_info=True)
    
    try:
        if update and update.callback_query:
            await update.callback_query.message.reply_text(
                "❌ Произошла ошибка. Попробуй еще раз или перезапусти бота с /start"
            )
        elif update and update.message:
            await update.message.reply_text(
                "❌ Произошла ошибка. Попробуй еще раз или перезапусти бота с /start"
            )
    except Exception as e:
        logger.error(f"Не удалось отправить сообщение об ошибке: {e}")

# --- ОСНОВНАЯ ФУНКЦИЯ ---

def main():
    """Запуск бота"""
    print("🚀 Запуск RPG бота...")
    
    # Проверка токена
    if not TOKEN:
        print("❌ ОШИБКА: TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        print("Добавьте переменную TELEGRAM_BOT_TOKEN в Railway")
        return
    
    print(f"✅ Токен найден, длина: {len(TOKEN)} символов")
    
    # Инициализация базы данных
    print("🔄 Инициализация базы данных...")
    try:
        init_db()
        print("✅ База данных инициализирована")
    except Exception as e:
        print(f"⚠️ Предупреждение: не удалось инициализировать БД: {e}")
    
    # Создание приложения
    try:
        application = Application.builder().token(TOKEN).build()
        
        # Conversation Handler для создания персонажа
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start_command)],
            states={
                CHOOSE_RACE: [
                    CallbackQueryHandler(choose_race, pattern='^race_')
                ],
                ENTER_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, enter_name)
                ],
                MAIN_MENU: [
                    CallbackQueryHandler(main_menu_handler)
                ],
                BATTLE_MENU: [
                    CallbackQueryHandler(battle_menu_handler),
                    CallbackQueryHandler(battle_action_handler, pattern='^(attack|defend|ability|flee)$')
                ]
            },
            fallbacks=[CommandHandler('cancel', cancel)],
            allow_reentry=True
        )
        
        # Регистрация обработчиков
        application.add_handler(conv_handler)
        application.add_handler(CommandHandler('help', help_command))
        
        # Обработчик ошибок
        application.add_error_handler(error_handler)
        
        print("🤖 RPG бот запущен!")
        print("📱 Перейдите в Telegram и напишите /start")
        
        # Запуск бота с обработкой конфликтов
        application.run_polling(
            drop_pending_updates=True,
            close_loop=False,
            allowed_updates=Update.ALL_TYPES
        )
        
    except Exception as e:
        print(f"❌ Критическая ошибка при запуске бота: {e}")
        print("\nВозможные решения:")
        print("1. Проверьте токен бота в Railway Variables")
        print("2. Убедитесь, что запущен только один экземпляр бота")
        print("3. Проверьте подключение к интернету")

if __name__ == '__main__':
    main()
