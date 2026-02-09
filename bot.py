import os
import telebot
import database  # Импортируем функции из database.py
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import random
import time

# Инициализация бота
TOKEN = os.getenv('TELEGRAM_TOKEN')
if not TOKEN:
    print("⚠️ Предупреждение: TELEGRAM_TOKEN не найден в переменных окружения")
    TOKEN = "YOUR_BOT_TOKEN_HERE"  # Замените на реальный токен

bot = telebot.TeleBot(TOKEN)

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
    'demon': 'https://img.freepik.com/free-photo/demon_23-2150762325.jpg',
    'lich': 'https://img.freepik.com/free-photo/lich_23-2150911246.jpg',
    'dragon': 'https://abrakadabra.fun/uploads/posts/2022-03/1646721873_1-abrakadabra-fun-p-pauk-fantezi-art-1.jpg',
    'dragon_young': 'https://img.freepik.com/free-photo/ancient-dragon_23-2150762338.jpg',
    'dragon_ancient': 'https://img.freepik.com/free-photo/ancient-dragon_23-2150762338.jpg',
    'titan': 'https://img.freepik.com/free-photo/titan_23-2150911270.jpg',
    'fallen_god': 'https://img.freepik.com/free-photo/fallen-god_23-2150911258.jpg',
    'village': 'https://img.freepik.com/premium-photo/tavern-like-game_808092-1770.jpg',
    'forest': 'https://img.freepik.com/premium-photo/ancient-forest-ai-generated_1127-13930.jpg',
    'castle': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTrAoGzKjgZxurLbxZ_Dyhtkm1gBqMUMtA87w&s',
    'dungeon': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSTZd9YHDcPOGmD8ezmHB0xD-HfA9O7OpgVyA&s',
    'training_camp': 'https://img1.liveinternet.ru/images/attach/b/2/1/726/1726838_full0011.jpg',
    'hell_gate': 'https://abrakadabra.fun/uploads/posts/2022-01/1642490542_3-abrakadabra-fun-p-temnii-mag-art-5.jpg',
    'throne_god': 'https://abrakadabra.fun/uploads/posts/2022-03/1646721873_1-abrakadabra-fun-p-pauk-fantezi-art-1.jpg',
    'shop': 'https://img.freepik.com/premium-photo/tavern-like-game_808092-1770.jpg',
    'levelup': 'https://i.pinimg.com/736x/7f/9a/97/7f9a97fdbbd70577225c213ad8a6e75c.jpg',
    'inventory': 'https://i.imgur.com/6QyTK2F.jpeg'
}

# Товары в магазине - УСЛОЖНЕННЫЕ ЦЕНЫ И ЭФФЕКТЫ
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
    },
    'rank_d_weapon': {
        'name': '⚔️ Меч D-ранга',
        'description': '+3 к силе (требуется D-ранг)',
        'price': 300,
        'type': 'weapon',
        'effect': 3,
        'available': True,
        'required_rank': 'D'
    },
    'rank_c_armor': {
        'name': '🛡️ Броня C-ранга',
        'description': '+5 к живучести (требуется C-ранг)',
        'price': 400,
        'type': 'armor',
        'effect': 5,
        'available': True,
        'required_rank': 'C'
    },
    'rank_b_artifact': {
        'name': '💎 Артефакт B-ранга',
        'description': '+8 к интеллекту (требуется B-ранг)',
        'price': 600,
        'type': 'artifact',
        'effect': 8,
        'available': True,
        'required_rank': 'B'
    },
    'ring_of_agility': {
        'name': '💍 Кольцо ловкости',
        'description': '+5 к ловкости',
        'price': 450,
        'type': 'artifact',
        'effect': 5,
        'available': True,
        'required_rank': 'C'
    }
}

