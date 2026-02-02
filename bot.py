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
    log_battle,
    buy_item,
    get_inventory
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
CHOOSE_RACE, ENTER_NAME, MAIN_MENU, BATTLE_MENU, IN_BATTLE, SHOP_MENU = range(6)

# Получение токена из переменных окружения
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Глобальная переменная для хранения данных о боях
battle_sessions = {}

# Ссылки на изображения
IMAGE_URLS = {
    'human': 'https://i126.fastpic.org/thumb/2026/0130/2c/_d2515d33e45fa7ffb5246cacabdaba2c.jpeg',
    'elf': 'https://i126.fastpic.org/thumb/2026/0130/81/_d3d94be5aa45b9239aeb5adc41443081.jpeg',
    'dwarf': 'https://i126.fastpic.org/thumb/2026/0130/5b/_c188fac4eb6d205bd9fc0486c9b9355b.jpeg',
    'orc': 'https://i126.fastpic.org/thumb/2026/0130/20/_b8c1f666bd21bb415e8fb35145eb3e20.jpeg',
    'wolf': 'https://i.pinimg.com/736x/9f/8e/25/9f8e2507aceaa217060d249c308e2a13.jpg',
    'zombie': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQRBEAcmeuf4tt0xnFUG1E8wcvZlSkLQcZkUw&s',
    'mage': 'https://abrakadabra.fun/uploads/posts/2022-01/1642490542_3-abrakadabra-fun-p-temnii-mag-art-5.jpg',
    'dragon': 'https://abrakadabra.fun/uploads/posts/2022-03/1646721873_1-abrakadabra-fun-p-pauk-fentezi-art-1.jpg',
    'village': 'https://img.freepik.com/premium-photo/tavern-like-game_808092-1770.jpg',
    'forest': 'https://img.freepik.com/premium-photo/ancient-forest-ai-generated_1127-13930.jpg',
    'castle': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTrAoGzKjgZxurLbxZ_Dyhtkm1gBqMUMtA87w&s',
    'dungeon': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSTZd9YHDcPOGmD8ezmHB0xD-HfA9O7OpgVyA&s',
    'shop': 'https://img.freepik.com/premium-photo/tavern-like-game_808092-1770.jpg'
}

# Товары в магазине
SHOP_ITEMS = {
    'small_health_potion': {
        'name': '💊 Малое зелье здоровья',
        'description': 'Восстанавливает 30 HP',
        'price': 25,
        'type': 'potion',
        'effect': 30,
        'available': True
    },
    'large_health_potion': {
        'name': '💊 Большое зелье здоровья',
        'description': 'Восстанавливает 60 HP',
        'price': 50,
        'type': 'potion',
        'effect': 60,
        'available': True
    },
    'small_mana_potion': {
        'name': '🔮 Малое зелье маны',
        'description': 'Восстанавливает 20 MP',
        'price': 20,
        'type': 'potion',
        'effect': 20,
        'available': True
    },
    'large_mana_potion': {
        'name': '🔮 Большое зелье маны',
        'description': 'Восстанавливает 40 MP',
        'price': 40,
        'type': 'potion',
        'effect': 40,
        'available': True
    },
    'basic_sword': {
        'name': '⚔️ Обычный меч',
        'description': '+2 к силе',
        'price': 80,
        'type': 'weapon',
        'effect': 2,
        'available': False,  # Пока недоступно
        'message': '🛠 *В разработке* - Оружейник уехал на ярмарку!'
    },
    'hunting_bow': {
        'name': '🏹 Охотничий лук',
        'description': '+2 к ловкости',
        'price': 80,
        'type': 'weapon',
        'effect': 2,
        'available': False,  # Пока недоступно
        'message': '🛠 *В разработке* - Мастер по лукам еще не вернулся!'
    },
    'wisdom_scroll': {
        'name': '📖 Свиток мудрости',
        'description': '+2 к интеллекту',
        'price': 80,
        'type': 'artifact',
        'effect': 2,
        'available': False,  # Пока недоступно
        'message': '🛠 *В разработке* - Мудрец ушел в медитацию!'
    }
}

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def create_progress_bar(current, maximum, length=10):
    """Создает текстовый индикатор прогресса"""
    if maximum <= 0:
        return "▯" * length
    
    percent = current / maximum
    filled = int(length * percent)
    empty = length - filled
    
    # Используем разные символы для разных уровней заполнения
    if percent >= 1.0:
        return "█" * length
    elif percent >= 0.7:
        bar = "▓" * filled + "░" * empty
    elif percent >= 0.4:
        bar = "▒" * filled + "░" * empty
    else:
        bar = "░" * filled + "░" * empty
    
    return bar

