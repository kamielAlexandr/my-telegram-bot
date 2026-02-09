import os
import telebot
import database  # Импортируем функции из database.py
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot import apihelper
import random
import time

# Инициализация бота
TOKEN = os.getenv('TELEGRAM_TOKEN')
if not TOKEN:
    print("❌ ОШИБКА: TELEGRAM_TOKEN не найден в переменных окружения!")
    print("ℹ️ Добавьте TELEGRAM_TOKEN в переменные окружения Railway")
    TOKEN = "placeholder_token"  # Заглушка для продолжения работы

# Настройка прокси для обхода блокировок (если нужно)
apihelper.proxy = {'https': os.getenv('HTTPS_PROXY')} if os.getenv('HTTPS_PROXY') else None

bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

# Константы для бота
IMAGE_URLS = {
    'human': 'https://i126.fastpic.org/thumb/2026/0130/2c/_d2515d33e45fa7ffb5246cacabdaba2c.jpeg',
    'elf': 'https://i126.fastpic.org/thumb/2026/0130/81/_d3d94be5aa45b9239aeb5adc41443081.jpeg',
    'dwarf': 'https://i126.fastpic.org/thumb/2026/0130/5b/_c188fac4eb6d205bd9fc0486c9b9355b.jpeg',
    'orc': 'https://i126.fastpic.org/thumb/2026/0130/20/_b8c1f666bd21bb415e8fb35145eb3e20.jpeg',
    'wolf': 'https://i.pinimg.com/736x/9f/8e/25/9f8e2507aceaa217060d249c308e2a13.jpg',
    'goblin': 'https://img.freepik.com/free-photo/goblin-digital-art_23-2151061965.jpg',
    'slime': 'https://papik.pro/uploads/posts/2023-02/1676176492_papik-pro-p-risunok-sliz-1.jpg',
    'hot_goblin': 'https://i.pinimg.com/736x/c8/26/9c/c8269c5d8631f0081b84de0e481542bb.jpg',
    'zombie': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQRBEAcmeuf4tt0xnFUG1E8wcvZlSkLQcZkUw&s',
    'skeleton': 'https://img.freepik.com/free-photo/skeleton-warrior_23-2150911306.jpg',
    'mage': 'https://abrakadabra.fun/uploads/posts/2022-01/1642490542_3-abrakadabra-fun-p-temnii-mag-art-5.jpg',
    'vampire': 'https://img.freepik.com/free-photo/vampire_23-2150762308.jpg',
    'knight': 'https://i.pinimg.com/originals/92/11/34/9211349d21f146a07aa1e2f920d5c2f4.jpg',
    'demon': 'https://img.freepg'https://img.freepik.com/free-photo/demon_23-2150762325.jpg',
    'dragon': 'https://abrakadabra.fun/uploads/posts/2022-03/1646721873_1-abrakadabra-fun-p-pauk-fantezi-art-1.jpg',
    'shop': 'https://img.freepik.com/premium-photo/tavern-like-game_808092-1770.jpg',
    'levelup': 'https://i.pinimg.com/736x/7f/9a/97/7f9a97fdbbd70577225c213ad8a6e75c.jpg',
    'inventory': 'https://i.imgur.com/6QyTK2F.jpeg'
}

# Товары в магазине
SHOP_ITEMS = {
    'small_health_potion': {
        'name': '💊 Малое зелье здоровья',
        'description': 'Восстанавливает 20 HP',
        'price': 40,
        'type': 'potion',
        'effect': 20,
        'available': True
    },
    'large_health_potion': {
        'name': '💊 Большое зелье здоровья',
        'description': 'Восстанавливает 40 HP',
        'price': 75,
        'type': 'potion',
        'effect': 40,
        'available': True
    },
    'small_mana_potion': {
        'name': '🔮 Малое зелье маны',
        'description': 'Восстанавливает 15 MP',
        'price': 35,
        'type': 'potion',
        'effect': 15,
        'available': True
    },
    'large_mana_potion': {
        'name': '🔮 Большое зелье маны',
        'description': 'Восстанавливает 30 MP',
        'price': 65,
        'type': 'potion',
        'effect': 30,
        'available': True
    }
}