# Определение локаций по рангам
LOCATIONS = {
    'E': {
        'name': '🎪 Тренировочный лагерь',
        'description': 'Начинай свой путь здесь. Враги слабые, но хороши для тренировки.',
        'enemies': ['wolf', 'goblin', 'slime', 'goblin_elite', 'training_master'],
        'mini_boss': 'goblin_elite',
        'boss': 'training_master',
        'image': IMAGE_URLS['training_camp'],
        'min_level': 1,
        'max_level': 15,
        'difficulty': 'easy'
    },
    'D': {
        'name': '🌲 Лес призраков',
        'description': 'Лес наполнен низкоуровневыми монстрами. Подходит для охотников D-ранга.',
        'enemies': ['forest_spider', 'ghost', 'wild_boar', 'forest_troll', 'forest_guardian'],
        'mini_boss': 'forest_troll',
        'boss': 'forest_guardian',
        'image': IMAGE_URLS['forest'],
        'min_level': 10,
        'max_level': 25,
        'difficulty': 'medium'
    },
    'C': {
        'name': '🪦 Заброшенные катакомбы',
        'description': 'Катакомбы наполнены опасными существами. Требует навыков C-ранга.',
        'enemies': ['skeleton_warrior', 'ghoul', 'dark_priest', 'crypt_keeper', 'catacomb_lord'],
        'mini_boss': 'crypt_keeper',
        'boss': 'catacomb_lord',
        'image': IMAGE_URLS['dungeon'],
        'min_level': 20,
        'max_level': 35,
        'difficulty': 'hard'
    },
    'B': {
        'name': '🏰 Руины древнего замка',
        'description': 'Замок охраняют могущественные существа. Только для охотников B-ранга.',
        'enemies': ['knight', 'vampire', 'warlock', 'death_knight', 'castle_overlord'],
        'mini_boss': 'death_knight',
        'boss': 'castle_overlord',
        'image': IMAGE_URLS['castle'],
        'min_level': 30,
        'max_level': 45,
        'difficulty': 'very_hard'
    },
    'A': {
        'name': '🌋 Врата в преисподнюю',
        'description': 'Портал в мир демонов. Только сильнейшие A-ранга могут здесь выжить.',
        'enemies': ['demon', 'hellhound', 'infernal_mage', 'pit_fiend', 'demon_general'],
        'mini_boss': 'pit_fiend',
        'boss': 'demon_general',
        'image': IMAGE_URLS['hell_gate'],
        'min_level': 40,
        'max_level': 55,
        'difficulty': 'extreme'
    },
    'S': {
        'name': '⚡ Трон божества',
        'description': 'Последнее испытание. Только S-ранг может бросить вызов богу.',
        'enemies': ['dragon_ancient', 'titan', 'fallen_angel', 'archangel', 'final_god'],
        'mini_boss': 'archangel',
        'boss': 'final_god',
        'image': IMAGE_URLS['throne_god'],
        'min_level': 50,
        'max_level': 70,
        'difficulty': 'legendary'
    }
}