def get_health_bar(current, maximum, length=15):
    """Создает индикатор здоровья"""
    if maximum <= 0:
        return "▯" * length
    
    percent = current / maximum
    filled = int(length * percent)
    empty = length - filled
    
    # Разные символы в зависимости от уровня здоровья
    if percent >= 0.7:
        bar = "🟩" * filled + "⬜" * empty
    elif percent >= 0.4:
        bar = "🟨" * filled + "⬜" * empty
    elif percent >= 0.1:
        bar = "🟧" * filled + "⬜" * empty
    else:
        bar = "🟥" * filled + "⬜" * empty
    
    return f"{bar} {current}/{maximum}"

def get_mana_bar(current, maximum, length=10):
    """Создает индикатор маны"""
    if maximum <= 0:
        return "▯" * length
    
    percent = current / maximum
    filled = int(length * percent)
    empty = length - filled
    
    bar = "🟦" * filled + "⬜" * empty
    return f"{bar} {current}/{maximum}"

def get_xp_progress(level, experience):
    """Рассчитывает прогресс опыта для текущего уровня"""
    # Для уровня 1 нужно 0 XP, для уровня 2 - 100 XP, для уровня 3 - 300 XP и т.д.
    # Текущая система: level * 100 XP для следующего уровня
    
    # Опыт, необходимый для следующего уровня
    xp_for_next_level = level * 100
    
    # Опыт, накопленный на текущем уровне
    # Для расчета нужно знать, сколько опыта уже было потрачено на предыдущие уровни
    # Для уровня 1: 0 XP потрачено, для уровня 2: 100 XP потрачено, для уровня 3: 300 XP и т.д.
    # Формула: (level-1) * level * 100 / 2
    
    xp_spent = 0
    if level > 1:
        xp_spent = ((level - 1) * level * 100) // 2
    
    # Текущий опыт на уровне
    current_xp_on_level = experience - xp_spent
    
    # Максимальный опыт на этом уровне
    max_xp_on_level = level * 100
    
    # Процент заполнения
    percent = min(current_xp_on_level / max_xp_on_level, 1.0) if max_xp_on_level > 0 else 0
    
    return current_xp_on_level, max_xp_on_level, percent

def get_xp_bar(level, experience, length=10):
    """Создает индикатор опыта"""
    current_xp, max_xp, percent = get_xp_progress(level, experience)
    
    if max_xp <= 0:
        return "▯" * length
    
    filled = int(length * percent)
    empty = length - filled
    
    # Символы для индикатора опыта
    if percent >= 1.0:
        bar = "⭐" * length
    else:
        bar = "✨" * filled + "⚫" * empty
    
    return f"{bar} {current_xp}/{max_xp} XP"

# --- КЛАВИАТУРЫ ---

