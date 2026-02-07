import os
import logging
import random
import asyncio
import time
import html
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
    get_inventory,
    add_stat_point,
    get_top_players,
    use_item
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
CHOOSE_RACE, ENTER_NAME, MAIN_MENU, BATTLE_MENU, IN_BATTLE, SHOP_MENU, LEVEL_UP, INVENTORY_MENU = range(8)

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
    'goblin': 'https://img.freepik.com/free-photo/goblin-digital-art_23-2151061965.jpg',
    'slime': 'https://img.freepik.com/free-photo/green-slime-monster_23-2150911234.jpg',
    'zombie': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQRBEAcmeuf4tt0xnFUG1E8wcvZlSkLQcZkUw&s',
    'skeleton': 'https://img.freepik.com/free-photo/skeleton-warrior_23-2150911306.jpg',
    'mage': 'https://abrakadabra.fun/uploads/posts/2022-01/1642490542_3-abrakadabra-fun-p-temnii-mag-art-5.jpg',
    'vampire': 'https://img.freepik.com/free-photo/vampire_23-2150762308.jpg',
    'knight': 'https://img.freepig.com/free-photo/dark-knight_23-2150762270.jpg',
    'demon': 'https://img.freepik.com/free-photo/demon_23-2150762325.jpg',
    'lich': 'https://img.freepik.com/free-photo/lich_23-2150911246.jpg',
    'dragon': 'https://abrakadabra.fun/uploads/posts/2022-03/1646721873_1-abrakadabra-fun-p-pauk-fentezi-art-1.jpg',
    'dragon_young': 'https://img.freepik.com/free-photo/ancient-dragon_23-2150762338.jpg',
    'dragon_ancient': 'https://img.freepik.com/free-photo/ancient-dragon_23-2150762338.jpg',
    'titan': 'https://img.freepik.com/free-photo/titan_23-2150911270.jpg',
    'fallen_god': 'https://img.freepik.com/free-photo/fallen-god_23-2150911258.jpg',
    'village': 'https://img.freepik.com/premium-photo/tavern-like-game_808092-1770.jpg',
    'forest': 'https://img.freepik.com/premium-photo/ancient-forest-ai-generated_1127-13930.jpg',
    'castle': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTrAoGzKjgZxurLbxZ_Dyhtkm1gBqMUMtA87w&s',
    'dungeon': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSTZd9YHDcPOGmD8ezmHB0xD-HfA9O7OpgVyA&s',
    'training_camp': 'https://img.freepik.com/free-photo/medieval-camp-with-tents-night_107791-16981.jpg',
    'hell_gate': 'https://abrakadabra.fun/uploads/posts/2022-01/1642490542_3-abrakadabra-fun-p-temnii-mag-art-5.jpg',
    'throne_god': 'https://abrakadabra.fun/uploads/posts/2022-03/1646721873_1-abrakadabra-fun-p-pauk-fentezi-art-1.jpg',
    'shop': 'https://img.freepik.com/premium-photo/tavern-like-game_808092-1770.jpg',
    'levelup': 'https://i.pinimg.com/736x/7f/9a/97/7f9a97fdbbd70577225c213ad8a6e75c.jpg',
    'inventory': 'https://i.imgur.com/6QyTK2F.jpeg'  # Исправленная ссылка на изображение инвентаря
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
    'rank_d_weapon': {
        'name': '⚔️ Меч D-ранга',
        'description': '+5 к силе (требуется D-ранг)',
        'price': 200,
        'type': 'weapon',
        'effect': 5,
        'available': True,
        'required_rank': 'D'
    },
    'rank_c_armor': {
        'name': '🛡️ Броня C-ранга',
        'description': '+10 к здоровью (требуется C-ранг)',
        'price': 300,
        'type': 'armor',
        'effect': 10,
        'available': True,
        'required_rank': 'C'
    },
    'rank_b_artifact': {
        'name': '💎 Артефакт B-ранга',
        'description': '+15 к интеллекту (требуется B-ранг)',
        'price': 500,
        'type': 'artifact',
        'effect': 15,
        'available': True,
        'required_rank': 'B'
    }
}

# Определение локаций по рангам
LOCATIONS = {
    'E': {
        'name': '🎪 Тренировочный лагерь',
        'description': 'Начинай свой путь здесь. Враги слабые, но хороши для тренировки.',
        'enemies': ['wolf', 'goblin', 'slime'],
        'image': IMAGE_URLS['training_camp'],
        'min_level': 1,
        'max_level': 5
    },
    'D': {
        'name': '🌲 Лес призраков',
        'description': 'Лес наполнен низкоуровневыми монстрами. Подходит для охотников D-ранга.',
        'enemies': ['wolf', 'zombie', 'goblin_warrior'],
        'image': IMAGE_URLS['forest'],
        'min_level': 5,
        'max_level': 10
    },
    'C': {
        'name': '🪦 Заброшенные катакомбы',
        'description': 'Катакомбы наполнены опасными существами. Требует навыков C-ранга.',
        'enemies': ['zombie', 'skeleton', 'mage'],
        'image': IMAGE_URLS['dungeon'],
        'min_level': 10,
        'max_level': 15
    },
    'B': {
        'name': '🏰 Руины древнего замка',
        'description': 'Замок охраняют могущественные существа. Только для охотников B-ранга.',
        'enemies': ['mage', 'vampire', 'knight'],
        'image': IMAGE_URLS['castle'],
        'min_level': 15,
        'max_level': 20
    },
    'A': {
        'name': '🌋 Врата в преисподнюю',
        'description': 'Портал в мир демонов. Только сильнейшие A-ранга могут здесь выжить.',
        'enemies': ['demon', 'lich', 'dragon_young'],
        'image': IMAGE_URLS['hell_gate'],
        'min_level': 20,
        'max_level': 25
    },
    'S': {
        'name': '⚡ Трон божества',
        'description': 'Последнее испытание. Только S-ранг может бросить вызов богу.',
        'enemies': ['dragon_ancient', 'titan', 'fallen_god'],
        'image': IMAGE_URLS['throne_god'],
        'min_level': 25,
        'max_level': 30
    }
}

# Расширенный список врагов с учетом рангов
ENEMIES = {
    'wolf': {
        'name': '🐺 Бешеный Волк',
        'health': 30,
        'max_health': 30,
        'min_damage': 3,
        'max_damage': 8,
        'exp': 15,
        'gold': 10,
        'rank': 'E',
        'description': 'Его глаза горят голодом, а клыки обнажены.',
        'image': IMAGE_URLS['wolf']
    },
    'goblin': {
        'name': '👹 Гоблин-разведчик',
        'health': 25,
        'max_health': 25,
        'min_damage': 2,
        'max_damage': 6,
        'exp': 10,
        'gold': 8,
        'rank': 'E',
        'description': 'Мелкий и трусливый, но опасный в стае.',
        'image': IMAGE_URLS['goblin']
    },
    'slime': {
        'name': '🟢 Слизь',
        'health': 20,
        'max_health': 20,
        'min_damage': 1,
        'max_damage': 4,
        'exp': 8,
        'gold': 5,
        'rank': 'E',
        'description': 'Желейная масса, медленная, но ядовитая.',
        'image': IMAGE_URLS['slime']
    },
    'zombie': {
        'name': '🧟 Гниющий Зомби',
        'health': 50,
        'max_health': 50,
        'min_damage': 5,
        'max_damage': 12,
        'exp': 25,
        'gold': 20,
        'rank': 'D',
        'description': 'Медленный, но его удары заражают страхом.',
        'image': IMAGE_URLS['zombie']
    },
    'goblin_warrior': {
        'name': '⚔️ Гоблин-воин',
        'health': 40,
        'max_health': 40,
        'min_damage': 6,
        'max_damage': 14,
        'exp': 20,
        'gold': 15,
        'rank': 'D',
        'description': 'Более опытный и опасный, чем его собратья.',
        'image': IMAGE_URLS['goblin']
    },
    'skeleton': {
        'name': '💀 Скелет-воин',
        'health': 45,
        'max_health': 45,
        'min_damage': 7,
        'max_damage': 15,
        'exp': 22,
        'gold': 18,
        'rank': 'C',
        'description': 'Оживленные кости с ржавым мечом.',
        'image': IMAGE_URLS['skeleton']
    },
    'mage': {
        'name': '🔮 Темный Чернокнижник',
        'health': 40,
        'max_health': 40,
        'min_damage': 8,
        'max_damage': 18,
        'exp': 40,
        'gold': 35,
        'rank': 'C',
        'description': 'Окружен темной аурой и шепчет заклинания.',
        'image': IMAGE_URLS['mage']
    },
    'vampire': {
        'name': '🦇 Молодой вампир',
        'health': 70,
        'max_health': 70,
        'min_damage': 10,
        'max_damage': 20,
        'exp': 60,
        'gold': 50,
        'rank': 'B',
        'description': 'Пьет кровь жертв и восстанавливается.',
        'image': IMAGE_URLS['vampire']
    },
    'knight': {
        'name': '⚔️ Проклятый рыцарь',
        'health': 80,
        'max_health': 80,
        'min_damage': 12,
        'max_damage': 22,
        'exp': 70,
        'gold': 60,
        'rank': 'B',
        'description': 'Броня сияет темной энергией.',
        'image': IMAGE_URLS['knight']
    },
    'demon': {
        'name': '😈 Младший демон',
        'health': 100,
        'max_health': 100,
        'min_damage': 15,
        'max_damage': 25,
        'exp': 100,
        'gold': 80,
        'rank': 'A',
        'description': 'Призван из бездны, жаждет разрушения.',
        'image': IMAGE_URLS['demon']
    },
    'lich': {
        'name': '💀 Лич',
        'health': 90,
        'max_health': 90,
        'min_damage': 18,
        'max_damage': 28,
        'exp': 120,
        'gold': 100,
        'rank': 'A',
        'description': 'Бессмертный некромант с армией нежити.',
        'image': IMAGE_URLS['lich']
    },
    'dragon_young': {
        'name': '🐉 Молодой дракон',
        'health': 120,
        'max_health': 120,
        'min_damage': 20,
        'max_damage': 30,
        'exp': 150,
        'gold': 120,
        'rank': 'A',
        'description': 'Еще не достиг полной силы, но уже опасен.',
        'image': IMAGE_URLS['dragon_young']
    },
    'dragon_ancient': {
        'name': '🐉 Древний Дракон',
        'health': 200,
        'max_health': 200,
        'min_damage': 25,
        'max_damage': 40,
        'exp': 300,
        'gold': 200,
        'rank': 'S',
        'description': 'Владыка небес. Его пламя сжигает все живое.',
        'image': IMAGE_URLS['dragon_ancient']
    },
    'titan': {
        'name': '🏔️ Титан',
        'health': 250,
        'max_health': 250,
        'min_damage': 30,
        'max_damage': 45,
        'exp': 350,
        'gold': 250,
        'rank': 'S',
        'description': 'Ходячая гора из плоти и камня.',
        'image': IMAGE_URLS['titan']
    },
    'fallen_god': {
        'name': '👑 Падший Бог',
        'health': 300,
        'max_health': 300,
        'min_damage': 35,
        'max_damage': 50,
        'exp': 500,
        'gold': 300,
        'rank': 'S',
        'description': 'Бывшее божество, жаждущее мести.',
        'image': IMAGE_URLS['fallen_god']
    }
}

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def calculate_rank(level, experience):
    """Определение ранга на основе уровня и опыта"""
    if level >= 30:
        return 'S'
    elif level >= 25:
        return 'A'
    elif level >= 20:
        return 'B'
    elif level >= 15:
        return 'C'
    elif level >= 10:
        return 'D'
    else:
        return 'E'