# Базовые параметры врагов (без учета уровня игрока)
BASE_ENEMIES = {
    # E-ранг враги
    'wolf': {
        'name': '🐺 Бешеный Волк',
        'base_health': 35,
        'base_min_physical_damage': 5,
        'base_max_physical_damage': 8,
        'base_min_magic_damage': 0,
        'base_max_magic_damage': 0,
        'base_exp': 12,
        'base_gold': 8,
        'rank': 'E',
        'description': 'Его глаза горят голодом, а клыки обнажены.',
        'image': IMAGE_URLS['wolf'],
        'difficulty': 'easy',
        'abilities': ['basic_attack'],
        'damage_type': 'physical',
        'dodge_chance': 0.08,
        'physical_resistance': 0.15,
        'magic_resistance': 0.0,
        'special_chance': 0.15,
        'attack_range': 'melee'
    },
    'goblin': {
        'name': '👹 Гоблин-разведчик',
        'base_health': 40,
        'base_min_physical_damage': 6,
        'base_max_physical_damage': 10,
        'base_min_magic_damage': 0,
        'base_max_magic_damage': 0,
        'base_exp': 16,
        'base_gold': 12,
        'rank': 'E',
        'description': 'Мелкий и трусливый, но опасный в стае.',
        'image': IMAGE_URLS['goblin'],
        'difficulty': 'easy',
        'abilities': ['basic_attack', 'dirty_trick'],
        'damage_type': 'physical',
        'dodge_chance': 0.12,
        'physical_resistance': 0.05,
        'magic_resistance': 0.0,
        'special_chance': 0.20,
        'attack_range': 'melee'
    },
    'slime': {
        'name': '🟢 Ядовитая Слизь',
        'base_health': 45,
        'base_min_physical_damage': 3,
        'base_max_physical_damage': 8,
        'base_min_magic_damage': 2,
        'base_max_magic_damage': 5,
        'base_exp': 10,
        'base_gold': 7,
        'rank': 'E',
        'description': 'Желейная масса, медленная, но ядовитая.',
        'image': IMAGE_URLS['slime'],
        'difficulty': 'easy',
        'abilities': ['basic_attack', 'poison_spit'],
        'damage_type': 'mixed',
        'dodge_chance': 0.03,
        'physical_resistance': 0.35,
        'magic_resistance': 0.15,
        'special_chance': 0.25,
        'poison_chance': 0.35,
        'attack_range': 'ranged'
    },
    'goblin_elite': {
        'name': '👹 Элитный гоблин',
        'base_health': 75,
        'base_min_physical_damage': 10,
        'base_max_physical_damage': 18,
        'base_min_magic_damage': 0,
        'base_max_magic_damage': 0,
        'base_exp': 28,
        'base_gold': 20,
        'rank': 'E',
        'description': 'Опытный воин гоблинов, вооруженный стальным оружием.',
        'image': IMAGE_URLS['hot_goblin'],
        'difficulty': 'mini_boss',
        'abilities': ['basic_attack', 'power_strike', 'goblin_shout'],
        'damage_type': 'physical',
        'dodge_chance': 0.15,
        'physical_resistance': 0.20,
        'magic_resistance': 0.08,
        'special_chance': 0.30,
        'mini_boss_bonus': 1.8,
        'attack_range': 'melee'
    },
    'training_master': {
        'name': '⚔️ Мастер-тренер',
        'base_health': 100,
        'base_min_physical_damage': 10,
        'base_max_physical_damage': 20,
        'base_min_magic_damage': 0,
        'base_max_magic_damage': 0,
        'base_exp': 40,
        'base_gold': 32,
        'rank': 'E',
        'description': 'Опытный воин, обучающий новичков. Не стоит недооценивать его!',
        'image': IMAGE_URLS['knight'],
        'difficulty': 'boss',
        'abilities': ['basic_attack', 'training_strike', 'defensive_stance', 'encouraging_shout'],
        'damage_type': 'physical',
        'dodge_chance': 0.20,
        'physical_resistance': 0.25,
        'magic_resistance': 0.15,
        'special_chance': 0.35,
        'boss_bonus': 2.5,
        'attack_range': 'melee'
    },
}