def get_main_menu_keyboard():
    """Клавиатура главного меню"""
    keyboard = [
        [InlineKeyboardButton("📜 Герой", callback_data='profile')],
        [InlineKeyboardButton("⚔️ НА БИТВУ!", callback_data='battle_menu')],
        [InlineKeyboardButton("🛍 Торговец", callback_data='shop'), InlineKeyboardButton("🏆 Зал славы", callback_data='stats')],
        [InlineKeyboardButton("📜 Свиток помощи", callback_data='help')],
        [InlineKeyboardButton("🔄 Реинкарнация (Сброс)", callback_data='restart')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_race_selection_keyboard():
    """Клавиатура выбора расы"""
    races = get_all_races()
    keyboard = []
    
    for race_key, race_data in races.items():
        keyboard.append([
            InlineKeyboardButton(
                f"{race_data['name']} (💪{race_data['strength']} | 🏹{race_data['agility']} | 🧠{race_data['intelligence']})",
                callback_data=f'race_{race_key}'
            )
        ])
    
    keyboard.append([InlineKeyboardButton("ℹ️ Энциклопедия рас", callback_data='race_info')])
    return InlineKeyboardMarkup(keyboard)

def get_battle_menu_keyboard():
    """Клавиатура меню боя"""
    keyboard = [
        [InlineKeyboardButton("🌲 Волк [Легко]", callback_data='battle_wolf')],
        [InlineKeyboardButton("🪦 Зомби [Средне]", callback_data='battle_zombie')],
        [InlineKeyboardButton("🔮 Маг [Сложно]", callback_data='battle_mage')],
        [InlineKeyboardButton("🔥 Дракон [БОСС]", callback_data='battle_dragon')],
        [InlineKeyboardButton("🔙 Вернуться в лагерь", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_battle_action_keyboard():
    """Клавиатура действий в бою"""
    keyboard = [
        [InlineKeyboardButton("⚔️ УДАР", callback_data='attack'), InlineKeyboardButton("🛡️ БЛОК", callback_data='defend')],
        [InlineKeyboardButton("✨ МАГИЯ РАСЫ", callback_data='ability')],
        [InlineKeyboardButton("🏃 БЕЖАТЬ", callback_data='flee')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_shop_keyboard(character=None):
    """Клавиатура магазина"""
    keyboard = []
    
    if character:
        gold = character['gold']
        
        # Доступные зелья
        keyboard.append([
            InlineKeyboardButton(
                f"💊 Малое зелье здоровья (30 HP) - 25💰",
                callback_data='buy_small_health_potion'
            )
        ])
        
        keyboard.append([
            InlineKeyboardButton(
                f"💊 Большое зелье здоровья (60 HP) - 50💰",
                callback_data='buy_large_health_potion'
            )
        ])
        
        keyboard.append([
            InlineKeyboardButton(
                f"🔮 Малое зелье маны (20 MP) - 20💰",
                callback_data='buy_small_mana_potion'
            )
        ])
        
        keyboard.append([
            InlineKeyboardButton(
                f"🔮 Большое зелье маны (40 MP) - 40💰",
                callback_data='buy_large_mana_potion'
            )
        ])
        
        # Недоступное оружие (серая кнопка)
        keyboard.append([
            InlineKeyboardButton(
                f"⚔️ Обычный меч (+2 силы) - 80💰 [НЕТ В НАЛИЧИИ]",
                callback_data='unavailable_weapon'
            )
        ])
        
        keyboard.append([
            InlineKeyboardButton(
                f"🏹 Охотничий лук (+2 ловк.) - 80💰 [НЕТ В НАЛИЧИИ]",
                callback_data='unavailable_weapon'
            )
        ])
        
        keyboard.append([
            InlineKeyboardButton(
                f"📖 Свиток мудрости (+2 инт.) - 80💰 [НЕТ В НАЛИЧИИ]",
                callback_data='unavailable_artifact'
            )
        ])
        
        # Информация о золоте и кнопка назад
        keyboard.append([
            InlineKeyboardButton(f"💰 Твой баланс: {gold}", callback_data='balance_info')
        ])
        
        keyboard.append([
            InlineKeyboardButton("🛒 Мой инвентарь", callback_data='show_inventory'),
            InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')
        ])
    
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
        caption=f"🏰 *ДОБРО ПОЖАЛОВАТЬ В МИР ГЕРОЕВ!* 🏰\n\n"
                f"👋 Приветствую тебя, путник *{user.first_name}*!\n\n"
                f"📜 _Древние легенды гласят, что именно ты изменишь судьбу этого мира._\n"
                f"Ты стоишь на главной площади деревни. Впереди — великие свершения!"
    )
    
    # Проверяем, есть ли у пользователя персонаж
    character = get_character(user.id)
    
    if character:
        # Если персонаж уже есть, показываем главное меню
        await update.message.reply_text(
            f"⚔️ С возвращением, *{character['character_name']}*!\nТвой меч все еще остер.",
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return MAIN_MENU
    else:
        # Если персонажа нет, начинаем создание
        await update.message.reply_text(
            f"✨ *Создание Легенды*\n\n"
            f"Прежде чем отправиться в путь, выбери своё происхождение:",
            reply_markup=get_race_selection_keyboard(),
            parse_mode='Markdown'
        )
        return CHOOSE_RACE

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда помощи"""
    help_text = """
📜 *ПУТЕВОДИТЕЛЬ ГЕРОЯ*

🕹 **Управление:**
/start - Вернуться к воротам мира (Главное меню)
/help - Развернуть этот свиток

👤 **Создание героя:**
1. Выбери расу (влияет на стиль боя)
2. Назови героя (это имя войдет в историю)

⚔️ **Классы и Бонусы:**
👨 **Человек** — `Баланс` (+1 ко всем статам)
🧝 **Эльф** — `Магия` (+50% маны)
⚒️ **Дварф** — `Живучесть` (+20% здоровья)
👹 **Орк** — `Ярость` (Рискованные, но мощные атаки)

💊 **Магазин:**
• Зелья здоровья - Быстрое восстановление в бою
• Зелья маны - Восполнение магической энергии
• *Оружие и артефакты пока недоступны*

🔄 **Регенерация:**
• Здоровье: 5% каждые 5 минут
• Мана: 10% каждые 5 минут
_Отдыхай между боями!_

🗡 **Тактика боя:**
• ⚔️ *Атака* - Базовый удар оружием
• 🛡️ *Защита* - Снижает урон на 50%
• ✨ *Способность* - Уникальный навык твоей расы
• 🏃 *Сбежать* - Шанс 50% покинуть бой

_Удачи, герой! Пусть боги хранят тебя._ 🏹
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
        info_text = "📚 *ЭНЦИКЛОПЕДИЯ РАС*\n━━━━━━━━━━━━━━━━\n"
        
        for race_key, race_data in races.items():
            info_text += (
                f"🔸 *{race_data['name']}*\n"
                f"├ 💪 Сила: `{race_data['strength']}`\n"
                f"├ 🏹 Ловкость: `{race_data['agility']}`\n"
                f"├ 🧠 Интеллект: `{race_data['intelligence']}`\n"
                f"├ ❤️ HP: `{race_data['health']}` | 🔮 MP: `{race_data['mana']}`\n"
                f"└ ✨ _Навык: {race_data['racial_ability']}_\n\n"
            )
        
        await query.edit_message_text(
            text=info_text + "👇 *Сделай свой выбор:*",
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
        caption=f"🎭 Твой выбор: *{race_data['name']}*\n━━━━━━━━━━━━━━━━\n"
                f"📊 *Базовые параметры:*\n"
                f"💪 Сила: `{race_data['strength']}`\n"
                f"🏹 Ловкость: `{race_data['agility']}`\n"
                f"🧠 Интеллект: `{race_data['intelligence']}`\n\n"
                f"❤️ Здоровье: `{race_data['health']}`\n"
                f"🔮 Мана: `{race_data['mana']}`\n\n"
                f"✨ *Особый дар:* _{race_data['racial_ability']}_",
        parse_mode='Markdown'
    )
    
    await query.message.reply_text(
        f"✍️ Теперь назови героя! \n*Введи имя (2-20 символов):*",
        parse_mode='Markdown'
    )
    return ENTER_NAME

async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ввода имени"""
    user = update.message.from_user
    character_name = update.message.text.strip()
    
    # Валидация имени
    if len(character_name) < 2 or len(character_name) > 20:
        await update.message.reply_text(
            "❌ *Ошибка летописца!*\nИмя должно быть от 2 до 20 символов. Попробуй еще раз:",
            parse_mode='Markdown'
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
            caption=f"🎉 *РОЖДЕНИЕ ГЕРОЯ!*\n\n"
                   f"🏷️ *Имя:* {character_name}\n"
                   f"🎭 *Раса:* {race_data['name']}\n"
                   f"✨ *Дар:* {race_data['racial_ability']}\n\n"
                   f"_Мир открыт перед тобой!_",
            parse_mode='Markdown'
        )
        
        await update.message.reply_text(
            f"Твоё приключение начинается! Куда направимся?",
            reply_markup=get_main_menu_keyboard()
        )
        return MAIN_MENU
    else:
        await update.message.reply_text(
            f"❌ Ошибка магии: {message}\n\n"
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
        await show_shop(query, user_id)
        return SHOP_MENU
    
    elif data == 'stats':
        await show_stats(query, user_id)
        return MAIN_MENU
    
    elif data == 'help':
        await show_help(query)
        return MAIN_MENU
    
    elif data == 'restart':
        await query.edit_message_text(
            text="🌪 *Магия времени...*\nПерезапускаю мир.\nНапиши /start, чтобы переродиться.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

async def show_profile(query, user_id):
    """Показ профиля персонажа"""
    character = get_character(user_id)
    
    if not character:
        await query.edit_message_text(
            text="❌ Герой не найден!",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    races = get_all_races()
    race_data = races.get(character['race'], {})
    image_url = IMAGE_URLS.get(character['race'], IMAGE_URLS['human'])
    
    # Создаем индикаторы
    health_bar = get_health_bar(character['health'], character['max_health'])
    mana_bar = get_mana_bar(character['mana'], character['max_mana'])
    xp_bar = get_xp_bar(character['level'], character['experience'])
    
    # Проверяем регенерацию
    last_regen = character.get('last_regeneration')
    regen_info = ""
    if last_regen:
        if isinstance(last_regen, str):
            last_regen = datetime.fromisoformat(last_regen.replace('Z', '+00:00'))
        
        time_diff = datetime.now() - last_regen
        if time_diff.total_seconds() >= 300:
            regen_info = "\n🔄 *Готов к регенерации!*"
        else:
            minutes_left = int((300 - time_diff.total_seconds()) / 60)
            seconds_left = int(300 - time_diff.total_seconds()) % 60
            regen_info = f"\n⏳ *Регенерация через:* {minutes_left}:{seconds_left:02d}"
    
    # Сначала отправляем изображение персонажа
    await query.message.reply_photo(
        photo=image_url,
        caption=f"👤 *ПАСПОРТ ГЕРОЯ: {character['character_name']}*\n"
               f"⭐ Уровень {character['level']} • {race_data.get('name', '')}\n\n"
               f"❤️ ЗДОРОВЬЕ\n{health_bar}\n\n"
               f"🔮 МАНА\n{mana_bar}\n\n"
               f"✨ ОПЫТ\n{xp_bar}{regen_info}",
        parse_mode='Markdown'
    )
    
    # Получаем инвентарь
    inventory = get_inventory(user_id)
    inventory_text = "🎒 *Инвентарь пуст*"
    if inventory:
        inventory_text = "🎒 *ИНВЕНТАРЬ*\n"
        for item in inventory:
            inventory_text += f"• {item['item_name']}: {item['quantity']} шт.\n"
    
    profile_text = (
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⚔️ *БОЕВЫЕ ПАРАМЕТРЫ*\n"
        f"💪 Сила:      `{character['strength']}`\n"
        f"🏹 Ловкость:  `{character['agility']}`\n"
        f"🧠 Интеллект: `{character['intelligence']}`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 *БОГАТСТВО*\n"
        f"Золото: `{character['gold']}` монет\n\n"
        f"📜 *Достижения:*\n"
        f"⚔️ Побед: {character.get('battle_wins', 0)} | 💀 Поражений: {character.get('battle_losses', 0)}\n\n"
        f"{inventory_text}\n\n"
        f"✨ *Расовый навык:*\n_{race_data.get('racial_ability', 'Нет')}_"
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
        caption="🌲 *ОКРАИНА ЛЕСА* 🌲\n\n"
                "Ты чувствуешь на себе чьи1-то взгляды. Кто станет твоей целью сегодня?\n\n"
                "*Выбери уровень угрозы:*",
        parse_mode='Markdown'
    )
    
    await query.message.reply_text(
        text="🐺 *Волк* - Разминка для новичка\n"
             "🧟 *Зомби* - Требует сноровки\n"
             "🧙 *Маг* - Испытание для опытных\n"
             "🐉 *Дракон* - Смертельная опасность!",
        parse_mode='Markdown',
        reply_markup=get_battle_menu_keyboard()
    )

async def show_shop(query, user_id):
    """Показ магазина"""
    character = get_character(user_id)
    
    if not character:
        await query.edit_message_text(
            text="❌ Герой не найден!",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    await query.message.reply_photo(
        photo=IMAGE_URLS['shop'],
        caption="🛖 *ЛАВКА СТАРОГО ТОРГОВЦА* 🛖\n\n"
                "_Пахнет травами и стариной. На прилавке разложены снадобья:_\n\n"
                f"💰 *Твой кошелек:* `{character['gold']}` золотых",
        parse_mode='Markdown'
    )
    
    shop_text = (
        "💊 *ЗЕЛЬЯ ЗДОРОВЬЯ*\n"
        "• Малое (+30 HP) — `25 золота`\n"
        "• Большое (+60 HP) — `50 золота`\n\n"
        "🔮 *ЭЛИКСИРЫ МАНЫ*\n"
        "• Малый (+20 MP) — `20 золота`\n"
        "• Большой (+40 MP) — `40 золота`\n\n"
        "⚔️ *Оружие временно отсутствует*\n"
        "🏹 *Луки временно отсутствуют*\n"
        "📖 *Артефакты временно отсутствуют*\n\n"
        "_Торговец бормочет: 'Держи зелья, герой. Остальное — когда повезёт...'_"
    )
    
    await query.message.reply_text(
        text=shop_text,
        reply_markup=get_shop_keyboard(character),
        parse_mode='Markdown'
    )

async def shop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик магазина"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == 'back_to_main':
        await query.edit_message_text(
            text="🔙 Ты вышел из лавки на улицу...",
            reply_markup=get_main_menu_keyboard()
        )
        return MAIN_MENU
    
    elif data == 'balance_info':
        character = get_character(user_id)
        if character:
            await query.answer(f"💰 У тебя {character['gold']} золота", show_alert=True)
        return SHOP_MENU
    
    elif data == 'show_inventory':
        await show_inventory(query, user_id)
        return SHOP_MENU
    
    elif data in ['unavailable_weapon', 'unavailable_artifact']:
        item_type = 'weapon' if 'weapon' in data else 'artifact'
        item = next((item for item in SHOP_ITEMS.values() if item['type'] == item_type and not item['available']), None)
        if item:
            await query.answer(item['message'], show_alert=True)
        return SHOP_MENU
    
    elif data.startswith('buy_'):
        item_key = data[4:]  # Убираем 'buy_'
        
        if item_key not in SHOP_ITEMS:
            await query.answer("❌ Такого товара нет в продаже!", show_alert=True)
            return SHOP_MENU
        
        item = SHOP_ITEMS[item_key]
        
        if not item['available']:
            await query.answer("❌ Этот товар временно недоступен!", show_alert=True)
            return SHOP_MENU
        
        # Покупаем предмет
        success, message = buy_item(
            user_id=user_id,
            item_type=item['type'],
            item_name=item['name'],
            price=item['price'],
            effect_amount=item.get('effect')
        )
        
        if success:
            # Обновляем информацию о персонаже
            character = get_character(user_id)
            
            # Показываем подтверждение покупки
            await query.message.reply_text(
                f"✅ *УСПЕШНАЯ ПОКУПКА!*\n\n"
                f"🎁 Ты приобрел: {item['name']}\n"
                f"📝 {item['description']}\n"
                f"💰 Потрачено: {item['price']} золота\n"
                f"💳 Осталось: {character['gold']} золота\n\n"
                f"_Предмет добавлен в инвентарь_",
                parse_mode='Markdown'
            )
            
            # Обновляем магазин
            await query.message.reply_text(
                text="🛖 *Что еще желаешь?*",
                reply_markup=get_shop_keyboard(character),
                parse_mode='Markdown'
            )
        else:
            await query.answer(f"❌ {message}", show_alert=True)
        
        return SHOP_MENU

async def show_inventory(query, user_id):
    """Показ инвентаря"""
    inventory = get_inventory(user_id)
    character = get_character(user_id)
    
    if not inventory:
        await query.message.reply_text(
            "🎒 *Твой инвентарь пуст!*\n_Загляни в лавку торговца..._",
            reply_markup=get_shop_keyboard(character),
            parse_mode='Markdown'
        )
    else:
        inventory_text = "🎒 *ТВОЙ ИНВЕНТАРЬ*\n━━━━━━━━━━━━━━━━\n"
        total_items = 0
        
        for item in inventory:
            inventory_text += f"• {item['item_name']}: `{item['quantity']} шт.`\n"
            total_items += item['quantity']
        
        inventory_text += f"\n📦 *Всего предметов:* `{total_items}`"
        
        await query.message.reply_text(
            text=inventory_text,
            reply_markup=get_shop_keyboard(character),
            parse_mode='Markdown'
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
    
    # Получаем прогресс опыта
    current_xp, max_xp, percent = get_xp_progress(character['level'], character['experience'])
    
    stats_text = (
        f"🏆 *ЗАЛ СЛАВЫ: {character['character_name']}*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⭐ *Уровень:* `{character['level']}`\n"
        f"✨ *Опыт:* `{character['experience']}` XP\n"
        f"📊 *Прогресс:* `{current_xp}/{max_xp}` ({percent:.1%})\n"
        f"{get_xp_bar(character['level'], character['experience'], length=15)}\n\n"
        f"❤️ *Здоровье:* `{character['health']}/{character['max_health']}`\n"
        f"{get_health_bar(character['health'], character['max_health'], length=15)}\n\n"
        f"🔮 *Мана:* `{character['mana']}/{character['max_mana']}`\n"
        f"{get_mana_bar(character['mana'], character['max_mana'], length=10)}\n\n"
        f"💰 *Богатство:* `{character['gold']}` золотых\n\n"
        f"⚔️ *Боевая сводка:*\n"
        f"✅ Побед: `{character.get('battle_wins', 0)}`\n"
        f"❌ Поражений: `{character.get('battle_losses', 0)}`\n"
        f"📉 Всего битв: `{total_battles}`\n"
        f"📈 Эффективность: `{win_rate:.1f}%`\n\n"
        f"📅 *Летопись:*\n"
        f"Рожден: {character['created_at'].strftime('%d.%m.%Y')}\n"
        f"Замечен: {character['last_active'].strftime('%d.%m.%Y %H:%M')}"
    )
    
    await query.edit_message_text(
        text=stats_text,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )

async def show_help(query):
    """Показ помощи"""
    help_text = """
📜 *ПУТЕВОДИТЕЛЬ ГЕРОЯ*

🕹 **Управление:**
Используй кнопки под сообщениями.

🏚 **Места:**
• 👤 **Герой** - Твой статус и инвентарь
• ⚔️ **Битва** - Охота на монстров
• 🛍 **Торговец** - Покупка зелий

💊 **Магазин:**
• Малое зелье здоровья (30 HP) - 25💰
• Большое зелье здоровья (60 HP) - 50💰
• Малое зелье маны (20 MP) - 20💰
• Большое зелье маны (40 MP) - 40💰

🔄 **Регенерация:**
• Здоровье восстанавливается 5% каждые 5 минут
• Мана восстанавливается 10% каждые 5 минут

🗡 **Советы бывалых:**
1. _Не лезь на Дракона первым уровнем!_
2. Орки сильны, но ранят себя в ярости.
3. Эльфы часто наносят критические удары магией.
4. Дварфы живут дольше благодаря защите.
5. Используй зелья в тяжелых битвах!

_Удачи на тропе войны!_ 🐾
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
        # Удаляем сессию боя если существует
        if user_id in battle_sessions:
            del battle_sessions[user_id]
        
        await query.edit_message_text(
            text="🔙 Ты возвращаешься в безопасность деревни...",
            reply_markup=get_main_menu_keyboard()
        )
        return MAIN_MENU
    
    elif data.startswith('battle_'):
        enemy_type = data[7:]  # Убираем 'battle_'
        await start_battle(query, user_id, enemy_type)
        return IN_BATTLE

async def start_battle(query, user_id, enemy_type):
    """Начало боя"""
    character = get_character(user_id)
    
    if not character:
        await query.edit_message_text(
            text="❌ Герой потерян во времени!",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    # Определяем параметры врага
    enemies = {
        'wolf': {
            'name': '🐺 Бешеный Волк',
            'health': 30,
            'max_health': 30,
            'min_damage': 3,
            'max_damage': 8,
            'exp': 15,
            'gold': 10,
            'description': 'Его глаза горят голодом, а клыки обнажены.',
            'image': IMAGE_URLS['wolf']
        },
        'zombie': {
            'name': '🧟 Гниющий Зомби',
            'health': 50,
            'max_health': 50,
            'min_damage': 5,
            'max_damage': 12,
            'exp': 25,
            'gold': 20,
            'description': 'Медленный, но его удары заражают страхом.',
            'image': IMAGE_URLS['zombie']
        },
        'mage': {
            'name': '🧙 Темный Чернокнижник',
            'health': 40,
            'max_health': 40,
            'min_damage': 8,
            'max_damage': 18,
            'exp': 40,
            'gold': 35,
            'description': 'Окружен темной аурой и шепчет заклинания.',
            'image': IMAGE_URLS['mage']
        },
        'dragon': {
            'name': '🐉 Древний Дракон',
            'health': 100,
            'max_health': 100,
            'min_damage': 15,
            'max_damage': 30,
            'exp': 100,
            'gold': 80,
            'description': 'Владыка небес. Его пламя сжигает все живое.',
            'image': IMAGE_URLS['dragon']
        }
    }
    
    enemy = enemies.get(enemy_type, enemies['wolf'])
    
    # Создаем сессию боя
    battle_sessions[user_id] = {
        'enemy': enemy.copy(),
        'character': character.copy(),
        'turn': 0,
        'player_defending': False,
        'enemy_defending': False,
        'log': [],
        'enemy_type': enemy_type
    }
    
    # Отправляем изображение врага
    await query.message.reply_photo(
        photo=enemy['image'],
        caption=f"🔥 *БОЙ НАЧАЛСЯ!* 🔥\n━━━━━━━━━━━━━━━━\n"
               f"👿 Противник: *{enemy['name']}*\n"
               f"📜 _{enemy['description']}_",
        parse_mode='Markdown'
    )
    
    battle_log = battle_sessions[user_id]['log']
    battle_log.append(f"🆚 *Статус:*")
    
    # Индикатор здоровья игрока
    player_health_bar = get_health_bar(character['health'], character['max_health'], length=10)
    battle_log.append(f"👤 ГЕРОЙ: {player_health_bar}")
    
    # Индикатор здоровья врага
    enemy_health_bar = get_health_bar(enemy['health'], enemy['max_health'], length=10)
    battle_log.append(f"👿 ВРАГ: {enemy_health_bar}")
    
    battle_log.append("━━━━━━━━━━━━━━━━")
    battle_log.append("⚡️ *Твой ход! Действуй!*")
    
    await query.message.reply_text(
        text="\n".join(battle_log),
        reply_markup=get_battle_action_keyboard(),
        parse_mode='Markdown'
    )

async def battle_action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик действий в бою"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    # Проверяем, существует ли сессия боя
    if user_id not in battle_sessions:
        await query.edit_message_text(
            text="❌ Бой уже завершен. Следы врага остыли.",
            reply_markup=get_main_menu_keyboard()
        )
        return MAIN_MENU
    
    battle_data = battle_sessions[user_id]
    character = battle_data['character']
    enemy = battle_data['enemy']
    
    # Очищаем лог и увеличиваем ход
    battle_data['log'] = []
    battle_data['turn'] += 1
    
    battle_log = battle_data['log']
    
    # Действие игрока
    if data == 'attack':
        player_damage = random.randint(character['strength'] // 2, character['strength'])
        if battle_data['enemy_defending']:
            player_damage = max(1, player_damage // 2)
            battle_log.append(f"🛡️ Враг в блоке! Ты нанес лишь *{player_damage}* урона.")
        else:
            battle_log.append(f"⚔️ Ты нанес *{player_damage}* урона!")
        enemy['health'] -= player_damage
        
    elif data == 'defend':
        battle_data['player_defending'] = True
        battle_log.append(f"🛡️ Ты поднял щит! Урон будет снижен.")
        
    elif data == 'ability':
        # Использование расовой способности
        if character['race'] == 'human':
            bonus = random.randint(1, 3)
            battle_log.append(f"✨ *Адаптивность!* Характеристики временно выросли на *+{bonus}*!")
            
        elif character['race'] == 'elf':
            if random.random() < 0.3:  # 30% шанс
                damage = character['intelligence'] * 2
                battle_log.append(f"🏹 *КРИТИЧЕСКИЙ ВЫСТРЕЛ!* Магия нанесла *{damage}* урона!")
                enemy['health'] -= damage
            else:
                damage = character['intelligence']
                battle_log.append(f"🏹 Точный выстрел на *{damage}* урона!")
                enemy['health'] -= damage
            
        elif character['race'] == 'dwarf':
            heal_amount = random.randint(5, 15)
            character['health'] = min(character['max_health'], character['health'] + heal_amount)
            battle_data['player_defending'] = True
            battle_log.append(f"🏔 *Каменная кожа!* Восстановлено *{heal_amount}* HP и поднят щит!")
            
        elif character['race'] == 'orc':
            damage = character['strength'] * 2
            self_damage = random.randint(1, 5)
            enemy['health'] -= damage
            character['health'] -= self_damage
            battle_log.append(f"🩸 *ЯРОСТЬ!* Сокрушительный удар на *{damage}*, но ты ранил себя на *{self_damage}*.")
            
    elif data == 'flee':
        flee_chance = random.randint(1, 100)
        if flee_chance > 50:  # 50% шанс сбежать
            battle_log.append("🏃💨 *ПОБЕГ УДАЛСЯ!* Ты растворился в тени...")
            del battle_sessions[user_id]
            await query.edit_message_text(
                text="\n".join(battle_log),
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard()
            )
            return MAIN_MENU
        else:
            battle_log.append("🚫 *НЕУДАЧА!* Враг перекрыл путь к отступлению!")
    
    # Действие врага
    if enemy['health'] > 0:
        enemy_action = random.choice(['attack', 'attack', 'defend'])  # 66% атака
        
        if enemy_action == 'attack':
            enemy_damage = random.randint(enemy['min_damage'], enemy['max_damage'])
            if battle_data['player_defending']:
                enemy_damage = max(1, enemy_damage // 2)
                battle_log.append(f"🛡️ Твой блок поглотил часть урона! Получено *{enemy_damage}* ед.")
            else:
                battle_log.append(f"💔 Враг атаковал тебя на *{enemy_damage}* урона!")
            character['health'] -= enemy_damage
            battle_data['player_defending'] = False
        else:
            battle_data['enemy_defending'] = True
            battle_log.append(f"🛡️ Враг ушел в глухую оборону!")
    
    # Сбрасываем защиту врага после его хода
    battle_data['enemy_defending'] = False
    
    # Проверка окончания боя
    if character['health'] <= 0:
        battle_log.append("━━━━━━━━━━━━━━━━")
        battle_log.append("💀 *ТЫ ПАЛ В БОЮ...*")
        battle_log.append("Твоя история прервалась на этом месте.")
        
        # Обновляем статистику в БД
        update_character_stats(user_id, 
            health=0,  # Устанавливаем здоровье в 0
            battle_losses=character.get('battle_losses', 0) + 1
        )
        log_battle(user_id, enemy['name'], 'поражение', 0, 0, 0, 0)
        
        del battle_sessions[user_id]
        
        await query.edit_message_text(
            text="\n".join(battle_log),
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard()
        )
        return MAIN_MENU
    
    elif enemy['health'] <= 0:
        battle_log.append("━━━━━━━━━━━━━━━━")
        battle_log.append("🏆 *ВЕЛИКАЯ ПОБЕДА!*")
        battle_log.append(f"Монстр {enemy['name']} повержен!")
        
        # Награда
        exp_gained = enemy['exp']
        gold_gained = enemy['gold']
        
        battle_log.append(f"💰 Трофеи: *{gold_gained}* золота")
        battle_log.append(f"🌟 Опыт: *{exp_gained}* XP")
        
        # Обновляем данные в БД с текущим здоровьем
        update_character_stats(
            user_id, 
            health=character['health'],  # Сохраняем текущее здоровье
            battle_wins=character.get('battle_wins', 0) + 1,
            gold=character['gold'] + gold_gained
        )
        add_experience(user_id, exp_gained)
        add_gold(user_id, gold_gained)
        log_battle(user_id, enemy['name'], 'победа', 0, 0, gold_gained, exp_gained)
        
        del battle_sessions[user_id]
        
        await query.edit_message_text(
            text="\n".join(battle_log),
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard()
        )
        return MAIN_MENU
    
    # Продолжение боя - обновляем индикаторы
    else:
        # Индикатор здоровья игрока
        player_health_bar = get_health_bar(max(0, character['health']), character['max_health'], length=10)
        
        # Индикатор здоровья врага
        enemy_health_bar = get_health_bar(max(0, enemy['health']), enemy['max_health'], length=10)
        
        status_text = (
            f"⚔️ *Ход №{battle_data['turn']}*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"👤 *ТЫ:* {player_health_bar}\n"
            f"👿 *ВРАГ:* {enemy_health_bar}\n\n"
            f"{chr(10).join(battle_log)}\n"  # Вставляем лог действий
            f"━━━━━━━━━━━━━━━━\n"
            f"⚡️ *Твои действия:*"
        )
        
        await query.edit_message_text(
            text=status_text,
            parse_mode='Markdown',
            reply_markup=get_battle_action_keyboard()
        )
        return IN_BATTLE

# --- ОБРАБОТЧИКИ ОШИБОК ---

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена диалога"""
    await update.message.reply_text(
        "🚫 Привал. Напиши /start, чтобы продолжить путь."
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
                "❌ Магический сбой. Попробуй /start"
            )
        elif update and update.message:
            await update.message.reply_text(
                "❌ Магический сбой. Попробуй /start"
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
                    CallbackQueryHandler(battle_menu_handler, pattern='^(battle_|back_to_main)')
                ],
                IN_BATTLE: [
                    CallbackQueryHandler(battle_action_handler, pattern='^(attack|defend|ability|flee)$')
                ],
                SHOP_MENU: [
                    CallbackQueryHandler(shop_handler)
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