def get_rank_icon(rank):
    """Получение иконки для ранга"""
    icons = {
        'E': '🆕',
        'D': '🟢',
        'C': '🔵',
        'B': '🟣',
        'A': '🟠',
        'S': '⚡'
    }
    return icons.get(rank, '🆕')

def get_rank_color(rank):
    """Получение цвета для ранга"""
    colors = {
        'E': '#808080',  # Серый
        'D': '#00FF00',  # Зеленый
        'C': '#0000FF',  # Синий
        'B': '#800080',  # Фиолетовый
        'A': '#FF8C00',  # Оранжевый
        'S': '#FF0000'   # Красный
    }
    return colors.get(rank, '#808080')

def get_available_locations(character_rank, character_level):
    """Получение доступных локаций для ранга и уровня"""
    available = []
    rank_order = ['E', 'D', 'C', 'B', 'A', 'S']
    
    for rank_key, location_data in LOCATIONS.items():
        rank_index = rank_order.index(rank_key)
        player_rank_index = rank_order.index(character_rank)
        
        # Игрок может посещать локации своего ранга и ниже
        if rank_index <= player_rank_index:
            # Проверяем уровень
            if (character_level >= location_data['min_level'] and 
                character_level <= location_data['max_level']):
                available.append((rank_key, location_data))
    
    return available

def get_next_rank_info(current_rank, current_level):
    """Получение информации о следующем ранге"""
    rank_progression = {
        'E': {'next': 'D', 'level': 10},
        'D': {'next': 'C', 'level': 15},
        'C': {'next': 'B', 'level': 20},
        'B': {'next': 'A', 'level': 25},
        'A': {'next': 'S', 'level': 30},
        'S': {'next': None, 'level': None}
    }
    
    if current_rank == 'S':
        return "🏆 Ты достиг максимального ранга!"
    
    next_rank = rank_progression[current_rank]['next']
    required_level = rank_progression[current_rank]['level']
    
    if current_level >= required_level:
        return f"{get_rank_icon(next_rank)} {next_rank}-ранг (ДОСТИГНУТ!)"
    else:
        return f"{get_rank_icon(next_rank)} {next_rank}-ранг (требуется {required_level} уровень)"

def create_progress_bar(current, maximum, length=10):
    """Создает текстовый индикатор прогресса"""
    if maximum <= 0:
        return "▯" * length
    
    percent = current / maximum
    filled = int(length * percent)
    empty = length - filled
    
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
    """Рассчитывает прогресс опета для текущего уровня"""
    xp_for_next_level = level * 100
    
    xp_spent = 0
    if level > 1:
        xp_spent = ((level - 1) * level * 100) // 2
    
    current_xp_on_level = experience - xp_spent
    max_xp_on_level = level * 100
    
    percent = min(current_xp_on_level / max_xp_on_level, 1.0) if max_xp_on_level > 0 else 0
    
    return current_xp_on_level, max_xp_on_level, percent

def get_xp_bar(level, experience, length=10):
    """Создает индикатор опыта"""
    current_xp, max_xp, percent = get_xp_progress(level, experience)
    
    if max_xp <= 0:
        return "▯" * length
    
    filled = int(length * percent)
    empty = length - filled
    
    if percent >= 1.0:
        bar = "⭐" * length
    else:
        bar = "✨" * filled + "⚫" * empty
    
    return f"{bar} {current_xp}/{max_xp} XP"

# --- КЛАВИАТУРЫ ---

def get_main_menu_keyboard(user_id=None):
    """Клавиатура главного меню"""
    keyboard = []
    
    if user_id:
        character = get_character(user_id)
        if character:
            rank = character.get('rank', 'E')
            rank_icon = get_rank_icon(rank)
            
            # Добавляем строку с рангом
            keyboard.append([
                InlineKeyboardButton(
                    f"{rank_icon} {rank}-ранг охотника",
                    callback_data='rank_info'
                )
            ])
    
    # Всегда показываем основные кнопки
    keyboard.append([InlineKeyboardButton("📜 Герой", callback_data='profile'), 
                     InlineKeyboardButton("🎒 Инвентарь", callback_data='inventory')])
    keyboard.append([InlineKeyboardButton("⚔️ НА БИТВУ!", callback_data='battle_menu')])
    
    # Проверяем, есть ли очки характеристик для прокачки
    if user_id:
        character = get_character(user_id)
        if character and character.get('stat_points', 0) > 0:
            keyboard.append([InlineKeyboardButton(f"🌟 ПРОКАЧАТЬ ХАР-КИ ({character['stat_points']} очков)", callback_data='level_up_menu')])
    
    keyboard.append([InlineKeyboardButton("🛍 Торговец", callback_data='shop'), InlineKeyboardButton("🏆 Зал славы", callback_data='stats')])
    keyboard.append([InlineKeyboardButton("👑 Топ игроков", callback_data='top_players'), InlineKeyboardButton("📜 Помощь", callback_data='help')])
    keyboard.append([InlineKeyboardButton("🔄 Реинкарнация (Сброс)", callback_data='restart')])
    
    return InlineKeyboardMarkup(keyboard)

def get_level_up_keyboard(character, stat_points):
    """Клавиатура распределения характеристик с отображением текущих значений"""
    keyboard = []
    
    if stat_points > 0:
        # Заголовок
        keyboard.append([
            InlineKeyboardButton(
                f"🎯 ОЧКОВ ДЛЯ ПРОКАЧКИ: {stat_points}",
                callback_data='info_only'
            )
        ])
        
        # Кнопки характеристик
        keyboard.append([
            InlineKeyboardButton(
                f"💪 СИЛА: {character['strength']}",
                callback_data='levelup_strength'
            )
        ])
        keyboard.append([
            InlineKeyboardButton(
                f"🏹 ЛОВКОСТЬ: {character['agility']}",
                callback_data='levelup_agility'
            )
        ])
        keyboard.append([
            InlineKeyboardButton(
                f"🧠 ИНТЕЛЛЕКТ: {character['intelligence']}",
                callback_data='levelup_intelligence'
            )
        ])
        
        # Кнопка "Назад"
        keyboard.append([
            InlineKeyboardButton(f"🔙 В главное меню", callback_data='back_to_main')
        ])
    else:
        keyboard.append([
            InlineKeyboardButton("🔙 В главное меню", callback_data='back_to_main')
        ])
    
    return InlineKeyboardMarkup(keyboard)