# Функция для создания врага с учетом уровня игрока - УСИЛЕННЫЙ ВАРИАНТ
def create_enemy(enemy_key, player_level):
    """Создает врага с параметрами, зависящими от уровня игрока - УСИЛЕННЫЙ ВАРИАНТ"""
    if enemy_key not in BASE_ENEMIES:
        return None
    
    base_enemy = BASE_ENEMIES[enemy_key].copy()
    
    # УСИЛЕННЫЙ МНОЖИТЕЛЬ УРОВНЯ
    # Враги становятся на 15% сильнее за каждый уровень игрока сверх 1
    level_multiplier = 1.0 + (player_level - 1) * 0.15
    
    # УСИЛЕННЫЕ БОНУСЫ ДЛЯ МИНИ-БОССОВ И БОССОВ
    if base_enemy.get('difficulty') == 'mini_boss':
        bonus = base_enemy.get('mini_boss_bonus', 1.8)  # Усилен
    elif base_enemy.get('difficulty') == 'boss':
        bonus = base_enemy.get('boss_bonus', 2.5)  # Усилен
    else:
        bonus = 1.0
    
    # Итоговый множитель
    final_multiplier = level_multiplier * bonus
    
    # Усиление характеристик
    enemy = {
        'key': enemy_key,
        'name': base_enemy['name'],
        'health': int(base_enemy['base_health'] * final_multiplier),
        'max_health': int(base_enemy['base_health'] * final_multiplier),
        'min_physical_damage': int(base_enemy['base_min_physical_damage'] * level_multiplier),
        'max_physical_damage': int(base_enemy['base_max_physical_damage'] * level_multiplier),
        'min_magic_damage': int(base_enemy['base_min_magic_damage'] * level_multiplier),
        'max_magic_damage': int(base_enemy['base_max_magic_damage'] * level_multiplier),
        'exp': int(base_enemy['base_exp'] * final_multiplier * 0.8),  # Немного меньше опыта
        'gold': int(base_enemy['base_gold'] * final_multiplier * 0.8), # Немного меньше золота
        'rank': base_enemy['rank'],
        'description': base_enemy['description'],
        'image': base_enemy['image'],
        'difficulty': base_enemy['difficulty'],
        'abilities': base_enemy['abilities'],
        'damage_type': base_enemy['damage_type'],
        'dodge_chance': min(base_enemy['dodge_chance'] * 1.2, 0.4),  # Увеличен шанс уклонения
        'physical_resistance': min(base_enemy['physical_resistance'] * 1.3, 0.6),  # Усилены сопротивления
        'magic_resistance': min(base_enemy['magic_resistance'] * 1.3, 0.6),
        'special_chance': min(base_enemy['special_chance'] * 1.2, 0.5),  # Чаще используют спецспособности
        'attack_range': base_enemy['attack_range'],
        'player_level': player_level,
        'level_multiplier': round(level_multiplier, 2)
    }
    
    # Добавляем специфические параметры
    for key in ['poison_chance', 'web_chance', 'charge_chance', 'heal_chance', 
                'summon_chance', 'defense_bonus', 'heal_from_damage', 'fire_chance',
                'burn_chance', 'aoe_chance', 'stun_chance', 'army_bonus', 'spell_chance',
                'block_chance', 'drain_chance', 'breath_chance']:
        if key in base_enemy:
            enemy[key] = min(base_enemy[key] * 1.2, 0.9)  # Усиливаем все шансы
    
    # Для боссов и мини-боссов добавляем особые отметки
    if enemy['difficulty'] == 'boss':
        enemy['is_boss'] = True
    elif enemy['difficulty'] == 'mini_boss':
        enemy['is_mini_boss'] = True
    
    return enemy