# Базовые параметры врагов
BASE_ENEMIES = {
    'wolf': {
        'name': '🐺 Бешеный Волк',
        'base_health': 35,
        'base_min_physical_damage': 5,
        'base_max_physical_damage': 8,
        'base_exp': 12,
        'base_gold': 8,
        'rank': 'E',
        'description': 'Его глаза горят голодом, а клыки обнажены.',
        'image': IMAGE_URLS['wolf'],
        'difficulty': 'easy'
    },
    'goblin': {
        'name': '👹 Гоблин-разведчик',
        'base_health': 40,
        'base_min_physical_damage': 6,
        'base_max_physical_damage': 10,
        'base_exp': 16,
        'base_gold': 12,
        'rank': 'E',
        'description': 'Мелкий и трусливый, но опасный в стае.',
        'image': IMAGE_URLS['goblin'],
        'difficulty': 'easy'
    },
    'slime': {
        'name': '🟢 Ядовитая Слизь',
        'base_health': 45,
        'base_min_physical_damage': 3,
        'base_max_physical_damage': 8,
        'base_exp': 10,
        'base_gold': 7,
        'rank': 'E',
        'description': 'Желейная масса, медленная, но ядовитая.',
        'image': IMAGE_URLS['slime'],
        'difficulty': 'easy'
    }
}

def create_enemy(enemy_key, player_level):
    """Создает врага с параметрами, зависящими от уровня игрока"""
    if enemy_key not in BASE_ENEMIES:
        return None
    
    base_enemy = BASE_ENEMIES[enemy_key].copy()
    level_multiplier = 1.0 + (player_level - 1) * 0.15
    
    enemy = {
        'key': enemy_key,
        'name': base_enemy['name'],
        'health': int(base_enemy['base_health'] * level_multiplier),
        'max_health': int(base_enemy['base_health'] * level_multiplier),
        'min_damage': int(base_enemy['base_min_physical_damage'] * level_multiplier),
        'max_damage': int(base_enemy['base_max_physical_damage'] * level_multiplier),
        'exp': int(base_enemy['base_exp'] * level_multiplier),
        'gold': int(base_enemy['base_gold'] * level_multiplier),
        'rank': base_enemy['rank'],
        'description': base_enemy['description'],
        'image': base_enemy['image'],
        'difficulty': base_enemy['difficulty']
    }
    
    return enemy

# Инициализация базы данных при старте
print("=" * 50)
print("🔄 Инициализация базы данных...")
try:
    database.init_db()
    print("✅ База данных инициализирована")
except Exception as e:
    print(f"❌ Ошибка при инициализации БД: {e}")

print(f"🤖 Бот инициализирован с токеном: {TOKEN[:10]}...")
print("=" * 50)

# ==================== ОСНОВНЫЕ КОМАНДЫ ====================