def get_inventory_keyboard(inventory_items, page=0, items_per_page=5):
    """Клавиатура для инвентаря с пагинацией"""
    keyboard = []
    
    if not inventory_items:
        keyboard.append([InlineKeyboardButton("🛍 В магазин", callback_data='shop')])
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')])
        return InlineKeyboardMarkup(keyboard)
    
    # Определяем, сколько всего страниц
    total_pages = (len(inventory_items) - 1) // items_per_page + 1
    start_idx = page * items_per_page
    end_idx = min(start_idx + items_per_page, len(inventory_items))
    
    # Добавляем предметы текущей страницы
    for item in inventory_items[start_idx:end_idx]:
        item_text = f"{item['item_name']} ({item['quantity']} шт.)"
        
        # Проверяем, можно ли использовать предмет
        if item['item_type'] == 'potion':
            # Для зелий добавляем кнопку использования
            callback_data = f"use_{item['item_key']}"
            keyboard.append([InlineKeyboardButton(f"✨ Использовать: {item_text}", callback_data=callback_data)])
        else:
            # Для других предметов просто информация
            keyboard.append([InlineKeyboardButton(f"📦 {item_text}", callback_data='item_info')])
    
    # Добавляем кнопки пагинации, если нужно
    pagination_buttons = []
    
    if page > 0:
        pagination_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f'inv_page_{page-1}'))
    
    if end_idx < len(inventory_items):
        pagination_buttons.append(InlineKeyboardButton("Вперед ➡️", callback_data=f'inv_page_{page+1}'))
    
    if pagination_buttons:
        keyboard.append(pagination_buttons)
    
    # Информация о странице
    keyboard.append([InlineKeyboardButton(f"📄 Страница {page+1}/{total_pages}", callback_data='page_info')])
    
    # Кнопки действий
    keyboard.append([
        InlineKeyboardButton("🛍 В магазин", callback_data='shop'),
        InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')
    ])
    
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