# Инициализация базы данных при старте
print("🔄 Инициализация базы данных...")
database.init_db()
print("✅ База данных инициализирована")

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
        
        if character.get('image'):
            bot.send_photo(
                message.chat.id,
                photo=character.get('image'),
                caption=welcome_text,
                reply_markup=keyboard
            )
        else:
            bot.send_message(
                message.chat.id,
                welcome_text,
                reply_markup=keyboard
            )
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
        f"👤 *Профиль персонажа*\n\n"
        f"*Имя:* {character['character_name']}\n"
        f"*Раса:* {race_info.get('name', 'Неизвестно')}\n"
        f"*Уровень:* {character['level']}\n"
        f"*Ранг:* {character['rank']}\n"
        f"*Опыт:* {character['experience']}\n\n"
        f"*Характеристики:*\n"
        f"💪 Сила: {character['strength']}\n"
        f"🏃‍♂️ Ловкость: {character['agility']}\n"
        f"🧠 Интеллект: {character['intelligence']}\n\n"
        f"*Состояние:*\n"
        f"❤️ Здоровье: {character['health']}/{character['max_health']}\n"
        f"🔮 Мана: {character['mana']}/{character['max_mana']}\n"
        f"💰 Золото: {character['gold']}\n\n"
        f"*Очки характеристик:* {character['stat_points']}\n"
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
        keyboard = None
    
    bot.send_message(
        message.chat.id,
        profile_text,
        parse_mode='Markdown',
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
    
    shop_text = "🏪 *Магазин приключений*\n\n"
    shop_text += f"💰 Твой баланс: {character['gold']} золота\n\n"
    shop_text += "*Доступные товары:*\n\n"
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    for i, (item_key, item_info) in enumerate(SHOP_ITEMS.items()):
        # Проверяем доступность по рангу
        required_rank = item_info.get('required_rank')
        if required_rank:
            rank_order = {'E': 0, 'D': 1, 'C': 2, 'B': 3, 'A': 4, 'S': 5}
            if rank_order.get(character['rank'], 0) < rank_order.get(required_rank, 0):
                continue
        
        shop_text += f"{item_info['name']}\n"
        shop_text += f"📝 {item_info['description']}\n"
        shop_text += f"💰 Цена: {item_info['price']} золота\n"
        shop_text += "─" * 20 + "\n"
        
        callback_data = f"buy_{item_key}"
        keyboard.add(InlineKeyboardButton(
            f"{item_info['name']} - {item_info['price']}💰", 
            callback_data=callback_data
        ))
    
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="main_menu"))
    
    bot.send_message(
        message.chat.id,
        shop_text,
        parse_mode='Markdown',
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
        inventory_text = "🎒 *Твой инвентарь пуст*\n\n"
        inventory_text += "Посети 🏪 Магазин, чтобы купить предметы!"
    else:
        inventory_text = "🎒 *Твой инвентарь*\n\n"
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        for item in inventory:
            inventory_text += f"{item['item_name']} ×{item['quantity']}\n"
            if item['effect_amount'] > 0:
                inventory_text += f"📊 Эффект: +{item['effect_amount']}\n"
            inventory_text += "─" * 20 + "\n"
            
            if 'potion' in item['item_key']:
                keyboard.add(InlineKeyboardButton(
                    f"Использовать {item['item_name']}", 
                    callback_data=f"use_{item['item_key']}"
                ))
    
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="main_menu"))
    
    bot.send_message(
        message.chat.id,
        inventory_text,
        parse_mode='Markdown',
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
        f"⚔️ *БОЕВАЯ СИТУАЦИЯ!*\n\n"
        f"Ты встретил {enemy['name']}!\n"
        f"{enemy['description']}\n\n"
        f"*Характеристики врага:*\n"
        f"❤️ Здоровье: {enemy['health']}\n"
        f"⚔️ Урон: {enemy['min_physical_damage']}-{enemy['max_physical_damage']}\n\n"
        f"*Твое состояние:*\n"
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
    
    bot.send_photo(
        message.chat.id,
        photo=enemy['image'],
        caption=battle_text,
        parse_mode='Markdown',
        reply_markup=keyboard
    )

# ==================== ОБРАБОТЧИКИ CALLBACK ====================

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """Обработка всех callback запросов"""
    user_id = call.from_user.id
    
    if call.data.startswith('create_'):
        # Создание персонажа
        race = call.data.replace('create_', '')
        username = call.from_user.username or call.from_user.first_name
        
        # Запрашиваем имя персонажа
        msg = bot.send_message(call.message.chat.id, f"📝 Вы выбрали расу: {database.get_all_races()[race]['name']}\n\nТеперь введите имя вашего персонажа:")
        bot.register_next_step_handler(msg, process_character_name, race, username)
    
    elif call.data == "main_menu":
        show_main_menu(call.message)
    
    elif call.data == "profile":
        profile_command(call.message)
    
    elif call.data == "inventory":
        inventory_command(call.message)
    
    elif call.data == "shop_menu":
        shop_command(call.message)
    
    elif call.data == "stats":
        show_stats(call.message)
    
    elif call.data == "top_players":
        show_top_players(call.message)
    
    elif call.data.startswith('stat_'):
        # Распределение характеристик
        stat_type = call.data.replace('stat_', '')
        success, message = database.add_stat_point(user_id, stat_type)
        
        if success:
            bot.answer_callback_query(call.id, message)
            profile_command(call.message)
        else:
            bot.answer_callback_query(call.id, message)
    
    elif call.data.startswith('buy_'):
        # Покупка предмета
        item_key = call.data.replace('buy_', '')
        
        if item_key in SHOP_ITEMS:
            item_info = SHOP_ITEMS[item_key]
            
            # Проверяем, есть ли персонаж
            character = database.get_character(user_id)
            if not character:
                bot.answer_callback_query(call.id, "❌ У тебя нет персонажа!")
                return
            
            # Проверяем ранг
            required_rank = item_info.get('required_rank')
            if required_rank:
                rank_order = {'E': 0, 'D': 1, 'C': 2, 'B': 3, 'A': 4, 'S': 5}
                if rank_order.get(character['rank'], 0) < rank_order.get(required_rank, 0):
                    bot.answer_callback_query(call.id, f"❌ Нужен ранг {required_rank} или выше!")
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
                shop_command(call.message)
    
    elif call.data.startswith('use_'):
        # Использование предмета
        item_key = call.data.replace('use_', '')
        
        # Ищем предмет в инвентаре
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
            inventory_command(call.message)
    
    elif call.data.startswith('attack_'):
        # Атака врага
        enemy_key = call.data.replace('attack_', '')
        perform_attack(call.message, user_id, enemy_key)
    
    elif call.data == "run_away":
        bot.answer_callback_query(call.id, "🏃‍♂️ Ты успешно сбежал с поля боя!")
        show_main_menu(call.message)

def process_character_name(message, race, username):
    """Обработка ввода имени персонажа"""
    character_name = message.text.strip()
    
    if len(character_name) < 2:
        msg = bot.send_message(message.chat.id, "❌ Имя должно содержать минимум 2 символа. Попробуй еще раз:")
        bot.register_next_step_handler(msg, process_character_name, race, username)
        return
    
    if len(character_name) > 20:
        msg = bot.send_message(message.chat.id, "❌ Имя слишком длинное (макс. 20 символов). Попробуй еще раз:")
        bot.register_next_step_handler(msg, process_character_name, race, username)
        return
    
    # Создаем персонажа
    success, result_message = database.create_character(message.from_user.id, username, character_name, race)
    
    if success:
        bot.send_message(
            message.chat.id,
            f"✅ {result_message}\n\n"
            f"🎉 Твой персонаж {character_name} ({database.get_all_races()[race]['name']}) успешно создан!\n\n"
            f"Используй /profile чтобы посмотреть характеристики,\n"
            f"/battle чтобы сражаться с монстрами,\n"
            f"/shop чтобы посетить магазин."
        )
        show_main_menu(message)
    else:
        bot.send_message(message.chat.id, f"❌ {result_message}")

def show_main_menu(message):
    """Показывает главное меню"""
    user_id = message.from_user.id
    character = database.get_character(user_id)
    
    if not character:
        return
    
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
    
    bot.send_message(
        message.chat.id,
        "🎮 *Главное меню*\n\nВыбери действие:",
        parse_mode='Markdown',
        reply_markup=keyboard
    )

def show_stats(message):
    """Показывает статистику игрока"""
    user_id = message.from_user.id
    stats = database.get_player_stats(user_id)
    
    if not stats:
        bot.send_message(message.chat.id, "❌ Статистика не найдена!")
        return
    
    stats_text = (
        f"📊 *Статистика игрока*\n\n"
        f"👤 Имя: {stats['character_name']}\n"
        f"🏆 Ранг: {stats['rank']}\n"
        f"⭐ Уровень: {stats['level']}\n"
        f"📈 Опыт: {stats['experience']}\n\n"
        f"⚔️ Победы: {stats['battle_wins']}\n"
        f"💀 Поражения: {stats['battle_losses']}\n"
        f"👑 Убито боссов: {stats['boss_kills']}\n"
        f"🎯 Убито мини-боссов: {stats['mini_boss_kills']}\n\n"
        f"💰 Золото: {stats['gold']}\n"
        f"📅 Дата создания: {stats['created_at'].strftime('%d.%m.%Y') if stats.get('created_at') else 'Неизвестно'}\n"
    )
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="main_menu"))
    
    bot.send_message(
        message.chat.id,
        stats_text,
        parse_mode='Markdown',
        reply_markup=keyboard
    )