@bot.message_handler(commands=['start'])
def start_command(message):
    """Обработка команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    # Проверяем, есть ли уже персонаж у пользователя
    character = database.get_character(user_id)
    
    if character:
        # Персонаж уже существует
        keyboard = InlineKeyboardMarkup()
        keyboard.row(
            InlineKeyboardButton("👤 Профиль", callback_data="profile"),
            InlineKeyboardButton("🎒 Инвентарь", callback_data="inventory")
        )
        keyboard.row(
            InlineKeyboardButton("⚔️ Атаковать", callback_data="battle_menu"),
            InlineKeyboardButton("🏪 Магазин", callback_data="shop_menu")
        )
        keyboard.row(
            InlineKeyboardButton("📊 Статистика", callback_data="stats"),
            InlineKeyboardButton("🏆 Топ игроков", callback_data="top_players")
        )
        
        welcome_text = (
            f"✨ Добро пожаловать обратно, {character['character_name']}!\n\n"
            f"Ты {database.get_all_races()[character['race']]['name']} {character['rank']}-ранга, уровень {character['level']}.\n"
            f"❤️ Здоровье: {character['health']}/{character['max_health']}\n"
            f"🔮 Мана: {character['mana']}/{character['max_mana']}\n"
            f"💰 Золото: {character['gold']}\n\n"
            f"Выбери действие:"
        )
        
        try:
            bot.send_message(
                message.chat.id,
                welcome_text,
                reply_markup=keyboard
            )
        except Exception as e:
            print(f"❌ Ошибка отправки сообщения: {e}")
            bot.send_message(message.chat.id, "Добро пожаловать обратно! Используйте /profile для просмотра профиля.")
        
    else:
        # Создаем нового персонажа
        bot.send_message(
            message.chat.id,
            f"🎮 Добро пожаловать в мир приключений, {username}!\n\n"
            "Это мир, полный опасностей и возможностей. Прежде чем начать, тебе нужно создать своего персонажа.\n\n"
            "Выбери расу для своего героя:"
        )
        show_race_selection(message)

def show_race_selection(message):
    """Показывает выбор расы"""
    races = database.get_all_races()
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    for race_key, race_info in races.items():
        keyboard.add(InlineKeyboardButton(
            race_info['name'], 
            callback_data=f"create_{race_key}"
        ))
    
    bot.send_message(
        message.chat.id,
        "📝 Выбери расу своего персонажа:",
        reply_markup=keyboard
    )

@bot.message_handler(commands=['profile'])
def profile_command(message):
    """Показывает профиль персонажа"""
    user_id = message.from_user.id
    character = database.get_character(user_id)
    
    if not character:
        bot.send_message(message.chat.id, "❌ У тебя еще нет персонажа! Используй /start для создания.")
        return
    
    race_info = database.get_all_races().get(character['race'], {})
    
    profile_text = (
        f"👤 <b>Профиль персонажа</b>\n\n"
        f"<b>Имя:</b> {character['character_name']}\n"
        f"<b>Раса:</b> {race_info.get('name', 'Неизвестно')}\n"
        f"<b>Уровень:</b> {character['level']}\n"
        f"<b>Ранг:</b> {character['rank']}\n"
        f"<b>Опыт:</b> {character['experience']}\n\n"
        f"<b>Характеристики:</b>\n"
        f"💪 Сила: {character['strength']}\n"
        f"🏃‍♂️ Ловкость: {character['agility']}\n"
        f"🧠 Интеллект: {character['intelligence']}\n\n"
        f"<b>Состояние:</b>\n"
        f"❤️ Здоровье: {character['health']}/{character['max_health']}\n"
        f"🔮 Мана: {character['mana']}/{character['max_mana']}\n"
        f"💰 Золото: {character['gold']}\n\n"
        f"<b>Очки характеристик:</b> {character['stat_points']}\n"
    )
    
    if character['stat_points'] > 0:
        keyboard = InlineKeyboardMarkup(row_width=3)
        keyboard.add(
            InlineKeyboardButton("💪 +1 Сила", callback_data="stat_strength"),
            InlineKeyboardButton("🏃‍♂️ +1 Ловкость", callback_data="stat_agility"),
            InlineKeyboardButton("🧠 +1 Интеллект", callback_data="stat_intelligence")
        )
        profile_text += "\n🎯 У тебя есть очки характеристик для распределения!"
    else:
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu"))
    
    bot.send_message(
        message.chat.id,
        profile_text,
        reply_markup=keyboard
    )

@bot.message_handler(commands=['shop'])
def shop_command(message):
    """Показывает магазин"""
    user_id = message.from_user.id
    character = database.get_character(user_id)
    
    if not character:
        bot.send_message(message.chat.id, "❌ У тебя еще нет персонажа! Используй /start для создания.")
        return
    
    shop_text = "🏪 <b>Магазин приключений</b>\n\n"
    shop_text += f"💰 Твой баланс: {character['gold']} золота\n\n"
    shop_text += "<b>Доступные товары:</b>\n\n"
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    for i, (item_key, item_info) in enumerate(SHOP_ITEMS.items()):
        shop_text += f"{item_info['name']}\n"
        shop_text += f"📝 {item_info['description']}\n"
        shop_text += f"💰 Цена: {item_info['price']} золота\n"
        shop_text += "─" * 20 + "\n"
        
        callback_data = f"buy_{item_key}"
        keyboard.add(InlineKeyboardButton(
            f"{item_info['name']} - {item_info['price']}💰", 
            callback_data=callback_data
        ))
    
    keyboard.add(InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu"))
    
    bot.send_message(
        message.chat.id,
        shop_text,
        reply_markup=keyboard
    )

@bot.message_handler(commands=['inventory'])
def inventory_command(message):
    """Показывает инвентарь"""
    user_id = message.from_user.id
    character = database.get_character(user_id)
    
    if not character:
        bot.send_message(message.chat.id, "❌ У тебя еще нет персонажа! Используй /start для создания.")
        return
    
    inventory = database.get_inventory(user_id)
    
    if not inventory:
        inventory_text = "🎒 <b>Твой инвентарь пуст</b>\n\n"
        inventory_text += "Посети 🏪 Магазин, чтобы купить предметы!"
    else:
        inventory_text = "🎒 <b>Твой инвентарь</b>\n\n"
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        for item in inventory:
            inventory_text += f"{item['item_name']} ×{item['quantity']}\n"
            if item['effect_amount'] > 0:
                inventory_text += f"📊 Эффект: +{item['effect_amount']}\n"
            inventory_text += "─" * 20 + "\n"
            
            if 'health_potion' in item['item_key']:
                keyboard.add(InlineKeyboardButton(
                    f"💊 Исп. {item['item_name']}", 
                    callback_data=f"use_{item['item_key']}"
                ))
            elif 'mana_potion' in item['item_key']:
                keyboard.add(InlineKeyboardButton(
                    f"🔮 Исп. {item['item_name']}", 
                    callback_data=f"use_{item['item_key']}"
                ))
    
    keyboard.add(InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu"))
    
    bot.send_message(
        message.chat.id,
        inventory_text,
        reply_markup=keyboard
    )

@bot.message_handler(commands=['battle'])
def battle_command(message):
    """Начинает битву"""
    user_id = message.from_user.id
    character = database.get_character(user_id)
    
    if not character:
        bot.send_message(message.chat.id, "❌ У тебя еще нет персонажа! Используй /start для создания.")
        return
    
    # Проверяем здоровье
    if character['health'] <= 0:
        bot.send_message(message.chat.id, "💀 Ты слишком слаб для битвы! Подожди регенерации или используй зелье здоровья.")
        return
    
    # Создаем случайного врага
    enemy_key = random.choice(['wolf', 'goblin', 'slime'])
    enemy = create_enemy(enemy_key, character['level'])
    
    if not enemy:
        bot.send_message(message.chat.id, "❌ Ошибка при создании врага!")
        return
    
    battle_text = (
        f"⚔️ <b>БОЕВАЯ СИТУАЦИЯ!</b>\n\n"
        f"Ты встретил {enemy['name']}!\n"
        f"{enemy['description']}\n\n"
        f"<b>Характеристики врага:</b>\n"
        f"❤️ Здоровье: {enemy['health']}\n"
        f"⚔️ Урон: {enemy['min_damage']}-{enemy['max_damage']}\n\n"
        f"<b>Твое состояние:</b>\n"
        f"❤️ Здоровье: {character['health']}/{character['max_health']}\n"
        f"🔮 Мана: {character['mana']}/{character['max_mana']}\n\n"
        f"Выбери действие:"
    )
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("⚔️ Атаковать", callback_data=f"attack_{enemy_key}"),
        InlineKeyboardButton("🛡️ Защищаться", callback_data=f"defend_{enemy_key}")
    )
    keyboard.add(
        InlineKeyboardButton("🏃‍♂️ Убежать", callback_data="run_away"),
        InlineKeyboardButton("🎒 Исп. предмет", callback_data="use_in_battle")
    )
    
    try:
        bot.send_photo(
            message.chat.id,
            photo=enemy['image'],
            caption=battle_text,
            reply_markup=keyboard
        )
    except:
        bot.send_message(
            message.chat.id,
            battle_text,
            reply_markup=keyboard
        )

@bot.message_handler(commands=['stats'])
def stats_command(message):
    """Показывает статистику"""
    user_id = message.from_user.id
    stats = database.get_player_stats(user_id)
    
    if not stats:
        bot.send_message(message.chat.id, "❌ У тебя еще нет персонажа! Используй /start для создания.")
        return
    
    stats_text = (
        f"📊 <b>Статистика игрока</b>\n\n"
        f"<b>Имя:</b> {stats['character_name']}\n"
        f"<b>Раса:</b> {stats['race']}\n"
        f"<b>Уровень:</b> {stats['level']}\n"
        f"<b>Ранг:</b> {stats['rank']}\n"
        f"<b>Опыт:</b> {stats['experience']}\n\n"
        f"<b>Боевая статистика:</b>\n"
        f"⚔️ Победы: {stats['battle_wins']}\n"
        f"💀 Поражения: {stats['battle_losses']}\n"
        f"👑 Убито боссов: {stats['boss_kills']}\n"
        f"🎯 Убито мини-боссов: {stats['mini_boss_kills']}\n\n"
        f"<b>Ресурсы:</b>\n"
        f"💰 Золото: {stats['gold']}\n"
        f"🎯 Очки характеристик: {stats['stat_points']}\n"
    )
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu"))
    
    bot.send_message(
        message.chat.id,
        stats_text,
        reply_markup=keyboard
    )

@bot.message_handler(commands=['top'])
def top_command(message):
    """Показывает топ игроков"""
    top_players = database.get_top_players(10)
    
    if not top_players:
        bot.send_message(message.chat.id, "🏆 Топ игроков пока пуст!")
        return
    
    top_text = "🏆 <b>ТОП 10 ИГРОКОВ</b>\n\n"
    
    for i, player in enumerate(top_players, 1):
        top_text += f"{i}. <b>{player['character_name']}</b>\n"
        top_text += f"   ⭐ Уровень: {player['level']} | 🏆 Ранг: {player['rank']}\n"
        top_text += f"   ⚔️ Победы: {player['battle_wins']} | 👑 Боссы: {player['boss_kills']}\n"
        top_text += "─" * 30 + "\n"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu"))
    
    bot.send_message(
        message.chat.id,
        top_text,
        reply_markup=keyboard
    )

@bot.message_handler(commands=['help'])
def help_command(message):
    """Показывает справку"""
    help_text = (
        "🎮 <b>RPG Бот - Справка</b>\n\n"
        "<b>Основные команды:</b>\n"
        "/start - Начать игру или главное меню\n"
        "/profile - Показать профиль персонажа\n"
        "/inventory - Открыть инвентарь\n"
        "/shop - Посетить магазин\n"
        "/battle - Начать битву\n"
        "/stats - Показать статистику\n"
        "/top - Топ игроков\n"
        "/help - Эта справка\n\n"
        "<b>Как играть:</b>\n"
        "1. Создай персонажа (/start)\n"
        "2. Сражайся с монстрами (/battle)\n"
        "3. Получай опыт и золото\n"
        "4. Улучшай характеристики в профиле\n"
        "5. Покупай зелья в магазине\n"
        "6. Становись сильнее!\n\n"
        "<b>Подсказки:</b>\n"
        "• Здоровье и мана восстанавливаются со временем\n"
        "• Распределяй очки характеристик мудро\n"
        "• Используй зелья в трудных битвах\n"
        "• Чем выше уровень, тем сильнее враги"
    )
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu"))
    
    bot.send_message(
        message.chat.id,
        help_text,
        reply_markup=keyboard
    )

# ==================== ОБРАБОТЧИКИ CALLBACK ====================

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """Обработка всех callback запросов"""
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    try:
        if call.data.startswith('create_'):
            # Создание персонажа
            race = call.data.replace('create_', '')
            username = call.from_user.username or call.from_user.first_name
            
            msg = bot.send_message(chat_id, f"📝 Вы выбрали расу: {database.get_all_races()[race]['name']}\n\nТеперь введите имя вашего персонажа:")
            bot.register_next_step_handler(msg, process_character_name, race, username)
        
        elif call.data == "main_menu":
            bot.delete_message(chat_id, message_id)
            start_command(call.message)
        
        elif call.data == "profile":
            bot.delete_message(chat_id, message_id)
            profile_command(call.message)
        
        elif call.data == "inventory":
            bot.delete_message(chat_id, message_id)
            inventory_command(call.message)
        
        elif call.data == "shop_menu" or call.data == "shop":
            bot.delete_message(chat_id, message_id)
            shop_command(call.message)
        
        elif call.data == "battle_menu" or call.data == "battle":
            bot.delete_message(chat_id, message_id)
            battle_command(call.message)
        
        elif call.data == "stats":
            bot.delete_message(chat_id, message_id)
            stats_command(call.message)
        
        elif call.data == "top_players":
            bot.delete_message(chat_id, message_id)
            top_command(call.message)
        
        elif call.data.startswith('stat_'):
            # Распределение характеристик
            stat_type = call.data.replace('stat_', '')
            success, message = database.add_stat_point(user_id, stat_type)
            
            bot.answer_callback_query(call.id, message)
            if success:
                bot.delete_message(chat_id, message_id)
                profile_command(call.message)
        
        elif call.data.startswith('buy_'):
            # Покупка предмета
            item_key = call.data.replace('buy_', '')
            
            if item_key in SHOP_ITEMS:
                item_info = SHOP_ITEMS[item_key]
                
                character = database.get_character(user_id)
                if not character:
                    bot.answer_callback_query(call.id, "❌ У тебя нет персонажа!")
                    return
                
                success, message = database.buy_item(
                    user_id, 
                    item_key, 
                    item_info['type'], 
                    item_info['name'], 
                    item_info['price'],
                    item_info.get('effect')
                )
                
                bot.answer_callback_query(call.id, message)
                
                if success:
                    bot.delete_message(chat_id, message_id)
                    shop_command(call.message)
        
        elif call.data.startswith('use_'):
            # Использование предмета
            item_key = call.data.replace('use_', '')
            
            inventory = database.get_inventory(user_id)
            item_to_use = None
            
            for item in inventory:
                if item['item_key'] == item_key:
                    item_to_use = item
                    break
            
            if not item_to_use:
                bot.answer_callback_query(call.id, "❌ Предмет не найден!")
                return
            
            success, message = database.use_item(
                user_id,
                item_key,
                item_to_use['item_type'],
                item_to_use['item_name'],
                item_to_use['effect_amount']
            )
            
            bot.answer_callback_query(call.id, message)
            
            if success:
                bot.delete_message(chat_id, message_id)
                inventory_command(call.message)
        
        elif call.data.startswith('attack_'):
            # Атака врага
            enemy_key = call.data.replace('attack_', '')
            perform_attack(call, enemy_key)
        
        elif call.data == "run_away":
            bot.answer_callback_query(call.id, "🏃‍♂️ Ты успешно сбежал с поля боя!")
            bot.delete_message(chat_id, message_id)
            start_command(call.message)
        
        elif call.data == "use_in_battle":
            bot.answer_callback_query(call.id, "🎒 Используй предмет из инвентаря командой /inventory")
        
        else:
            bot.answer_callback_query(call.id, "⚠️ Неизвестная команда")
    
    except Exception as e:
        print(f"❌ Ошибка в обработчике callback: {e}")
        bot.answer_callback_query(call.id, "❌ Произошла ошибка. Попробуй еще раз.")

def process_character_name(message, race, username):
    """Обработка ввода имени персонажа"""
    character_name = message.text.strip()
    user_id = message.from_user.id
    
    if len(character_name) < 2:
        msg = bot.send_message(message.chat.id, "❌ Имя должно содержать минимум 2 символа. Попробуй еще раз:")
        bot.register_next_step_handler(msg, process_character_name, race, username)
        return
    
    if len(character_name) > 20:
        msg = bot.send_message(message.chat.id, "❌ Имя слишком длинное (макс. 20 символов). Попробуй еще раз:")
        bot.register_next_step_handler(msg, process_character_name, race, username)
        return
    
    # Создаем персонажа
    success, result_message = database.create_character(user_id, username, character_name, race)
    
    if success:
        bot.send_message(
            message.chat.id,
            f"✅ {result_message}\n\n"
            f"🎉 Твой персонаж <b>{character_name}</b> ({database.get_all_races()[race]['name']}) успешно создан!\n\n"
            f"Используй /profile чтобы посмотреть характеристики,\n"
            f"/battle чтобы сражаться с монстрами,\n"
            f"/shop чтобы посетить магазин."
        )
        start_command(message)
    else:
        bot.send_message(message.chat.id, f"❌ {result_message}")

def perform_attack(call, enemy_key):
    """Выполняет атаку на врага"""
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    character = database.get_character(user_id)
    enemy = create_enemy(enemy_key, character['level'])
    
    if not character or not enemy:
        bot.answer_callback_query(call.id, "❌ Ошибка в битве!")
        return
    
    # Игрок атакует врага
    player_damage = random.randint(
        character['strength'] // 2,
        character['strength']
    )
    
    actual_damage = max(1, player_damage)
    enemy['health'] -= actual_damage
    
    battle_text = f"⚔️ Ты атаковал {enemy['name']} и нанес {actual_damage} урона!\n"
    
    # Проверяем, побежден ли враг
    if enemy['health'] <= 0:
        # Победа!
        experience_gained = enemy['exp']
        gold_gained = enemy['gold']
        
        # Добавляем опыт и золото
        database.add_experience(user_id, experience_gained)
        database.add_gold(user_id, gold_gained)
        database.increment_battle_stats(user_id, won=True)
        
        battle_text += f"\n🎉 <b>ПОБЕДА!</b>\n"
        battle_text += f"✨ Получено опыта: {experience_gained}\n"
        battle_text += f"💰 Получено золота: {gold_gained}\n\n"
        
        # Проверяем повышение уровня
        success, level_up, new_level, stat_points = database.add_experience(user_id, experience_gained)
        if level_up:
            battle_text += f"🎊 <b>ПОВЫШЕНИЕ УРОВНЯ!</b>\n"
            battle_text += f"📈 Новый уровень: {new_level}\n"
            battle_text += f"🎯 Получено очков характеристик: {stat_points}\n\n"
        
        battle_text += f"Что хочешь сделать дальше?"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("⚔️ Сражаться снова", callback_data="battle"),
            InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
        )
        
        try:
            bot.edit_message_caption(
                chat_id=chat_id,
                message_id=message_id,
                caption=battle_text,
                reply_markup=keyboard
            )
        except:
            bot.edit_message_text(
                battle_text,
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=keyboard
            )
        
    else:
        # Враг атакует в ответ
        enemy_damage = random.randint(
            enemy['min_damage'],
            enemy['max_damage']
        )
        
        character['health'] -= enemy_damage
        
        battle_text += f"💥 {enemy['name']} контратаковал и нанес {enemy_damage} урона!\n"
        battle_text += f"\n❤️ Твое здоровье: {max(0, character['health'])}/{character['max_health']}\n"
        battle_text += f"❤️ Здоровье врага: {enemy['health']}/{enemy['max_health']}\n\n"
        
        # Обновляем здоровье персонажа в БД
        database.update_character_stats(user_id, health=max(0, character['health']))
        
        # Проверяем, жив ли игрок
        if character['health'] <= 0:
            # Поражение
            battle_text += f"💀 <b>ПОРАЖЕНИЕ!</b>\n"
            battle_text += f"Ты был повержен {enemy['name']}.\n\n"
            battle_text += f"Подожди регенерации или используй зелье здоровья."
            
            database.increment_battle_stats(user_id, won=False)
            
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"))
        else:
            # Бой продолжается
            battle_text += f"Выбери следующее действие:"
            
            keyboard = InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                InlineKeyboardButton("⚔️ Атаковать", callback_data=f"attack_{enemy_key}"),
                InlineKeyboardButton("🛡️ Защищаться", callback_data=f"defend_{enemy_key}")
            )
            keyboard.add(
                InlineKeyboardButton("🏃‍♂️ Убежать", callback_data="run_away"),
                InlineKeyboardButton("🎒 Исп. предмет", callback_data="use_in_battle")
            )
        
        try:
            bot.edit_message_caption(
                chat_id=chat_id,
                message_id=message_id,
                caption=battle_text,
                reply_markup=keyboard
            )
        except:
            bot.edit_message_text(
                battle_text,
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=keyboard
            )

# ==================== ЗАПУСК БОТА ====================

if __name__ == "__main__":
    print("🤖 Запуск бота...")
    print(f"📊 Токен: {'Установлен' if TOKEN and TOKEN != 'placeholder_token' else 'НЕ УСТАНОВЛЕН!'}")
    
    # Устанавливаем повторные попытки подключения
    max_retries = 5
    retry_delay = 10
    
    for attempt in range(max_retries):
        try:
            print(f"🔄 Попытка запуска {attempt + 1}/{max_retries}...")
            
            # Удаляем вебхук если он был установлен
            try:
                bot.remove_webhook()
                time.sleep(1)
            except Exception as e:
                print(f"ℹ️ Не удалось удалить вебхук (может не быть установлен): {e}")
            
            # Запускаем polling
            print("✅ Запускаю polling...")
            bot.polling(none_stop=True, interval=1, timeout=30)
            
        except Exception as e:
            print(f"❌ Ошибка при запуске бота (попытка {attempt + 1}): {e}")
            
            if attempt < max_retries - 1:
                print(f"⏳ Повторная попытка через {retry_delay} секунд...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Экспоненциальная задержка
            else:
                print("❌ Все попытки запуска провалились. Бот остановлен.")
                break