def get_battle_menu_keyboard(character):
    """Клавиатура меню боя с локациями по рангу"""
    keyboard = []
    
    if not character:
        return InlineKeyboardMarkup(keyboard)
    
    rank = character.get('rank', 'E')
    level = character.get('level', 1)
    available_locations = get_available_locations(rank, level)
    
    for rank_key, location in available_locations:
        rank_icon = get_rank_icon(rank_key)
        keyboard.append([
            InlineKeyboardButton(
                f"{rank_icon} {location['name']} ({rank_key}-ранг)",
                callback_data=f'location_{rank_key}'
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Вернуться в лагерь", callback_data='back_to_main')])
    return InlineKeyboardMarkup(keyboard)

def get_location_enemies_keyboard(location_rank):
    """Клавиатура выбора врагов в локации"""
    keyboard = []
    
    location = LOCATIONS.get(location_rank)
    if not location:
        return InlineKeyboardMarkup(keyboard)
    
    for enemy_key in location['enemies']:
        enemy = ENEMIES.get(enemy_key)
        if enemy:
            rank_icon = get_rank_icon(enemy['rank'])
            keyboard.append([
                InlineKeyboardButton(
                    f"{rank_icon} {enemy['name']} ({enemy['rank']}-ранг)",
                    callback_data=f'battle_{enemy_key}'
                )
            ])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад к локациям", callback_data='back_to_battle_menu')])
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
        rank = character.get('rank', 'E')
        
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
        
        # Предметы по рангам
        shop_items_by_rank = {
            'D': SHOP_ITEMS['rank_d_weapon'],
            'C': SHOP_ITEMS['rank_c_armor'],
            'B': SHOP_ITEMS['rank_b_artifact']
        }
        
        rank_order = ['E', 'D', 'C', 'B', 'A', 'S']
        player_rank_index = rank_order.index(rank)
        
        for rank_key, item in shop_items_by_rank.items():
            rank_index = rank_order.index(rank_key)
            if player_rank_index >= rank_index:
                keyboard.append([
                    InlineKeyboardButton(
                        f"{item['name']} - {item['price']}💰",
                        callback_data=f'buy_{list(shop_items_by_rank.keys()).index(rank_key)}'
                    )
                ])
        
        keyboard.append([
            InlineKeyboardButton(f"💰 Твой баланс: {gold}", callback_data='balance_info')
        ])
        
        keyboard.append([
            InlineKeyboardButton("🎒 Мой инвентарь", callback_data='inventory'),
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
    
    await update.message.reply_photo(
        photo=IMAGE_URLS['village'],
        caption=f"🏰 *ДОБРО ПОЖАЛОВАТЬ В МИР ГЕРОЕВ!* 🏰\n\n"
                f"👋 Приветствую тебя, путник *{user.first_name}*!\n\n"
                f"📜 _Древние легенды гласят, что именно ты изменишь судьбу этого мира._\n"
                f"Ты стоишь на главной площади деревни. Впереди — великие свершения!",
        parse_mode='Markdown'
    )
    
    character = get_character(user.id)
    
    if character:
        # Проверяем, есть ли нераспределенные очки характеристик
        if character.get('stat_points', 0) > 0:
            await update.message.reply_text(
                f"⚔️ С возвращением, *{character['character_name']}*!\n"
                f"✨ У тебя есть {character['stat_points']} очко(в) характеристик для распределения!",
                parse_mode='Markdown',
                reply_markup=get_level_up_keyboard(character, character['stat_points'])
            )
            return LEVEL_UP
        else:
            await update.message.reply_text(
                f"⚔️ С возвращением, *{character['character_name']}*!\nТвой меч все еще остер.",
                reply_markup=get_main_menu_keyboard(user.id),
                parse_mode='Markdown'
            )
            return MAIN_MENU
    else:
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

🏆 **Система рангов:**
🆕 E-ранг — Начинающие охотники (уровень 1-9)
🟢 D-ранг — Рядовые бойцы (уровень 10-14)
🔵 C-ранг — Средний уровень (уровень 15-19)
🟣 B-ранг — Сильные охотники (уровень 20-24)
🟠 A-ранг — Элита (уровень 25-29)
⚡ S-ранг — Легенды (уровень 30+)

🗺 **Локации по рангам:**
• E-ранг: 🎪 Тренировочный лагерь
• D-ранг: 🌲 Лес призраков
• C-ранг: 🪦 Заброшенные катакомбы
• B-ранг: 🏰 Руины древнего замка
• A-ранг: 🌋 Врата в преисподнюю
• S-ранг: ⚡ Трон божества

💪 **Способности рас и мана:**
• 👨 *Человек*: Адаптивность (10 маны) - временный буст всех характеристик
• 🧝 *Эльф*: Магический дар (20 маны) - мощный магический удар
• ⚒️ *Дварф*: Каменная кожа (15 маны) - лечение и защита
• 👹 *Орк*: Ярость (5 маны) - двойной удор с риском самоповреждения

👤 **Создание героя:**
1. Выбери расу (влияет на стиль бой)
2. Назови героя (это имя войдет в историю)

⚔️ **Классы и Бонусы:**
👨 **Человек** — `Баланс` (+1 ко всем статам)
🧝 **Эльф** — `Магия` (+50% маны)
⚒️ **Дварф** — `Живучесть` (+20% здоровья)
👹 **Орк** — `Ярость` (Рискованные, но мощные атаки)

📈 **Прокачка:**
• За каждый уровень получаешь *3 очка характеристик*
• Можешь распределить их между:
  💪 *СИЛА* - Увеличивает урон в ближнем бою
  🏹 *ЛОВКОСТЬ* - Увеличивает защиту и шанс увернуться
  🧠 *ИНТЕЛЛЕКТ* - Увеличивает магический урон и ману

🎒 **Инвентарь:**
• Теперь есть отдельная вкладка инвентаря!
• Используй зелья для восстановления здоровья и маны
• Все купленные предметы хранятся в инвентаре

💊 **Магазин:**
• Зелья здоровья - Быстрое восстановление в бою
• Зелья маны - Восполнение магической энергии
• Оружие и броня по рангам

🔄 **Регенерация:**
• Здоровье: 5% каждые 5 минут
• Мана: 10% каждые 5 минут

🗡 **Тактика боя:**
• ⚔️ *Атака* - Базовый удар оружием (зависит от силы)
• 🛡️ *Защита* - Снижает урон на 50%
• ✨ *Способность* - Уникальный навык твоей расы (тратит ману)
• 🏃 *Сбежать* - Шанс 50% покинуть бой

🏆 **Соревнование:**
• Заходи в "👑 Топ игроков" чтобы увидеть лучших охотников
• Повышай свой рейтинг, чтобы попасть в топ

_Удачи, герой! Пусть боги хранят тебя._ 🏹
"""
    if update.message:
        await update.message.reply_text(help_text, parse_mode='Markdown')
    elif update.callback_query:
        await update.callback_query.message.reply_text(help_text, parse_mode='Markdown')

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена и выход из всех состояний"""
    user = update.effective_user
    
    if update.callback_query:
        await update.callback_query.answer()
    
    await update.message.reply_text(
        "❌ Действие отменено. Ты возвращаешься в деревню.\n\n"
        "Напиши /start, чтобы начать заново.",
        reply_markup=None,
        parse_mode='Markdown'
    )
    
    # Очищаем все данные боя, если есть
    if user.id in battle_sessions:
        del battle_sessions[user.id]
    
    return ConversationHandler.END

# --- ОБРАБОТЧИКИ СОЗДАНИЯ ПЕРСОНАЖА ---

async def choose_race(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора расы"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == 'race_info':
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
    
    race_key = data[5:]  # Убираем 'race_'
    context.user_data['selected_race'] = race_key
    
    races = get_all_races()
    race_data = races[race_key]
    image_url = IMAGE_URLS.get(race_key, IMAGE_URLS['human'])
    
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
    
    if len(character_name) < 2 or len(character_name) > 20:
        await update.message.reply_text(
            "❌ <b>Ошибка летописца!</b>\nИмя должно быть от 2 до 20 символов. Попробуй еще раз:",
            parse_mode='HTML'
        )
        return ENTER_NAME
    
    race_key = context.user_data.get('selected_race', 'human')
    
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
        
        # Экранируем имя персонажа для HTML
        escaped_character_name = html.escape(character_name)
        
        await update.message.reply_photo(
            photo=image_url,
            caption=f"🎉 <b>РОЖДЕНИЕ ГЕРОЯ!</b>\n\n"
                   f"🏷️ <b>Имя:</b> {escaped_character_name}\n"
                   f"🎭 <b>Раса:</b> {race_data['name']}\n"
                   f"✨ <b>Дар:</b> {race_data['racial_ability']}\n\n"
                   f"📈 <b>Стартовые очки:</b> 3 (распредели в профиле!)\n"
                   f"🏆 <b>Начальный ранг:</b> E",
            parse_mode='HTML'
        )
        
        await update.message.reply_text(
            f"Твоё приключение начинается! Куда направимся?",
            reply_markup=get_main_menu_keyboard(user.id)
        )
        return MAIN_MENU
    else:
        await update.message.reply_text(
            f"❌ Ошибка магии: {message}\n\n"
            f"Начни заново с /start",
            parse_mode='HTML'
        )
        return ConversationHandler.END

# --- ОБРАБОТЧИКИ ПРОКАЧКИ ХАРАКТЕРИСТИК ---

async def level_up_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик прокачки характеристик"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == 'back_to_main':
        await query.edit_message_text(
            text="Возвращаюсь в главное меню...",
            reply_markup=get_main_menu_keyboard(user_id),
            parse_mode='Markdown'
        )
        return MAIN_MENU
    
    elif data == 'info_only':
        # Это информационная кнопка, ничего не делаем
        await query.answer("🎯 Выбери характеристику для прокачки!", show_alert=False)
        return LEVEL_UP
    
    elif data.startswith('levelup_'):
        stat_type = data[8:]  # Убираем 'levelup_'
        
        if stat_type in ['strength', 'agility', 'intelligence']:
            # Получаем текущего персонажа ДО прокачки
            character_before = get_character(user_id)
            old_value = character_before[stat_type]
            
            # Пытаемся улучшить характеристику
            success, message = add_stat_point(user_id, stat_type)
            
            if success:
                # Получаем обновленного персонажа ПОСЛЕ прокачки
                character_after = get_character(user_id)
                new_value = character_after[stat_type]
                stat_points_left = character_after.get('stat_points', 0)
                
                # Определяем название характеристики для русского отображения
                stat_names = {
                    'strength': 'Сила 💪',
                    'agility': 'Ловкость 🏹', 
                    'intelligence': 'Интеллект 🧠'
                }
                stat_name = stat_names.get(stat_type, stat_type)
                
                # Показываем ОЧЕНЬ ЯВНОЕ подтверждение прокачки
                await query.message.reply_text(
                    f"✨ *УСПЕШНАЯ ПРОКАЧКА!* ✨\n\n"
                    f"✅ **{stat_name}** успешно повышена!\n"
                    f"📊 Было: `{old_value}` → Стало: `{new_value}`\n\n"
                    f"🎯 Осталось очков: `{stat_points_left}`",
                    parse_mode='Markdown'
                )
                
                # Если еще есть очки, показываем обновленную клавиатуру
                if stat_points_left > 0:
                    # Обновляем сообщение с клавиатурой
                    await query.edit_message_text(
                        text=f"🎯 *РАСПРЕДЕЛЕНИЕ ХАРАКТЕРИСТИК*\n\n"
                             f"📊 Очков доступно: `{stat_points_left}`\n\n"
                             f"👇 *Выбери следующую характеристику:*",
                        reply_markup=get_level_up_keyboard(character_after, stat_points_left),
                        parse_mode='Markdown'
                    )
                    return LEVEL_UP
                else:
                    # Все очки распределены, возвращаем в главное меню
                    await query.message.reply_text(
                        f"🏆 *ВСЕ ОЧКИ РАСПРЕДЕЛЕНЫ!*\n\n"
                        f"🎯 Твой герой стал сильнее!\n"
                        f"📊 Итоговые характеристики:\n"
                        f"💪 Сила: `{character_after['strength']}`\n"
                        f"🏹 Ловкость: `{character_after['agility']}`\n"
                        f"🧠 Интеллект: `{character_after['intelligence']}`\n\n"
                        f"_Возвращаюсь в главное меню..._",
                        reply_markup=get_main_menu_keyboard(user_id),
                        parse_mode='Markdown'
                    )
                    return MAIN_MENU
            else:
                # Ошибка при прокачке
                await query.answer(f"❌ {message}", show_alert=True)
                return LEVEL_UP
    
    return LEVEL_UP

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
    
    elif data == 'inventory':
        await show_inventory_menu(query, user_id)
        return INVENTORY_MENU
    
    elif data == 'battle_menu':
        await show_battle_menu(query, user_id)
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
    
    elif data == 'level_up_menu':
        character = get_character(user_id)
        if character and character.get('stat_points', 0) > 0:
            await query.edit_message_text(
                text=f"✨ *РАСПРЕДЕЛЕНИЕ ХАРАКТЕРИСТИК*\n\n"
                     f"🎯 Очков доступно: `{character['stat_points']}`\n\n"
                     f"👇 *Выбери характеристику для улучшения:*",
                reply_markup=get_level_up_keyboard(character, character['stat_points']),
                parse_mode='Markdown'
            )
            return LEVEL_UP
        else:
            await query.answer("❌ У тебя нет очков характеристик для распределения!", show_alert=True)
            return MAIN_MENU
    
    elif data == 'rank_info':
        await rank_info_handler(update, context)
        return MAIN_MENU
    
    elif data == 'top_players':
        await show_top_players(query, user_id)
        return MAIN_MENU

async def rank_info_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик информации о системе рангов"""
    query = update.callback_query
    await query.answer()
    
    rank_info_text = """
🏆 *СИСТЕМА РАНГОВ ОХОТНИКОВ*

🆕 *E-ранг* — Начинающие охотники
• Способности лишь немного выше человеческих
• Сон Джинву начинал свой путь здесь
• Доступно: Тренировочный лагерь

🟢 *D-ранг* — Рядовые бойцы
• Могут справляться с низкоуровневыми подземельями
• Способны на базовые магические атаки
• Доступно: Лес призраков

🔵 *C-ранг* — Средний уровень
• Могут зарабатывать на жизнь рейдами
• Имеют развитые боевые навыки
• Доступно: Заброшенные катакомбы

🟣 *B-ранг* — Сильные охотники
• Часто лидеры в небольших группах
• Обладают уникальными способностями
• Доступно: Руины древнего замка

🟠 *A-ранг* — Элита
• Обладают огромной мощью
• Могут в одиночку справляться с S-ранговыми угрозами
• Доступно: Врата в преисподнюю

⚡ *S-ранг* — Высший ранг
• Магическая сила не поддается измерению
• Легенды среди охотников
• Доступно: Трон божества

*Для повышения ранга:*
1. Повышай уровень персонажа
2. Набери необходимый опыт
3. Пройди испытание следующего ранга

_Сила приходит с опытом, охотник. Стремись выше!_
"""
    
    await query.edit_message_text(
        text=rank_info_text,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard(query.from_user.id)
    )

async def show_profile(query, user_id):
    """Показ профиля персонажа с ранговой системой"""
    character = get_character(user_id)
    
    if not character:
        await query.edit_message_text(
            text="❌ Герой не найден!",
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    # Рассчитываем ранг, если его нет в базе
    if not character.get('rank'):
        rank = calculate_rank(character['level'], character['experience'])
        update_character_stats(user_id, rank=rank)
        character['rank'] = rank
    
    rank = character['rank']
    rank_icon = get_rank_icon(rank)
    races = get_all_races()
    race_data = races.get(character['race'], {})
    image_url = IMAGE_URLS.get(character['race'], IMAGE_URLS['human'])
    
    # Создаем индикаторы
    health_bar = get_health_bar(character['health'], character['max_health'])
    mana_bar = get_mana_bar(character['mana'], character['max_mana'])
    xp_bar = get_xp_bar(character['level'], character['experience'])
    
    # Получаем следующий ранг
    next_rank_info = get_next_rank_info(rank, character['level'])
    
    # Проверяем регенерацию
    last_regen = character.get('last_regeneration')
    regen_info = ""
    if last_regen:
        if isinstance(last_regen, str):
            try:
                last_regen = datetime.fromisoformat(last_regen.replace('Z', '+00:00'))
            except:
                last_regen = None
        
        if last_regen:
            time_diff = datetime.now() - last_regen
            if time_diff.total_seconds() >= 300:
                regen_info = "\n🔄 *Готов к регенерации!*"
            else:
                minutes_left = int((300 - time_diff.total_seconds()) / 60)
                seconds_left = int(300 - time_diff.total_seconds()) % 60
                regen_info = f"\n⏳ *Регенерация через:* {minutes_left}:{seconds_left:02d}"
    
    # Статистика характеристик
    stat_points = character.get('stat_points', 0)
    stats_info = ""
    if stat_points > 0:
        stats_info = f"\n\n🎯 *Нераспределенные очки:* `{stat_points}`"
    
    await query.message.reply_photo(
        photo=image_url,
        caption=f"👤 *ПАСПОРТ ОХОТНИКА: {character['character_name']}*\n"
               f"{rank_icon} *{rank}-ранг* • ⭐ Уровень {character['level']}\n\n"
               f"❤️ ЗДОРОВЬЕ\n{health_bar}\n\n"
               f"🔮 МАНА\n{mana_bar}\n\n"
               f"✨ ОПЫТ\n{xp_bar}{regen_info}{stats_info}\n\n"
               f"🎯 *Следующий ранг:* {next_rank_info}",
        parse_mode='Markdown'
    )
    
    # Получаем инвентарь
    inventory = get_inventory(user_id)
    inventory_text = "🎒 *Инвентарь пуст*"
    if inventory:
        inventory_text = "🎒 *ИНВЕНТАРЬ*\n"
        total_items = 0
        for item in inventory:
            inventory_text += f"• {item['item_name']}: {item['quantity']} шт.\n"
            total_items += item['quantity']
        inventory_text += f"\n📦 Всего предметов: {total_items}"
    
    profile_text = (
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⚔️ *БОЕВЫЕ ПАРАМЕТРЫ*\n"
        f"💪 **Сила:**      `{character['strength']}`\n"
        f"🏹 **Ловкость:**  `{character['agility']}`\n"
        f"🧠 **Интеллект:** `{character['intelligence']}`\n"
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
        reply_markup=get_main_menu_keyboard(user_id)
    )

# --- ОБРАБОТЧИКИ ИНВЕНТАРЯ ---

async def show_inventory_menu(query, user_id, page=0):
    """Показ меню инвентаря"""
    inventory = get_inventory(user_id)
    character = get_character(user_id)
    
    if not character:
        await query.edit_message_text(
            text="❌ Герой не найден!",
            reply_markup=get_main_menu_keyboard(user_id),
            parse_mode='Markdown'
        )
        return
    
    # Рассчитываем статистику инвентаря
    total_items = sum(item['quantity'] for item in inventory) if inventory else 0
    potions_count = sum(item['quantity'] for item in inventory if item['item_type'] == 'potion') if inventory else 0
    equipment_count = sum(item['quantity'] for item in inventory if item['item_type'] in ['weapon', 'armor', 'artifact']) if inventory else 0
    
    if not inventory:
        inventory_text = (
            f"🎒 *ТВОЙ ИНВЕНТАРЬ*\n\n"
            f"📦 *Пусто!*\n\n"
            f"Твой рюкзак легок, как перышко...\n"
            f"Загляни в лавку торговца, чтобы заполнить его!"
        )
        
        await query.message.reply_text(
            text=inventory_text,
            parse_mode='Markdown'
        )
        
        await query.message.reply_text(
            text="🛍 *Что хочешь сделать?*",
            reply_markup=get_inventory_keyboard(inventory, page),
            parse_mode='Markdown'
        )
        return INVENTORY_MENU
    
    inventory_text = f"🎒 *ТВОЙ ИНВЕНТАРЬ*\n\n"
    inventory_text += f"📊 *Статистика:*\n"
    inventory_text += f"📦 Всего предметов: `{total_items}`\n"
    inventory_text += f"💊 Зелий: `{potions_count}`\n"
    inventory_text += f"⚔️ Снаряжения: `{equipment_count}`\n\n"
    inventory_text += f"👇 *Выбери предмет для использования:*"
    
    # Отправляем текстовое сообщение вместо фото, чтобы избежать ошибки
    await query.message.reply_text(
        text=inventory_text,
        parse_mode='Markdown'
    )
    
    # Показываем инвентарь с пагинацией
    await query.message.reply_text(
        text="📋 *Список предметов:*",
        reply_markup=get_inventory_keyboard(inventory, page),
        parse_mode='Markdown'
    )
    
    return INVENTORY_MENU

async def use_item_from_inventory(query, user_id, item_key):
    """Использование предмета из инвентаря"""
    inventory = get_inventory(user_id)
    
    # Находим предмет в инвентаре
    item_to_use = None
    for item in inventory:
        if item['item_key'] == item_key:
            item_to_use = item
            break
    
    if not item_to_use:
        await query.answer("❌ Предмет не найден в инвентаре!", show_alert=True)
        return
    
    # Используем предмет
    success, message = use_item(
        user_id=user_id,
        item_key=item_to_use['item_key'],
        item_type=item_to_use['item_type'],
        item_name=item_to_use['item_name'],
        effect_amount=item_to_use['effect_amount']
    )
    
    if success:
        # Показываем сообщение об успешном использовании
        await query.answer(message, show_alert=True)
        
        # Получаем обновленного персонажа
        character = get_character(user_id)
        
        # Показываем обновленный инвентарь
        inventory = get_inventory(user_id)
        
        if inventory:
            # Обновляем сообщение с инвентарем
            total_items = sum(item['quantity'] for item in inventory)
            
            # Обновляем только текст, не фото
            inventory_text = f"✅ *Предмет использован!*\n\n"
            inventory_text += f"{message}\n\n"
            inventory_text += f"📦 В инвентаре осталось `{total_items}` предметов"
            
            await query.edit_message_text(
                text=inventory_text,
                reply_markup=get_inventory_keyboard(inventory, 0),
                parse_mode='Markdown'
            )
        else:
            # Инвентарь пуст
            inventory_text = f"✅ *Предмет использован!*\n\n"
            inventory_text += f"{message}\n\n"
            inventory_text += f"🎒 Твой инвентарь теперь пуст"
            
            await query.edit_message_text(
                text=inventory_text,
                reply_markup=get_inventory_keyboard([], 0),
                parse_mode='Markdown'
            )
    else:
        await query.answer(f"❌ {message}", show_alert=True)

async def inventory_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик меню инвентаря"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == 'back_to_main':
        await query.edit_message_text(
            text="🔙 Возвращаюсь в главное меню...",
            reply_markup=get_main_menu_keyboard(user_id),
            parse_mode='Markdown'
        )
        return MAIN_MENU
    
    elif data == 'shop':
        await show_shop(query, user_id)
        return SHOP_MENU
    
    elif data.startswith('inv_page_'):
        page = int(data.split('_')[2])
        inventory = get_inventory(user_id)
        await query.edit_message_text(
            text="📋 *Список предметов:*",
            reply_markup=get_inventory_keyboard(inventory, page),
            parse_mode='Markdown'
        )
        return INVENTORY_MENU
    
    elif data.startswith('use_'):
        item_key = data[4:]
        await use_item_from_inventory(query, user_id, item_key)
        return INVENTORY_MENU
    
    elif data in ['item_info', 'page_info']:
        # Информационные кнопки, ничего не делаем
        await query.answer("ℹ️ Выбери предмет для использования", show_alert=False)
        return INVENTORY_MENU

async def show_battle_menu(query, user_id):
    """Показ меню выбора локации по рангу"""
    character = get_character(user_id)
    
    if not character:
        await query.edit_message_text(
            text="❌ Герой не найден!",
            reply_markup=get_main_menu_keyboard(user_id),
            parse_mode='Markdown'
        )
        return
    
    rank = character.get('rank', 'E')
    rank_icon = get_rank_icon(rank)
    
    await query.message.reply_photo(
        photo=IMAGE_URLS['forest'],
        caption=f"{rank_icon} *ВЫБОР ЛОКАЦИИ*\n\n"
                f"📊 *Твой ранг:* {rank_icon} **{rank}-ранг**\n"
                f"⭐ *Уровень:* {character['level']}\n\n"
                f"Выбери место для охоты на монстров:",
        parse_mode='Markdown'
    )
    
    await query.message.reply_text(
        text="📜 *Доступные локации:*\n",
        parse_mode='Markdown',
        reply_markup=get_battle_menu_keyboard(character)
    )

async def show_shop(query, user_id):
    """Показ магазина"""
    character = get_character(user_id)
    
    if not character:
        await query.edit_message_text(
            text="❌ Герой не найден!",
            reply_markup=get_main_menu_keyboard(user_id),
            parse_mode='Markdown'
        )
        return
    
    rank = character.get('rank', 'E')
    rank_icon = get_rank_icon(rank)
    
    await query.message.reply_photo(
        photo=IMAGE_URLS['shop'],
        caption=f"🛖 *ЛАВКА СТАРОГО ТОРГОВЦА* 🛖\n\n"
                f"_Пахнет травами и стариной. На прилавке разложены снадобья:_\n\n"
                f"💰 *Твой кошелек:* `{character['gold']}` золотых\n"
                f"{rank_icon} *Твой ранг:* {rank}-ранг",
        parse_mode='Markdown'
    )
    
    shop_text = (
        "💊 *ЗЕЛЬЯ ЗДОРОВЬЯ*\n"
        "• Малое (+30 HP) — `25 золота`\n"
        "• Большое (+60 HP) — `50 золота`\n\n"
        "🔮 *ЭЛИКСИРЫ МАНЫ*\n"
        "• Малый (+20 MP) — `20 золота`\n"
        "• Большой (+40 MP) — `40 золота`\n\n"
        "⚔️ *Оружие и броня по рангам:*\n"
    )
    
    # Добавляем предметы по рангам
    rank_order = ['E', 'D', 'C', 'B', 'A', 'S']
    player_rank_index = rank_order.index(rank)
    
    for rank_key, item_key in [('D', 'rank_d_weapon'), ('C', 'rank_c_armor'), ('B', 'rank_b_artifact')]:
        if item_key in SHOP_ITEMS:
            item = SHOP_ITEMS[item_key]
            rank_index = rank_order.index(rank_key)
            if player_rank_index >= rank_index:
                shop_text += f"• {item['name']} — `{item['price']} золота`\n"
            else:
                shop_text += f"• {item['name']} — `{item['price']} золота` [Требуется {rank_key}-ранг]\n"
    
    shop_text += "\n_Торговец бормочет: 'Только лучшие товары для героев!'_"
    
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
            reply_markup=get_main_menu_keyboard(user_id),
            parse_mode='Markdown'
        )
        return MAIN_MENU
    
    elif data == 'inventory':
        await show_inventory_menu(query, user_id)
        return INVENTORY_MENU
    
    elif data == 'balance_info':
        character = get_character(user_id)
        if character:
            await query.answer(f"💰 У тебя {character['gold']} золота", show_alert=True)
        return SHOP_MENU
    
    elif data.startswith('buy_'):
        # Определяем, что покупаем
        if data == 'buy_small_health_potion':
            item_key = 'small_health_potion'
        elif data == 'buy_large_health_potion':
            item_key = 'large_health_potion'
        elif data == 'buy_small_mana_potion':
            item_key = 'small_mana_potion'
        elif data == 'buy_large_mana_potion':
            item_key = 'large_mana_potion'
        elif data == 'buy_0':
            item_key = 'rank_d_weapon'
        elif data == 'buy_1':
            item_key = 'rank_c_armor'
        elif data == 'buy_2':
            item_key = 'rank_b_artifact'
        else:
            await query.answer("❌ Неизвестный товар!", show_alert=True)
            return SHOP_MENU
        
        if item_key not in SHOP_ITEMS:
            await query.answer("❌ Такого товара нет в продаже!", show_alert=True)
            return SHOP_MENU
        
        item = SHOP_ITEMS[item_key]
        
        # Проверяем ранг для предметов по рангам
        if 'required_rank' in item:
            character = get_character(user_id)
            rank = character.get('rank', 'E')
            rank_order = ['E', 'D', 'C', 'B', 'A', 'S']
            
            player_rank_index = rank_order.index(rank)
            required_rank_index = rank_order.index(item['required_rank'])
            
            if player_rank_index < required_rank_index:
                await query.answer(f"❌ Для этого предмета требуется {item['required_rank']}-ранг!", show_alert=True)
                return SHOP_MENU
        
        # Покупаем предмет
        success, message = buy_item(
            user_id=user_id,
            item_key=item_key,
            item_type=item['type'],
            item_name=item['name'],
            price=item['price'],
            effect_amount=item.get('effect')
        )
        
        if success:
            character = get_character(user_id)
            
            await query.message.reply_text(
                f"✅ *УСПЕШНАЯ ПОКУПКА!*\n\n"
                f"🎁 Ты приобрел: {item['name']}\n"
                f"📝 {item['description']}\n"
                f"💰 Потрачено: {item['price']} золота\n"
                f"💳 Осталось: {character['gold']} золота\n\n"
                f"_Предмет добавлен в инвентарь_",
                parse_mode='Markdown'
            )
            
            await query.message.reply_text(
                text="🛖 *Что еще желаешь?*",
                reply_markup=get_shop_keyboard(character),
                parse_mode='Markdown'
            )
        else:
            await query.answer(f"❌ {message}", show_alert=True)
        
        return SHOP_MENU

async def show_stats(query, user_id):
    """Показ статистики с топом игроков"""
    character = get_character(user_id)
    
    if not character:
        await query.edit_message_text(
            text="❌ У тебя еще нет персонажа!",
            reply_markup=get_main_menu_keyboard(user_id),
            parse_mode='Markdown'
        )
        return
    
    total_battles = character.get('battle_wins', 0) + character.get('battle_losses', 0)
    win_rate = (character.get('battle_wins', 0) / total_battles * 100) if total_battles > 0 else 0
    
    current_xp, max_xp, percent = get_xp_progress(character['level'], character['experience'])
    
    rank = character.get('rank', 'E')
    rank_icon = get_rank_icon(rank)
    
    stats_text = (
        f"🏆 *ЗАЛ СЛАВЫ: {character['character_name']}*\n"
        f"{rank_icon} *Ранг:* {rank}-ранг\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⭐ *Уровень:* `{character['level']}`\n"
        f"✨ *Опыт:* `{character['experience']}` XP\n"
        f"📊 *Прогресс:* `{current_xp}/{max_xp}` ({percent:.1%})\n"
        f"{get_xp_bar(character['level'], character['experience'], length=15)}\n\n"
        f"💪 *Характеристики:*\n"
        f"Сила: `{character['strength']}` | "
        f"Ловкость: `{character['agility']}` | "
        f"Интеллект: `{character['intelligence']}`\n\n"
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
    
    # Получаем топ-5 игроков
    top_players = get_top_players(5)
    
    if top_players:
        stats_text += "\n\n🏆 *ТОП-5 ЛЕГЕНД СЕРВЕРА* 🏆\n"
        stats_text += "━━━━━━━━━━━━━━━━━━━━━━\n"
        
        for i, player in enumerate(top_players, 1):
            player_rank = player.get('rank', 'E')
            rank_icon = get_rank_icon(player_rank)
            win_rate_player = 0
            total_player_battles = player.get('battle_wins', 0) + player.get('battle_losses', 0)
            if total_player_battles > 0:
                win_rate_player = (player.get('battle_wins', 0) / total_player_battles * 100)
            
            medal = ""
            if i == 1:
                medal = "🥇"
            elif i == 2:
                medal = "🥈"  
            elif i == 3:
                medal = "🥉"
            else:
                medal = "🏅"
            
            # Экранируем имя игрока для Markdown
            safe_name = html.escape(player['character_name'])
            
            stats_text += (
                f"{medal} *{i}. {safe_name}*\n"
                f"   {rank_icon} {player_rank}-ранг | ⭐ Ур. {player['level']}\n"
                f"   ⚔️ {player.get('battle_wins', 0)} побед ({win_rate_player:.1f}%)\n"
                f"   💰 {player.get('gold', 0)} золота\n"
            )
            
            if i < len(top_players):
                stats_text += "   ─────────────────\n"
    
    await query.edit_message_text(
        text=stats_text,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard(user_id)
    )

async def show_top_players(query, user_id):
    """Показ топа игроков"""
    top_players = get_top_players(10)  # Берем топ-10 для полноценной таблицы
    
    if not top_players:
        await query.edit_message_text(
            text="🏆 *ТОП ИГРОКОВ*\n\nНа сервере еще нет легенд... Стань первым!",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(user_id)
        )
        return
    
    # Получаем информацию о текущем игроке
    current_player = get_character(user_id)
    player_position = None
    
    # Находим позицию текущего игрока в топе
    for i, player in enumerate(top_players, 1):
        if player['character_name'] == current_player['character_name']:
            player_position = i
            break
    
    # Если игрок не в топ-10, проверяем его позицию среди всех
    if not player_position and current_player:
        all_players = get_top_players(100)  # Берем больше для поиска позиции
        for i, player in enumerate(all_players, 1):
            if player['character_name'] == current_player['character_name']:
                player_position = i
                break
    
    top_text = "🏆 *ТОП ЛЕГЕНД СЕРВЕРА* 🏆\n"
    top_text += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for i, player in enumerate(top_players, 1):
        player_rank = player.get('rank', 'E')
        rank_icon = get_rank_icon(player_rank)
        
        # Экранируем имя игрока
        safe_name = html.escape(player['character_name'])
        
        # Определяем медаль для первых трех мест
        medal = ""
        if i == 1:
            medal = "👑"
            top_text += f"{medal} *{i}. {safe_name}*\n"
        elif i == 2:
            medal = "🥈"
            top_text += f"{medal} *{i}. {safe_name}*\n"
        elif i == 3:
            medal = "🥉"
            top_text += f"{medal} *{i}. {safe_name}*\n"
        else:
            top_text += f"   *{i}. {safe_name}*\n"
        
        total_battles = player.get('battle_wins', 0) + player.get('battle_losses', 0)
        win_rate = 0
        if total_battles > 0:
            win_rate = (player.get('battle_wins', 0) / total_battles * 100)
        
        top_text += (
            f"   {rank_icon} {player_rank}-ранг | ⭐ Ур. {player['level']}\n"
            f"   ⚔️ {player.get('battle_wins', 0)}/{total_battles} побед ({win_rate:.1f}%)\n"
            f"   💰 {player.get('gold', 0)} золота\n"
        )
        
        if i < len(top_players):
            top_text += "   ─────────────────\n"
    
    # Добавляем информацию о позиции текущего игрока
    if player_position:
        top_text += f"\n📊 *Твоя позиция:* `#{player_position}`\n"
        
        if player_position > 10:
            top_text += f"_Ты не в топ-10, но у тебя есть потенциал!_ 💪\n"
        else:
            top_text += f"_Ты в числе лучших! Так держать!_ 🏆\n"
    
    top_text += "\n💡 *Как попасть в топ?*\n"
    top_text += "• Повышай уровень и ранг\n• Побеждай в боях\n• Накопай золота\n• Стань легендой!"
    
    await query.edit_message_text(
        text=top_text,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard(user_id)
    )

async def show_help(query):
    """Показ помощи"""
    help_text = """
📜 *ПУТЕВОДИТЕЛЬ ГЕРОЯ*

🕹 **Управление:**
Используй кнопки под сообщениями.

🏆 **Система рангов:**
Нажми на кнопку ранга в главном меню для подробной информации!

💪 **Способности рас и мана:**
• 👨 *Человек*: Адаптивность (10 маны) - временный буст всех характеристик
• 🧝 *Эльф*: Магический дар (20 маны) - мощный магический удар
• ⚒️ *Дварф*: Каменная кожа (15 маны) - лечение и защита
• 👹 *Орк*: Ярость (5 маны) - двойной удор с риском самоповреждения

🏚 **Места:**
• 👤 **Герой** - Твой статус и инвентарь
• 🎒 **Инвентарь** - Твои предметы (можно использовать зелья!)
• ⚔️ **Битва** - Охота на монстров в локациях по рангу
• 🛍 **Торговец** - Покупка зелий и снаряжения
• 🌟 **Прокачка** - Распределение характеристик
• 🏆 **Зал славы** - Твоя статистика и топ игроков
• 👑 **Топ игроков** - Рейтинг лучших охотников

📈 **Система прокачки:**
• За каждый уровень: *+3 очка характеристик*
• Распределяй между:
  💪 *СИЛА* - Урон в ближнем бою
  🏹 *ЛОВКОСТЬ* - Защита и уворот
  🧠 *ИНТЕЛЛЕКТ* - Магический урон и мана

🎒 **Инвентарь:**
• Нажми на кнопку 🎒 в главном меню
• Используй зелья для восстановления здоровья и маны
• Все купленные предметы хранятся здесь

💊 **Магазин:**
• Малое зелье здоровья (30 HP) - 25💰
• Большое зелье здоровья (60 HP) - 50💰
• Малое зелье маны (20 MP) - 20💰
• Большое зелье маны (40 MP) - 40💰
• Оружие и броня доступны по мере повышения ранга

🔄 **Регенерация:**
• Здоровье: 5% каждые 5 минут
• Мана: 10% каждые 5 минут

🗡 **Советы бывалых:**
1. _Создавай уникальный билд под свой стиль игры!_
2. Орки выигрывают от силы, эльфы — от интеллекта.
3. Не забывай про защиту — ловкость важна всем.
4. Используй зелья в тяжелых битвах!
5. Повышай ранг для доступа к новым локациям и снаряжению!

_Создай свою легенду!_ 🏹
"""
    await query.edit_message_text(
        text=help_text,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard(query.from_user.id)
    )

# --- ОБРАБОТЧИКИ БОЯ ---

async def battle_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик меню боя"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == 'back_to_main':
        if user_id in battle_sessions:
            del battle_sessions[user_id]
        
        await query.edit_message_text(
            text="🔙 Ты возвращаешься в безопасность деревни...",
            reply_markup=get_main_menu_keyboard(user_id),
            parse_mode='Markdown'
        )
        return MAIN_MENU
    
    elif data.startswith('location_'):
        location_rank = data[9:]
        await show_enemies_in_location(query, user_id, location_rank)
        return BATTLE_MENU
    
    elif data.startswith('battle_'):
        enemy_type = data[7:]
        await start_battle(query, user_id, enemy_type)
        return IN_BATTLE
    
    elif data == 'back_to_battle_menu':
        await show_battle_menu(query, user_id)
        return BATTLE_MENU

async def show_enemies_in_location(query, user_id, location_rank):
    """Показ врагов в выбранной локации"""
    character = get_character(user_id)
    location = LOCATIONS.get(location_rank)
    
    if not character or not location:
        await query.edit_message_text(
            text="❌ Ошибка загрузки локации!",
            reply_markup=get_main_menu_keyboard(user_id),
            parse_mode='Markdown'
        )
        return
    
    rank_icon = get_rank_icon(location_rank)
    
    # Показываем информацию о локации
    await query.message.reply_photo(
        photo=location['image'],
        caption=f"📍 *{location['name']}*\n{rank_icon} {location_rank}-ранг локация\n\n"
               f"📜 {location['description']}\n\n"
               f"⚔️ *Доступные враги:*",
        parse_mode='Markdown'
    )
    
    await query.message.reply_text(
        text="Выбери противника для боя:",
        reply_markup=get_location_enemies_keyboard(location_rank),
        parse_mode='Markdown'
    )

async def start_battle(query, user_id, enemy_type):
    """Начало боя с врагом"""
    character = get_character(user_id)
    
    if not character:
        await query.edit_message_text(
            text="❌ Герой потерян во времени!",
            reply_markup=get_main_menu_keyboard(user_id),
            parse_mode='Markdown'
        )
        return
    
    enemy = ENEMIES.get(enemy_type)
    
    if not enemy:
        await query.edit_message_text(
            text="❌ Враг не найден!",
            reply_markup=get_main_menu_keyboard(user_id),
            parse_mode='Markdown'
        )
        return
    
    # Проверяем, доступен ли враг для ранга игрока
    player_rank = character.get('rank', 'E')
    enemy_rank = enemy.get('rank', 'E')
    
    rank_order = ['E', 'D', 'C', 'B', 'A', 'S']
    player_rank_index = rank_order.index(player_rank)
    enemy_rank_index = rank_order.index(enemy_rank)
    
    # Игрок может сражаться с врагами своего ранга и на 1 ранг выше
    if enemy_rank_index > player_rank_index + 1:
        await query.answer(
            f"❌ Этот враг слишком силен для твоего {player_rank}-ранга!",
            show_alert=True
        )
        return
    
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
    
    enemy_rank_icon = get_rank_icon(enemy_rank)
    
    await query.message.reply_photo(
        photo=enemy['image'],
        caption=f"🔥 *БОЙ НАЧАЛСЯ!* 🔥\n━━━━━━━━━━━━━━━━\n"
               f"👿 Противник: *{enemy['name']}*\n"
               f"{enemy_rank_icon} *Ранг врага:* {enemy_rank}\n"
               f"📜 _{enemy['description']}_",
        parse_mode='Markdown'
    )
    
    battle_log = battle_sessions[user_id]['log']
    battle_log.append(f"🆚 *Статус:*")
    
    player_health_bar = get_health_bar(character['health'], character['max_health'], length=10)
    battle_log.append(f"👤 ГЕРОЙ: {player_health_bar}")
    
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
    """Обработчик действий в бою с учетом маны"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if user_id not in battle_sessions:
        await query.edit_message_text(
            text="❌ Бой уже завершен. Следы врага остыли.",
            reply_markup=get_main_menu_keyboard(user_id),
            parse_mode='Markdown'
        )
        return MAIN_MENU
    
    battle_data = battle_sessions[user_id]
    character = battle_data['character']
    enemy = battle_data['enemy']
    
    battle_data['log'] = []
    battle_data['turn'] += 1
    
    battle_log = battle_data['log']
    
    # Действие игрока - теперь с учетом характеристик
    if data == 'attack':
        # Урон зависит от силы
        base_damage = character['strength']
        player_damage = random.randint(base_damage // 2, base_damage)
        
        # Эффект ловкости: шанс на двойной удар
        agility_bonus = character['agility'] // 10  # Каждые 10 ловкости дают +1% шанс
        if random.randint(1, 100) <= (5 + agility_bonus):  # Базовый шанс 5% + бонус ловкости
            player_damage *= 2
            battle_log.append(f"⚡️ *КРИТИЧЕСКИЙ УДАР!* Ловкость помогла! Нанесено *{player_damage}* урона!")
        elif battle_data['enemy_defending']:
            player_damage = max(1, player_damage // 2)
            battle_log.append(f"🛡️ Враг в блоке! Ты нанес лишь *{player_damage}* урона.")
        else:
            battle_log.append(f"⚔️ Ты нанес *{player_damage}* урона!")
        
        enemy['health'] -= player_damage
        enemy['health'] = max(0, enemy['health'])  # Не даем здоровью уйти в минус
        
    elif data == 'defend':
        # Защита зависит от ловкости
        agility_bonus = min(character['agility'] // 5, 50)  # Максимум 50% бонуса
        battle_data['player_defending'] = True
        battle_log.append(f"🛡️ Ты поднял щит! Урон снижен на {50 + agility_bonus}%")
        
    elif data == 'ability':
        # Определяем стоимость маны для каждой расы
        mana_costs = {
            'human': 10,
            'elf': 20,
            'dwarf': 15,
            'orc': 5
        }
        
        mana_cost = mana_costs.get(character['race'], 10)
        
        # Проверяем, достаточно ли маны
        if character['mana'] < mana_cost:
            battle_log.append(f"❌ *НЕДОСТАТОЧНО МАНЫ!* Нужно {mana_cost} маны, а у тебя {character['mana']}.")
        else:
            # Отнимаем ману
            character['mana'] -= mana_cost
            
            if character['race'] == 'human':
                # Адаптивность: увеличение всех характеристик на основе интеллекта
                int_bonus = character['intelligence'] // 10
                battle_data['player_defending'] = True
                battle_log.append(f"✨ *Адаптивность!* Затрачено {mana_cost} маны. Все характеристики временно увеличены на *+{int_bonus}* и поднят щит!")
                
            elif character['race'] == 'elf':
                # Магический дар: урон зависит от интеллекта
                base_magic = character['intelligence']
                if random.random() < 0.3:  # 30% шанс
                    damage = base_magic * 2
                    battle_log.append(f"🏹 *КРИТИЧЕСКИЙ ВЫСТРЕЛ!* Затрачено {mana_cost} маны. Магия нанесла *{damage}* урона!")
                    enemy['health'] -= damage
                else:
                    damage = base_magic
                    battle_log.append(f"🏹 *Точный выстрел!* Затрачено {mana_cost} маны. Нанесено *{damage}* урона!")
                    enemy['health'] -= damage
                
            elif character['race'] == 'dwarf':
                # Каменная кожа: лечение зависит от здоровья
                heal_amount = character['max_health'] // 10 + random.randint(5, 15)
                character['health'] = min(character['max_health'], character['health'] + heal_amount)
                battle_data['player_defending'] = True
                battle_log.append(f"🏔 *Каменная кожа!* Затрачено {mana_cost} маны. Восстановлено *{heal_amount}* HP и поднят щит!")
                
            elif character['race'] == 'orc':
                # Ярость: урон зависит от силы
                damage = character['strength'] * 2 + random.randint(0, 5)
                self_damage = random.randint(1, 5)
                enemy['health'] -= damage
                character['health'] -= self_damage
                battle_log.append(f"🩸 *ЯРОСТЬ!* Затрачено {mana_cost} маны. Сокрушительный удар на *{damage}*, но ты ранил себя на *{self_damage}*.")
            
            battle_log.append(f"🔮 Осталось маны: {character['mana']}/{character['max_mana']}")
            
    elif data == 'flee':
        # Шанс сбежать зависит от ловкости
        agility_bonus = character['agility'] // 5  # Каждые 5 ловкости дают +1% шанс
        flee_chance = 50 + agility_bonus
        
        if random.randint(1, 100) <= flee_chance:
            battle_log.append("🏃💨 *ПОБЕГ УДАЛСЯ!* Ты растворился в тени...")
            del battle_sessions[user_id]
            await query.edit_message_text(
                text="\n".join(battle_log),
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return MAIN_MENU
        else:
            battle_log.append("🚫 *НЕУДАЧА!* Враг перекрыл путь к отступлению!")
    
    # Проверяем, не убит ли враг ДО его хода
    if enemy['health'] <= 0:
        battle_log.append("━━━━━━━━━━━━━━━━")
        battle_log.append("🏆 *ВЕЛИКАЯ ПОБЕДА!*")
        battle_log.append(f"Монстр {enemy['name']} повержен!")
        
        exp_gained = enemy['exp']
        gold_gained = enemy['gold']
        
        battle_log.append(f"💰 Трофеи: *{gold_gained}* золота")
        battle_log.append(f"🌟 Опыт: *{exp_gained}* XP")
        
        # Добавляем опыт и проверяем повышение уровня
        success, level_up, new_level, stat_points_gained = add_experience(user_id, exp_gained)
        
        if success and level_up:
            # Рассчитываем новый ранг
            new_rank = calculate_rank(new_level, character['experience'] + exp_gained)
            battle_log.append(f"🎯 *НОВЫЙ УРОВЕНЬ!* Ты достиг {new_level} уровня!")
            battle_log.append(f"✨ Получено *{stat_points_gained}* очков характеристик!")
            
            if new_rank != character.get('rank', 'E'):
                battle_log.append(f"🏆 *НОВЫЙ РАНГ!* Теперь ты {get_rank_icon(new_rank)} {new_rank}-ранг охотник!")
        
        update_character_stats(
            user_id, 
            health=character['health'],
            mana=character['mana'],
            battle_wins=character.get('battle_wins', 0) + 1,
            gold=character['gold'] + gold_gained
        )
        add_gold(user_id, gold_gained)
        log_battle(user_id, enemy['name'], 'победа', 0, 0, gold_gained, exp_gained)
        
        del battle_sessions[user_id]
        
        await query.edit_message_text(
            text="\n".join(battle_log),
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(user_id)
        )
        return MAIN_MENU
    
    # Если враг еще жив, он делает ход
    if enemy['health'] > 0:
        enemy_action = random.choice(['attack', 'attack', 'defend'])
        
        if enemy_action == 'attack':
            enemy_damage = random.randint(enemy['min_damage'], enemy['max_damage'])
            
            # Защита игрока снижает урон
            if battle_data['player_defending']:
                agility_bonus = min(character['agility'] // 5, 50)
                reduction = 50 + agility_bonus
                enemy_damage = max(1, enemy_damage * (100 - reduction) // 100)
                battle_log.append(f"🛡️ Твой блок поглотил {reduction}% урона! Получено *{enemy_damage}* ед.")
            else:
                battle_log.append(f"💔 Враг атаковал тебя на *{enemy_damage}* урона!")
            
            character['health'] -= enemy_damage
            character['health'] = max(0, character['health'])  # Не даем здоровью уйти в минус
            battle_data['player_defending'] = False
        else:
            battle_data['enemy_defending'] = True
            battle_log.append(f"🛡️ Враг ушел в глухую оборону!")
    
    battle_data['enemy_defending'] = False
    
    # Проверка окончания боя (игрок погиб)
    if character['health'] <= 0:
        battle_log.append("━━━━━━━━━━━━━━━━")
        battle_log.append("💀 *ТЫ ПАЛ В БОЮ...*")
        battle_log.append("Твоя история прервалась на этом месте.")
        
        update_character_stats(user_id, 
            health=0,
            mana=character['mana'],
            battle_losses=character.get('battle_losses', 0) + 1
        )
        log_battle(user_id, enemy['name'], 'поражение', 0, 0, 0, 0)
        
        del battle_sessions[user_id]
        
        await query.edit_message_text(
            text="\n".join(battle_log),
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(user_id)
        )
        return MAIN_MENU
    
    # Продолжение боя (оба живы)
    player_health_bar = get_health_bar(max(0, character['health']), character['max_health'], length=10)
    enemy_health_bar = get_health_bar(max(0, enemy['health']), enemy['max_health'], length=10)
    player_mana_bar = get_mana_bar(max(0, character['mana']), character['max_mana'], length=8)
    
    status_text = (
        f"⚔️ *Ход №{battle_data['turn']}*\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"👤 *ТЫ:* {player_health_bar}\n"
        f"🔮 *МАНА:* {player_mana_bar}\n"
        f"👿 *ВРАГ:* {enemy_health_bar}\n\n"
        f"{chr(10).join(battle_log)}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"⚡️ *Твои действия:*"
    )
    
    await query.edit_message_text(
        text=status_text,
        parse_mode='Markdown',
        reply_markup=get_battle_action_keyboard()
    )
    return IN_BATTLE

# --- ОСНОВНАЯ ФУНКЦИЯ ---

def main():
    """Запуск бота"""
    print("🚀 Запуск RPG бота с системой рангов, локаций и инвентарем...")
    
    if not TOKEN:
        print("❌ ОШИБКА: TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        print("Добавьте переменную TELEGRAM_BOT_TOKEN в Railway")
        return
    
    print(f"✅ Токен найден, длина: {len(TOKEN)} символов")
    
    print("🔄 Инициализация базы данных...")
    try:
        init_db()
        print("✅ База данных инициализирована")
    except Exception as e:
        print(f"⚠️ Предупреждение: не удалось инициализировать БД: {e}")
    
    try:
        application = Application.builder().token(TOKEN).build()
        
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
                    CallbackQueryHandler(battle_menu_handler, pattern='^(location_|battle_|back_to_main|back_to_battle_menu)')
                ],
                IN_BATTLE: [
                    CallbackQueryHandler(battle_action_handler, pattern='^(attack|defend|ability|flee)$')
                ],
                SHOP_MENU: [
                    CallbackQueryHandler(shop_handler)
                ],
                LEVEL_UP: [
                    CallbackQueryHandler(level_up_handler, pattern='^(levelup_|back_to_main|info_only)')
                ],
                INVENTORY_MENU: [
                    CallbackQueryHandler(inventory_menu_handler)
                ]
            },
            fallbacks=[CommandHandler('cancel', cancel)],
            allow_reentry=True
        )
        
        application.add_handler(conv_handler)
        application.add_handler(CommandHandler('help', help_command))
        
        print("🤖 RPG бот запущен!")
        print("📱 Перейдите в Telegram и напишите /start")
        
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