def show_top_players(message):
    """Показывает топ игроков"""
    top_players = database.get_top_players(10)
    
    if not top_players:
        bot.send_message(message.chat.id, "🏆 Топ игроков пока пуст!")
        return
    
    top_text = "🏆 *ТОП 10 ИГРОКОВ*\n\n"
    
    for i, player in enumerate(top_players, 1):
        top_text += f"{i}. *{player['character_name']}*\n"
        top_text += f"   ⭐ Уровень: {player['level']} | 🏆 Ранг: {player['rank']}\n"
        top_text += f"   ⚔️ Победы: {player['battle_wins']} | 👑 Боссы: {player['boss_kills']}\n"
        top_text += "─" * 30 + "\n"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="main_menu"))
    
    bot.send_message(
        message.chat.id,
        top_text,
        parse_mode='Markdown',
        reply_markup=keyboard
    )

def perform_attack(message, user_id, enemy_key):
    """Выполняет атаку на врага"""
    character = database.get_character(user_id)
    enemy = create_enemy(enemy_key, character['level'])
    
    if not character or not enemy:
        bot.send_message(message.chat.id, "❌ Ошибка в битве!")
        return
    
    # Игрок атакует врага
    player_damage = random.randint(
        character['strength'] // 2,
        character['strength']
    )
    
    # Учитываем сопротивление врага
    if enemy['damage_type'] == 'physical':
        damage_multiplier = 1.0 - enemy['physical_resistance']
    else:
        damage_multiplier = 1.0 - enemy['magic_resistance']
    
    actual_damage = max(1, int(player_damage * damage_multiplier))
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
        
        battle_text += f"\n🎉 *ПОБЕДА!*\n"
        battle_text += f"✨ Получено опыта: {experience_gained}\n"
        battle_text += f"💰 Получено золота: {gold_gained}\n\n"
        
        # Проверяем повышение уровня
        success, level_up, new_level, stat_points = database.add_experience(user_id, experience_gained)
        if level_up:
            battle_text += f"🎊 *ПОВЫШЕНИЕ УРОВНЯ!*\n"
            battle_text += f"📈 Новый уровень: {new_level}\n"
            battle_text += f"🎯 Получено очков характеристик: {stat_points}\n\n"
        
        battle_text += f"Что хочешь сделать дальше?"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("⚔️ Сражаться снова", callback_data="battle_menu"),
            InlineKeyboardButton("🏠 В главное меню", callback_data="main_menu")
        )
        
    else:
        # Враг атакует в ответ
        enemy_damage = random.randint(
            enemy['min_physical_damage'],
            enemy['max_physical_damage']
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
            battle_text += f"💀 *ПОРАЖЕНИЕ!*\n"
            battle_text += f"Ты был повержен {enemy['name']}.\n\n"
            battle_text += f"Подожди регенерации или используй зелье здоровья."
            
            database.increment_battle_stats(user_id, won=False)
            
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("🏠 В главное меню", callback_data="main_menu"))
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
    
    bot.send_message(
        message.chat.id,
        battle_text,
        parse_mode='Markdown',
        reply_markup=keyboard
    )

# ==================== ЗАПУСК БОТА ====================

if __name__ == "__main__":
    print("🤖 Бот запускается...")
    print("✅ Используется импорт из database.py")
    
    # Удаляем вебхук (если есть)
    bot.remove_webhook()
    
    # Запускаем опрос
    print("🔄 Запускаю polling...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
