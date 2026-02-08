import os
import logging
import random
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
import psycopg2
from psycopg2.extras import RealDictCursor

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

# Константы для database.py - УСЛОЖНЕННЫЕ ЗНАЧЕНИЯ
RACES = {
    "human": {
        "name": "Человек",
        "strength": 8,
        "agility": 8,
        "intelligence": 8,
        "vitality": 8,
        "health_multiplier": 8,
        "mana_multiplier": 3,
        "racial_ability": "Адаптивность: +5% ко всем характеристикам на 1 ход"
    },
    "elf": {
        "name": "Эльф",
        "strength": 6,
        "agility": 12,
        "intelligence": 10,
        "vitality": 6,
        "health_multiplier": 6,
        "mana_multiplier": 6,
        "racial_ability": "Магический дар: +30% к мане, точные выстрелы"
    },
    "dwarf": {
        "name": "Дварф",
        "strength": 11,
        "agility": 5,
        "intelligence": 7,
        "vitality": 10,
        "health_multiplier": 10,
        "mana_multiplier": 2,
        "racial_ability": "Каменная кожа: +15% к здоровью, сопротивление к магии"
    },
    "orc": {
        "name": "Орк",
        "strength": 13,
        "agility": 7,
        "intelligence": 5,
        "vitality": 9,
        "health_multiplier": 9,
        "mana_multiplier": 1.5,
        "racial_ability": "Ярость: +50% урон при низком здоровье"
    }
}

# Ссылки на изображения
IMAGE_URLS = {
    'human': 'https://i126.fastpic.org/thumb/2026/0130/2c/_d2515d33e45fa7ffb5246cacabdaba2c.jpeg',
    'elf': 'https://i126.fastpic.org/thumb/2026/0130/81/_d3d94be5aa45b9239aeb5adc41443081.jpeg',
    'dwarf': 'https://i126.fastpic.org/thumb/2026/0130/5b/_c188fac4eb6d205bd9fc0486c9b9355b.jpeg',
    'orc': 'https://i126.fastpic.org/thumb/2026/0130/20/_b8c1f666bd21bb415e8fb35145eb3e20.jpeg',
    'wolf': 'https://i.pinimg.com/736x/9f/8e/25/9f8e2507aceaa217060d249c308e2a13.jpg',
    'goblin': 'https://img.freepik.com/free-photo/goblin-digital-art_23-2151061965.jpg',
    'slime': 'https://papik.pro/uploads/posts/2023-02/1676176492_papik-pro-p-risunok-sliz-1.jpg',
    'zombie': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQRBEAcmeuf4tt0xnFUG1E8wcvZlSkLQcZkUw&s',
    'skeleton': 'https://img.freepik.com/free-photo/skeleton-warrior_23-2150911306.jpg',
    'mage': 'https://abrakadabra.fun/uploads/posts/2022-01/1642490542_3-abrakadabra-fun-p-temnii-mag-art-5.jpg',
    'vampire': 'https://img.freepik.com/free-photo/vampire_23-2150762308.jpg',
    'knight': 'https://img.freepik.com/free-photo/dark-knight_23-2150762270.jpg',
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
    'training_camp': 'https://img.freepik.com/free-photo/medieval-camp-with-tents-night_107791-16981.jpg',
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
        'base_max_physical_damage': 11,
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
        'base_max_physical_damage': 13,
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
        'base_health': 50,
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
        'image': IMAGE_URLS['goblin'],
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
    
    # D-ранг враги
    'forest_spider': {
        'name': '🕷️ Лесной Паук',
        'base_health': 65,
        'base_min_physical_damage': 8,
        'base_max_physical_damage': 16,
        'base_min_magic_damage': 0,
        'base_max_magic_damage': 0,
        'base_exp': 25,
        'base_gold': 16,
        'rank': 'D',
        'description': 'Огромный паук, плетущий смертельные сети.',
        'image': 'https://img.freepik.com/free-photo/giant-spider_23-2150911307.jpg',
        'difficulty': 'medium',
        'abilities': ['basic_attack', 'web_shot', 'poison_bite'],
        'damage_type': 'physical',
        'dodge_chance': 0.15,
        'physical_resistance': 0.15,
        'magic_resistance': 0.05,
        'special_chance': 0.25,
        'web_chance': 0.30,
        'attack_range': 'melee'
    },
    'ghost': {
        'name': '👻 Призрак',
        'base_health': 55,
        'base_min_physical_damage': 7,
        'base_max_physical_damage': 14,
        'base_min_magic_damage': 4,
        'base_max_magic_damage': 9,
        'base_exp': 28,
        'base_gold': 20,
        'rank': 'D',
        'description': 'Бесформенный дух, способный проходить сквозь стены.',
        'image': 'https://img.freepik.com/free-photo/ghost_23-2150762306.jpg',
        'difficulty': 'medium',
        'abilities': ['basic_attack', 'fear', 'phase_through'],
        'damage_type': 'magic',
        'dodge_chance': 0.25,
        'physical_resistance': 0.60,
        'magic_resistance': 0.25,
        'special_chance': 0.30,
        'attack_range': 'ranged'
    },
    'wild_boar': {
        'name': '🐗 Дикий Кабан',
        'base_health': 85,
        'base_min_physical_damage': 10,
        'base_max_physical_damage': 20,
        'base_min_magic_damage': 0,
        'base_max_magic_damage': 0,
        'base_exp': 32,
        'base_gold': 24,
        'rank': 'D',
        'description': 'Массивное животное с острыми клыками.',
        'image': 'https://img.freepik.com/free-photo/wild-boar_23-2150911295.jpg',
        'difficulty': 'medium',
        'abilities': ['basic_attack', 'charge', 'tusks'],
        'damage_type': 'physical',
        'dodge_chance': 0.08,
        'physical_resistance': 0.30,
        'magic_resistance': 0.05,
        'special_chance': 0.25,
        'charge_chance': 0.35,
        'attack_range': 'melee'
    },
    'forest_troll': {
        'name': '🌳 Лесной тролль',
        'base_health': 110,
        'base_min_physical_damage': 15,
        'base_max_physical_damage': 23,
        'base_min_magic_damage': 0,
        'base_max_magic_damage': 0,
        'base_exp': 48,
        'base_gold': 36,
        'rank': 'D',
        'description': 'Мощное лесное существо с регенерацией.',
        'image': 'https://img.freepik.com/free-photo/troll_23-2150911292.jpg',
        'difficulty': 'mini_boss',
        'abilities': ['basic_attack', 'regeneration', 'club_smash'],
        'damage_type': 'physical',
        'dodge_chance': 0.12,
        'physical_resistance': 0.35,
        'magic_resistance': 0.15,
        'special_chance': 0.35,
        'mini_boss_bonus': 1.9,
        'attack_range': 'melee'
    },
    'forest_guardian': {
        'name': '🌳 Хранитель Леса',
        'base_health': 150,
        'base_min_physical_damage': 13,
        'base_max_physical_damage': 25,
        'base_min_magic_damage': 7,
        'base_max_magic_damage': 13,
        'base_exp': 80,
        'base_gold': 64,
        'rank': 'D',
        'description': 'Древнее дерево, пробужденное магией леса.',
        'image': 'https://img.freepik.com/free-photo/treant_23-2150911290.jpg',
        'difficulty': 'boss',
        'abilities': ['basic_attack', 'root_grab', 'healing_leaves', 'forest_rage'],
        'damage_type': 'mixed',
        'dodge_chance': 0.08,
        'physical_resistance': 0.45,
        'magic_resistance': 0.35,
        'special_chance': 0.40,
        'boss_bonus': 2.7,
        'heal_chance': 0.25,
        'attack_range': 'mixed'
    },
    
    # C-ранг враги
    'skeleton_warrior': {
        'name': '💀 Скелет-воин',
        'base_health': 100,
        'base_min_physical_damage': 13,
        'base_max_physical_damage': 23,
        'base_min_magic_damage': 0,
        'base_max_magic_damage': 0,
        'base_exp': 48,
        'base_gold': 32,
        'rank': 'C',
        'description': 'Оживленные кости с ржавым мечом и щитом.',
        'image': IMAGE_URLS['skeleton'],
        'difficulty': 'hard',
        'abilities': ['basic_attack', 'shield_bash', 'bone_armor'],
        'damage_type': 'physical',
        'dodge_chance': 0.12,
        'physical_resistance': 0.35,
        'magic_resistance': 0.15,
        'special_chance': 0.30,
        'block_chance': 0.35,
        'attack_range': 'melee'
    },
    'ghoul': {
        'name': '🧟 Гуль',
        'base_health': 115,
        'base_min_physical_damage': 12,
        'base_max_physical_damage': 22,
        'base_min_magic_damage': 0,
        'base_max_magic_damage': 0,
        'base_exp': 52,
        'base_gold': 36,
        'rank': 'C',
        'description': 'Ненасытная нежить, питающаяся плотью.',
        'image': IMAGE_URLS['zombie'],
        'difficulty': 'hard',
        'abilities': ['basic_attack', 'life_drain', 'frenzy'],
        'damage_type': 'physical',
        'dodge_chance': 0.10,
        'physical_resistance': 0.25,
        'magic_resistance': 0.05,
        'special_chance': 0.35,
        'drain_chance': 0.30,
        'attack_range': 'melee'
    },
    'dark_priest': {
        'name': '🕯️ Темный Жрец',
        'base_health': 90,
        'base_min_physical_damage': 7,
        'base_max_physical_damage': 13,
        'base_min_magic_damage': 15,
        'base_max_magic_damage': 28,
        'base_exp': 60,
        'base_gold': 44,
        'rank': 'C',
        'description': 'Служитель темных богов, владеющий запретной магией.',
        'image': IMAGE_URLS['mage'],
        'difficulty': 'hard',
        'abilities': ['basic_attack', 'dark_bolt', 'curse', 'sacrifice'],
        'damage_type': 'magic',
        'dodge_chance': 0.15,
        'physical_resistance': 0.15,
        'magic_resistance': 0.30,
        'special_chance': 0.40,
        'spell_chance': 0.45,
        'attack_range': 'ranged'
    },
    'crypt_keeper': {
        'name': '💀 Хранитель склепа',
        'base_health': 140,
        'base_min_physical_damage': 15,
        'base_max_physical_damage': 25,
        'base_min_magic_damage': 10,
        'base_max_magic_damage': 19,
        'base_exp': 72,
        'base_gold': 56,
        'rank': 'C',
        'description': 'Древний некромант, охраняющий катакомбы.',
        'image': 'https://img.freepik.com/free-photo/necromancer_23-2150911284.jpg',
        'difficulty': 'mini_boss',
        'abilities': ['basic_attack', 'raise_dead', 'death_bolt', 'bone_shield'],
        'damage_type': 'mixed',
        'dodge_chance': 0.18,
        'physical_resistance': 0.25,
        'magic_resistance': 0.40,
        'special_chance': 0.40,
        'mini_boss_bonus': 2.0,
        'attack_range': 'ranged'
    },
    'catacomb_lord': {
        'name': '👑 Повелитель Катакомб',
        'base_health': 225,
        'base_min_physical_damage': 19,
        'base_max_physical_damage': 32,
        'base_min_magic_damage': 13,
        'base_max_magic_damage': 23,
        'base_exp': 160,
        'base_gold': 120,
        'rank': 'C',
        'description': 'Древний король, проклятый вечно охранять свои владения.',
        'image': 'https://img.freepik.com/free-photo/skeleton-king_23-2150911291.jpg',
        'difficulty': 'boss',
        'abilities': ['basic_attack', 'royal_decree', 'summon_skeletons', 'kings_wrath'],
        'damage_type': 'mixed',
        'dodge_chance': 0.15,
        'physical_resistance': 0.40,
        'magic_resistance': 0.30,
        'special_chance': 0.45,
        'boss_bonus': 3.0,
        'summon_chance': 0.35,
        'attack_range': 'mixed'
    },
    
    # B-ранг враги
    'knight': {
        'name': '⚔️ Проклятый рыцарь',
        'base_health': 150,
        'base_min_physical_damage': 19,
        'base_max_physical_damage': 32,
        'base_min_magic_damage': 0,
        'base_max_magic_damage': 0,
        'base_exp': 80,
        'base_gold': 64,
        'rank': 'B',
        'description': 'Броня сияет темной энергией, а меч жаждет крови.',
        'image': IMAGE_URLS['knight'],
        'difficulty': 'very_hard',
        'abilities': ['basic_attack', 'shield_wall', 'vengeful_strike', 'dark_aura'],
        'damage_type': 'physical',
        'dodge_chance': 0.20,
        'physical_resistance': 0.45,
        'magic_resistance': 0.25,
        'special_chance': 0.35,
        'defense_bonus': 0.45,
        'attack_range': 'melee'
    },
    'vampire': {
        'name': '🦇 Молодой вампир',
        'base_health': 125,
        'base_min_physical_damage': 23,
        'base_max_physical_damage': 35,
        'base_min_magic_damage': 0,
        'base_max_magic_damage': 0,
        'base_exp': 96,
        'base_gold': 80,
        'rank': 'B',
        'description': 'Аристократ ночи, пьющий кровь жертв.',
        'image': IMAGE_URLS['vampire'],
        'difficulty': 'very_hard',
        'abilities': ['basic_attack', 'blood_drain', 'bat_swarm', 'hypnosis'],
        'damage_type': 'physical',
        'dodge_chance': 0.25,
        'physical_resistance': 0.30,
        'magic_resistance': 0.20,
        'special_chance': 0.40,
        'heal_from_damage': 0.35,
        'attack_range': 'melee'
    },
    'warlock': {
        'name': '🔮 Чернокнижник',
        'base_health': 115,
        'base_min_physical_damage': 7,
        'base_max_physical_damage': 13,
        'base_min_magic_damage': 25,
        'base_max_magic_damage': 40,
        'base_exp': 104,
        'base_gold': 88,
        'rank': 'B',
        'description': 'Маг, заключивший договор с демонами.',
        'image': IMAGE_URLS['mage'],
        'difficulty': 'very_hard',
        'abilities': ['basic_attack', 'shadow_bolt', 'demon_summon', 'soul_burn'],
        'damage_type': 'magic',
        'dodge_chance': 0.18,
        'physical_resistance': 0.15,
        'magic_resistance': 0.45,
        'special_chance': 0.45,
        'summon_chance': 0.30,
        'attack_range': 'ranged'
    },
    'death_knight': {
        'name': '💀 Рыцарь смерти',
        'base_health': 190,
        'base_min_physical_damage': 25,
        'base_max_physical_damage': 38,
        'base_min_magic_damage': 13,
        'base_max_magic_damage': 23,
        'base_exp': 144,
        'base_gold': 112,
        'rank': 'B',
        'description': 'Бывший паладин, павший во тьму и получивший нежить.',
        'image': 'https://img.freepik.com/free-photo/death-knight_23-2150911264.jpg',
        'difficulty': 'mini_boss',
        'abilities': ['basic_attack', 'death_coil', 'anti_magic_shell', 'army_of_the_dead'],
        'damage_type': 'mixed',
        'dodge_chance': 0.23,
        'physical_resistance': 0.50,
        'magic_resistance': 0.40,
        'special_chance': 0.45,
        'mini_boss_bonus': 2.1,
        'attack_range': 'melee'
    },
    'castle_overlord': {
        'name': '🏰 Владыка Замка',
        'base_health': 315,
        'base_min_physical_damage': 25,
        'base_max_physical_damage': 44,
        'base_min_magic_damage': 19,
        'base_max_magic_damage': 32,
        'base_exp': 280,
        'base_gold': 200,
        'rank': 'B',
        'description': 'Бывший король, павший во тьму и превративший свой замок в обитель зла.',
        'image': 'https://img.freepik.com/free-photo/dark-king_23-2150911261.jpg',
        'difficulty': 'boss',
        'abilities': ['basic_attack', 'royal_command', 'castle_defense', 'tyrants_wrath'],
        'damage_type': 'mixed',
        'dodge_chance': 0.20,
        'physical_resistance': 0.55,
        'magic_resistance': 0.35,
        'special_chance': 0.50,
        'boss_bonus': 3.3,
        'defense_bonus': 0.55,
        'attack_range': 'mixed'
    },
    
    # A-ранг враги
    'demon': {
        'name': '😈 Младший демон',
        'base_health': 190,
        'base_min_physical_damage': 32,
        'base_max_physical_damage': 50,
        'base_min_magic_damage': 13,
        'base_max_magic_damage': 25,
        'base_exp': 160,
        'base_gold': 120,
        'rank': 'A',
        'description': 'Призван из бездны, жаждет разрушения.',
        'image': IMAGE_URLS['demon'],
        'difficulty': 'extreme',
        'abilities': ['basic_attack', 'hellfire', 'demonic_claws', 'fear_aura'],
        'damage_type': 'mixed',
        'dodge_chance': 0.25,
        'physical_resistance': 0.35,
        'magic_resistance': 0.45,
        'special_chance': 0.40,
        'fire_chance': 0.35,
        'attack_range': 'mixed'
    },
    'hellhound': {
        'name': '🔥 Адская Гончая',
        'base_health': 225,
        'base_min_physical_damage': 28,
        'base_max_physical_damage': 48,
        'base_min_magic_damage': 7,
        'base_max_magic_damage': 13,
        'base_exp': 144,
        'base_gold': 112,
        'rank': 'A',
        'description': 'Пес из преисподней с горящей шерстью.',
        'image': 'https://img.freepik.com/free-photo/hellhound_23-2150911276.jpg',
        'difficulty': 'extreme',
        'abilities': ['basic_attack', 'fire_breath', 'pack_hunt', 'hellish_howl'],
        'damage_type': 'mixed',
        'dodge_chance': 0.30,
        'physical_resistance': 0.30,
        'magic_resistance': 0.40,
        'special_chance': 0.35,
        'burn_chance': 0.30,
        'attack_range': 'melee'
    },
    'infernal_mage': {
        'name': '🔥 Инфернальный Маг',
        'base_health': 165,
        'base_min_physical_damage': 13,
        'base_max_physical_damage': 23,
        'base_min_magic_damage': 35,
        'base_max_magic_damage': 56,
        'base_exp': 176,
        'base_gold': 136,
        'rank': 'A',
        'description': 'Мастер огненной и демонической магии.',
        'image': 'https://img.freepik.com/free-photo/fire-mage_23-2150911269.jpg',
        'difficulty': 'extreme',
        'abilities': ['basic_attack', 'meteor_shower', 'demonic_gate', 'inferno'],
        'damage_type': 'magic',
        'dodge_chance': 0.20,
        'physical_resistance': 0.20,
        'magic_resistance': 0.55,
        'special_chance': 0.45,
        'aoe_chance': 0.40,
        'attack_range': 'ranged'
    },
    'pit_fiend': {
        'name': '😈 Повелитель бездны',
        'base_health': 275,
        'base_min_physical_damage': 35,
        'base_max_physical_damage': 53,
        'base_min_magic_damage': 25,
        'base_max_magic_damage': 40,
        'base_exp': 240,
        'base_gold': 176,
        'rank': 'A',
        'description': 'Высший демон, командующий легионами преисподней.',
        'image': 'https://img.freepik.com/free-photo/pit-fiend_23-2150911286.jpg',
        'difficulty': 'mini_boss',
        'abilities': ['basic_attack', 'summon_demons', 'infernal_rage', 'dimensional_rip'],
        'damage_type': 'mixed',
        'dodge_chance': 0.28,
        'physical_resistance': 0.45,
        'magic_resistance': 0.50,
        'special_chance': 0.50,
        'mini_boss_bonus': 2.2,
        'attack_range': 'mixed'
    },
    'demon_general': {
        'name': '😈 Генерал Преисподней',
        'base_health': 440,
        'base_min_physical_damage': 38,
        'base_max_physical_damage': 63,
        'base_min_magic_damage': 32,
        'base_max_magic_damage': 50,
        'base_exp': 400,
        'base_gold': 280,
        'rank': 'A',
        'description': 'Командующий армиями ада. Его появление предвещает конец света.',
        'image': 'https://img.freepik.com/free-photo/demon-general_23-2150911263.jpg',
        'difficulty': 'boss',
        'abilities': ['basic_attack', 'army_command', 'apocalypse', 'final_judgment'],
        'damage_type': 'mixed',
        'dodge_chance': 0.25,
        'physical_resistance': 0.50,
        'magic_resistance': 0.45,
        'special_chance': 0.55,
        'boss_bonus': 3.5,
        'army_bonus': 1.6,
        'attack_range': 'mixed'
    },
    
    # S-ранг враги
    'dragon_ancient': {
        'name': '🐉 Древний Дракон',
        'base_health': 500,
        'base_min_physical_damage': 44,
        'base_max_physical_damage': 69,
        'base_min_magic_damage': 32,
        'base_max_magic_damage': 50,
        'base_exp': 480,
        'base_gold': 320,
        'rank': 'S',
        'description': 'Владыка небес. Его пламя сжигает все живое.',
        'image': IMAGE_URLS['dragon_ancient'],
        'difficulty': 'legendary',
        'abilities': ['basic_attack', 'dragon_breath', 'wing_gust', 'ancient_roar'],
        'damage_type': 'mixed',
        'dodge_chance': 0.30,
        'physical_resistance': 0.55,
        'magic_resistance': 0.55,
        'special_chance': 0.45,
        'breath_chance': 0.40,
        'attack_range': 'mixed'
    },
    'titan': {
        'name': '🏔️ Титан',
        'base_health': 625,
        'base_min_physical_damage': 50,
        'base_max_physical_damage': 75,
        'base_min_magic_damage': 19,
        'base_max_magic_damage': 32,
        'base_exp': 560,
        'base_gold': 360,
        'rank': 'S',
        'description': 'Ходячая гора из плоти и камня.',
        'image': IMAGE_URLS['titan'],
        'difficulty': 'legendary',
        'abilities': ['basic_attack', 'earthquake', 'mountain_slam', 'titanic_rage'],
        'damage_type': 'physical',
        'dodge_chance': 0.15,
        'physical_resistance': 0.65,
        'magic_resistance': 0.35,
        'special_chance': 0.40,
        'stun_chance': 0.35,
        'attack_range': 'melee'
    },
    'fallen_angel': {
        'name': '😇 Падший Ангел',
        'base_health': 565,
        'base_min_physical_damage': 48,
        'base_max_physical_damage': 73,
        'base_min_magic_damage': 38,
        'base_max_magic_damage': 56,
        'base_exp': 520,
        'base_gold': 336,
        'rank': 'S',
        'description': 'Бывший слуга небес, изгнанный за гордыню.',
        'image': 'https://img.freepik.com/free-photo/fallen-angel_23-2150911260.jpg',
        'difficulty': 'legendary',
        'abilities': ['basic_attack', 'heavenly_light', 'fallen_wings', 'judgment_sword'],
        'damage_type': 'mixed',
        'dodge_chance': 0.35,
        'physical_resistance': 0.45,
        'magic_resistance': 0.65,
        'special_chance': 0.50,
        'heal_chance': 0.30,
        'attack_range': 'mixed'
    },
    'archangel': {
        'name': '😇 Архангел',
        'base_health': 475,
        'base_min_physical_damage': 40,
        'base_max_physical_damage': 60,
        'base_min_magic_damage': 44,
        'base_max_magic_damage': 65,
        'base_exp': 440,
        'base_gold': 304,
        'rank': 'S',
        'description': 'Верховный ангел, защитник небесного трона.',
        'image': 'https://img.freepik.com/free-photo/archangel_23-2150911259.jpg',
        'difficulty': 'mini_boss',
        'abilities': ['basic_attack', 'divine_smite', 'angelic_shield', 'holy_aura'],
        'damage_type': 'mixed',
        'dodge_chance': 0.40,
        'physical_resistance': 0.40,
        'magic_resistance': 0.60,
        'special_chance': 0.55,
        'mini_boss_bonus': 2.3,
        'attack_range': 'mixed'
    },
    'final_god': {
        'name': '⚡ Верховный Бог',
        'base_health': 1250,
        'base_min_physical_damage': 63,
        'base_max_physical_damage': 100,
        'base_min_magic_damage': 50,
        'base_max_magic_damage': 88,
        'base_exp': 1200,
        'base_gold': 800,
        'rank': 'S',
        'description': 'Верховное божество этого мира. Победа над ним сделает тебя легендой.',
        'image': IMAGE_URLS['fallen_god'],
        'difficulty': 'boss',
        'abilities': ['basic_attack', 'divine_judgment', 'creation', 'annihilation', 'omnipotence'],
        'damage_type': 'mixed',
        'dodge_chance': 0.45,
        'physical_resistance': 0.65,
        'magic_resistance': 0.65,
        'special_chance': 0.65,
        'boss_bonus': 4.5,
        'god_powers': True,
        'attack_range': 'mixed'
    }
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

# --- ФУНКЦИИ ДЛЯ РАБОТЫ С БАЗОЙ ДАННЫХ ---

def get_connection():
    """Создание подключения к PostgreSQL"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        # Для локальной разработки
        db_host = os.getenv('PGHOST', 'localhost')
        db_port = os.getenv('PGPORT', '5432')
        db_name = os.getenv('PGDATABASE', 'railway')
        db_user = os.getenv('PGUSER', 'postgres')
        db_password = os.getenv('PGPASSWORD', '')
        database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    try:
        conn = psycopg2.connect(database_url, sslmode='require')
        return conn
    except Exception as e:
        print(f"❌ Ошибка подключения с sslmode=require: {e}")
        # Пробуем подключиться без sslmode
        try:
            conn = psycopg2.connect(database_url)
            return conn
        except Exception as e2:
            print(f"❌ Не удалось подключиться к БД: {e2}")
            return None

def init_db():
    """Инициализация таблиц в базе данных"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            print("❌ Не удалось подключиться к БД для инициализации")
            return
        
        cursor = conn.cursor()
        
        # Создаем таблицу, если она не существует
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_characters (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL UNIQUE,
                character_name VARCHAR(100) NOT NULL,
                race VARCHAR(50) NOT NULL,
                level INTEGER DEFAULT 1,
                experience INTEGER DEFAULT 0,
                rank VARCHAR(10) DEFAULT 'E',
                strength INTEGER DEFAULT 8,
                agility INTEGER DEFAULT 8,
                intelligence INTEGER DEFAULT 8,
                vitality INTEGER DEFAULT 8,
                health INTEGER DEFAULT 64,
                max_health INTEGER DEFAULT 64,
                mana INTEGER DEFAULT 24,
                max_mana INTEGER DEFAULT 24,
                gold INTEGER DEFAULT 50,
                stat_points INTEGER DEFAULT 2,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_regeneration TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                battle_wins INTEGER DEFAULT 0,
                battle_losses INTEGER DEFAULT 0,
                boss_kills INTEGER DEFAULT 0,
                mini_boss_kills INTEGER DEFAULT 0,
                physical_resistance DECIMAL DEFAULT 0.0,
                magic_resistance DECIMAL DEFAULT 0.0
            )
        """)
        
        # Проверяем, есть ли столбец vitality, если нет - добавляем
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='player_characters' and column_name='vitality'
        """)
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE player_characters ADD COLUMN vitality INTEGER DEFAULT 8")
            print("✅ Столбец 'vitality' добавлен в таблицу 'player_characters'")
        
        # Проверяем, есть ли столбец mini_boss_kills, если нет - добавляем
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='player_characters' and column_name='mini_boss_kills'
        """)
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE player_characters ADD COLUMN mini_boss_kills INTEGER DEFAULT 0")
            print("✅ Столбец 'mini_boss_kills' добавлен в таблицу 'player_characters'")
        
        # Проверяем, есть ли столбцы сопротивлений, если нет - добавляем
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='player_characters' and column_name='physical_resistance'
        """)
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE player_characters ADD COLUMN physical_resistance DECIMAL DEFAULT 0.0")
            cursor.execute("ALTER TABLE player_characters ADD COLUMN magic_resistance DECIMAL DEFAULT 0.0")
            print("✅ Столбцы сопротивлений добавлены в таблицу 'player_characters'")
        
        print("✅ Таблица 'player_characters' создана/обновлена")
        
        # Создаем таблицу для логов боев
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS battle_logs (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                enemy_type VARCHAR(100),
                enemy_name VARCHAR(100),
                result VARCHAR(50),
                damage_dealt INTEGER DEFAULT 0,
                damage_taken INTEGER DEFAULT 0,
                gold_earned INTEGER DEFAULT 0,
                experience_earned INTEGER DEFAULT 0,
                is_boss BOOLEAN DEFAULT FALSE,
                is_mini_boss BOOLEAN DEFAULT FALSE,
                battle_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Создаем таблицу инвентаря
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_inventory (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                item_key VARCHAR(100) NOT NULL,
                item_type VARCHAR(50) NOT NULL,
                item_name VARCHAR(100) NOT NULL,
                quantity INTEGER DEFAULT 1,
                effect_amount INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Создаем индексы для быстрого поиска
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_player_inventory_user_item 
            ON player_inventory (user_id, item_key)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_player_inventory_user 
            ON player_inventory (user_id)
        """)
        
        conn.commit()
        print("✅ База данных инициализирована")
        
    except Exception as e:
        print(f"❌ Ошибка при создании таблиц: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def create_character(user_id, username, character_name, race):
    """Создание нового персонажа - УСЛОЖНЕННЫЙ ВАРИАНТ"""
    conn = None
    cursor = None
    try:
        # Проверяем, что раса существует
        if race not in RACES:
            return False, "Неизвестная раса"
        
        race_data = RACES[race]
        
        # Рассчитываем начальные характеристики на основе расы
        strength = race_data['strength']
        agility = race_data['agility']
        intelligence = race_data['intelligence']
        vitality = race_data['vitality']
        
        # Рассчитываем здоровье и ману
        health = vitality * race_data['health_multiplier']
        mana = intelligence * race_data['mana_multiplier']
        
        # Рассчитываем начальные сопротивления на основе расы
        physical_resistance = 0.0
        magic_resistance = 0.0
        
        if race == 'dwarf':
            magic_resistance = 0.15  # Было 0.2
        elif race == 'elf':
            physical_resistance = 0.08  # Было 0.1
        
        conn = get_connection()
        if not conn:
            return False, "Не удалось подключиться к базе данных"
        
        cursor = conn.cursor()
        
        # Проверяем, есть ли уже персонаж у пользователя
        cursor.execute("SELECT id FROM player_characters WHERE user_id = %s", (user_id,))
        if cursor.fetchone():
            return False, "У вас уже есть персонаж!"
        
        # Создаем персонажа с характеристиками расы - МЕНЬШЕ РЕСУРСОВ
        cursor.execute("""
            INSERT INTO player_characters 
            (user_id, character_name, race, level, experience, rank,
             strength, agility, intelligence, vitality, health, max_health, 
             mana, max_mana, gold, stat_points, physical_resistance, magic_resistance)
            VALUES (%s, %s, %s, 1, 0, 'E', %s, %s, %s, %s, %s, %s, %s, %s, 50, 2, %s, %s)
        """, (
            user_id, character_name, race,
            strength, agility, intelligence, vitality,
            health, health, mana, mana,
            physical_resistance, magic_resistance
        ))
        
        conn.commit()
        print(f"✅ Персонаж создан для user_id: {user_id}")
        return True, "Персонаж успешно создан!"
        
    except Exception as e:
        print(f"❌ Ошибка при создании персонажа: {e}")
        if conn:
            conn.rollback()
        return False, f"Ошибка при создании персонажа: {e}"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_character(user_id):
    """Получение информации о персонаже"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            print("❌ Не удалось подключиться к БД для получения персонажа")
            return None
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT * FROM player_characters 
            WHERE user_id = %s
        """, (user_id,))
        
        character = cursor.fetchone()
        
        if character:
            # Обновляем время последней активности
            cursor.execute("""
                UPDATE player_characters 
                SET last_active = CURRENT_TIMESTAMP 
                WHERE user_id = %s
            """, (user_id,))
            
            # Если ранг не установлен, рассчитываем его
            if not character.get('rank'):
                from database import calculate_rank
                rank = calculate_rank(character['level'], character['experience'])
                cursor.execute("""
                    UPDATE player_characters 
                    SET rank = %s
                    WHERE user_id = %s
                """, (rank, user_id))
                character['rank'] = rank
            
            conn.commit()
        
        return character
        
    except Exception as e:
        print(f"❌ Ошибка при получении персонажа: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_all_races():
    """Получение списка всех рас"""
    return RACES

def update_character_stats(user_id, **kwargs):
    """Обновление характеристик персонажа"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        set_clauses = []
        values = []
        for key, value in kwargs.items():
            set_clauses.append(f"{key} = %s")
            values.append(value)
        
        values.append(user_id)
        query = f"UPDATE player_characters SET {', '.join(set_clauses)} WHERE user_id = %s"
        
        cursor.execute(query, values)
        conn.commit()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при обновлении персонажа: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def calculate_rank(level, experience):
    """Определение ранга на основе уровня и опыта - УСЛОЖНЕННЫЙ ВАРИАНТ"""
    if level >= 50:  # Повышены требования
        return 'S'
    elif level >= 40:
        return 'A'
    elif level >= 30:
        return 'B'
    elif level >= 20:
        return 'C'
    elif level >= 10:
        return 'D'
    else:
        return 'E'

def add_experience(user_id, exp_amount):
    """Добавление опыта персонажу - УСЛОЖНЕННАЯ ВЕРСИЯ"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            return False, False, 0, 0
        
        cursor = conn.cursor()
        
        # Получаем текущие данные персонажа
        cursor.execute("""
            SELECT experience, level, stat_points, rank, vitality, intelligence, race
            FROM player_characters WHERE user_id = %s
        """, (user_id,))
        result = cursor.fetchone()
        
        if not result:
            return False, False, 0, 0
        
        current_exp, current_level, current_stat_points, current_rank, vitality, intelligence, race = result
        
        # Добавляем опыт
        new_exp = current_exp + exp_amount
        new_level = current_level
        level_up = False
        stat_points_gained = 0
        
        # Проверяем, достаточно ли опыта для повышения уровня
        # Формула: для перехода с уровня N на N+1 нужно N * 150 опыта (вместо 100)
        
        while True:
            # Общий опыт для уровня L: сумма от 1 до L (i * 150)
            total_exp_for_next_level = ((new_level) * (new_level + 1) * 150) // 2
            
            if new_exp >= total_exp_for_next_level:
                new_level += 1
                level_up = True
                stat_points_gained += 2  # Только 2 очка за уровень
            else:
                break
        
        if level_up:
            # Рассчитываем новый ранг
            new_rank = calculate_rank(new_level, new_exp)
            
            # Рассчитываем увеличение здоровья и маны
            race_info = RACES.get(race, RACES['human'])
            new_max_health = vitality * race_info['health_multiplier']
            new_max_mana = intelligence * race_info['mana_multiplier']
            
            # Обновляем персонажа
            cursor.execute("""
                UPDATE player_characters 
                SET experience = %s, level = %s, stat_points = stat_points + %s, rank = %s,
                    max_health = %s,
                    max_mana = %s,
                    health = %s,
                    mana = %s
                WHERE user_id = %s
            """, (
                new_exp, new_level, stat_points_gained, new_rank,
                new_max_health,
                new_max_mana,
                new_max_health,
                new_max_mana,
                user_id
            ))
        else:
            # Обновляем только опыт
            cursor.execute("""
                UPDATE player_characters 
                SET experience = %s
                WHERE user_id = %s
            """, (new_exp, user_id))
        
        conn.commit()
        return True, level_up, new_level, stat_points_gained
        
    except Exception as e:
        print(f"❌ Ошибка при добавлении опыта: {e}")
        if conn:
            conn.rollback()
        return False, False, 0, 0
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def add_stat_point(user_id, stat_type):
    """Распределение очка характеристики"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            return False, "Ошибка подключения к БД"
        
        cursor = conn.cursor()
        
        # Проверяем, есть ли очки характеристик
        cursor.execute("SELECT stat_points FROM player_characters WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        
        if not result:
            return False, "Персонаж не найден"
        
        stat_points = result[0]
        
        if stat_points <= 0:
            return False, "У тебя нет очков характеристик для распределения!"
        
        # Определяем, какую характеристику улучшаем
        if stat_type == 'strength':
            cursor.execute("""
                UPDATE player_characters 
                SET strength = strength + 1, stat_points = stat_points - 1
                WHERE user_id = %s
            """, (user_id,))
            
        elif stat_type == 'agility':
            cursor.execute("""
                UPDATE player_characters 
                SET agility = agility + 1, stat_points = stat_points - 1
                WHERE user_id = %s
            """, (user_id,))
            
        elif stat_type == 'intelligence':
            cursor.execute("""
                UPDATE player_characters 
                SET intelligence = intelligence + 1, stat_points = stat_points - 1
                WHERE user_id = %s
            """, (user_id,))
            
        elif stat_type == 'vitality':
            # При повышении живучести также увеличиваем максимальное здоровье
            cursor.execute("""
                SELECT vitality, race FROM player_characters WHERE user_id = %s
            """, (user_id,))
            char_result = cursor.fetchone()
            
            if char_result:
                vitality, race = char_result
                race_info = RACES.get(race, RACES['human'])
                health_per_vitality = race_info['health_multiplier']
                
                cursor.execute("""
                    UPDATE player_characters 
                    SET vitality = vitality + 1, 
                        stat_points = stat_points - 1,
                        max_health = max_health + %s,
                        health = health + %s
                    WHERE user_id = %s
                """, (health_per_vitality, health_per_vitality, user_id))
            
        else:
            return False, "Неизвестная характеристика"
        
        conn.commit()
        return True, f"Характеристика '{stat_type}' увеличена на 1!"
        
    except Exception as e:
        print(f"❌ Ошибка при распределении характеристики: {e}")
        if conn:
            conn.rollback()
        return False, f"Ошибка: {e}"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def add_gold(user_id, gold_amount):
    """Добавление золота персонажу"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE player_characters 
            SET gold = gold + %s 
            WHERE user_id = %s
        """, (gold_amount, user_id))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Ошибка при добавлении золота: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def increment_boss_kills(user_id, is_mini_boss=False):
    """Увеличение счетчика убитых боссов"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        if is_mini_boss:
            cursor.execute("""
                UPDATE player_characters 
                SET mini_boss_kills = mini_boss_kills + 1
                WHERE user_id = %s
            """, (user_id,))
        else:
            cursor.execute("""
                UPDATE player_characters 
                SET boss_kills = boss_kills + 1
                WHERE user_id = %s
            """, (user_id,))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Ошибка при увеличении счетчика боссов: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def buy_item(user_id, item_key, item_type, item_name, price, effect_amount=None):
    """Покупка предмета в магазине"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            return False, "Ошибка подключения к БД"
        
        cursor = conn.cursor()
        
        # Проверяем баланс игрока
        cursor.execute("SELECT gold FROM player_characters WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        
        if not result:
            return False, "Персонаж не найден"
        
        current_gold = result[0]
        
        if current_gold < price:
            return False, f"Недостаточно золота! Нужно {price}, есть {current_gold}"
        
        # Списываем золото
        cursor.execute("""
            UPDATE player_characters 
            SET gold = gold - %s 
            WHERE user_id = %s
        """, (price, user_id))
        
        # Устанавливаем effect_amount по умолчанию, если не передан
        if effect_amount is None:
            if 'small_health_potion' in item_key:
                effect_amount = 20
            elif 'large_health_potion' in item_key:
                effect_amount = 40
            elif 'small_mana_potion' in item_key:
                effect_amount = 15
            elif 'large_mana_potion' in item_key:
                effect_amount = 30
            else:
                effect_amount = 0
        
        # Проверяем, есть ли уже такой предмет в инвентаре
        cursor.execute("""
            SELECT id, quantity FROM player_inventory 
            WHERE user_id = %s AND item_key = %s
        """, (user_id, item_key))
        
        existing_item = cursor.fetchone()
        
        if existing_item:
            # Увеличиваем количество
            item_id, quantity = existing_item
            cursor.execute("""
                UPDATE player_inventory 
                SET quantity = quantity + 1
                WHERE id = %s
            """, (item_id,))
        else:
            # Вставляем новую запись
            cursor.execute("""
                INSERT INTO player_inventory 
                (user_id, item_key, item_type, item_name, quantity, effect_amount)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, item_key, item_type, item_name, 1, effect_amount))
        
        conn.commit()
        return True, f"Предмет '{item_name}' куплен успешно!"
        
    except Exception as e:
        print(f"❌ Ошибка при покупке предмета: {e}")
        if conn:
            conn.rollback()
        return False, f"Ошибка при покупке: {e}"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_inventory(user_id):
    """Получение инвентаря игрока"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Группируем предметы по item_key и суммируем количество
        cursor.execute("""
            SELECT 
                item_key,
                item_type,
                item_name,
                SUM(quantity) as quantity,
                MAX(effect_amount) as effect_amount
            FROM player_inventory 
            WHERE user_id = %s AND quantity > 0
            GROUP BY item_key, item_type, item_name
            ORDER BY 
                CASE item_type
                    WHEN 'potion' THEN 1
                    WHEN 'weapon' THEN 2
                    WHEN 'armor' THEN 3
                    WHEN 'artifact' THEN 4
                    ELSE 5
                END,
                item_name
        """, (user_id,))
        
        return cursor.fetchall()
        
    except Exception as e:
        print(f"❌ Ошибка при получении инвентаря: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def use_item(user_id, item_key, item_type, item_name, effect_amount):
    """Использование предмета из инвентаря"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            return False, "Ошибка подключения к БД"
        
        cursor = conn.cursor()
        
        # Находим первую запись с этим предметом
        cursor.execute("""
            SELECT id, quantity, effect_amount FROM player_inventory 
            WHERE user_id = %s AND item_key = %s AND quantity > 0
            ORDER BY id
            LIMIT 1
        """, (user_id, item_key))
        
        result = cursor.fetchone()
        if not result:
            return False, "Предмет не найден в инвентаре"
        
        item_id, quantity, db_effect_amount = result
        
        # Используем effect_amount из базы, если он не передан
        if effect_amount is None or effect_amount == 0:
            effect_amount = db_effect_amount or 0
        
        # Уменьшаем количество на 1
        new_quantity = quantity - 1
        
        if new_quantity <= 0:
            # Удаляем запись, если предметы закончились
            cursor.execute("""
                DELETE FROM player_inventory 
                WHERE id = %s
            """, (item_id,))
        else:
            # Обновляем количество
            cursor.execute("""
                UPDATE player_inventory 
                SET quantity = %s
                WHERE id = %s
            """, (new_quantity, item_id))
        
        # Восстанавливаем здоровье или ману
        message = ""
        
        if 'health_potion' in item_key:
            # Зелье здоровья - получаем текущее состояние персонажа
            cursor.execute("""
                SELECT health, max_health FROM player_characters 
                WHERE user_id = %s
            """, (user_id,))
            char_result = cursor.fetchone()
            
            if not char_result:
                conn.rollback()
                return False, "Персонаж не найден"
            
            current_health, max_health = char_result
            new_health = min(max_health, current_health + effect_amount)
            health_restored = new_health - current_health
            
            # Обновляем здоровье
            cursor.execute("""
                UPDATE player_characters 
                SET health = %s
                WHERE user_id = %s
            """, (new_health, user_id))
            
            message = f"Использовано {item_name}. Восстановлено {health_restored} HP!"
            
        elif 'mana_potion' in item_key:
            # Зелье маны - получаем текущее состояние персонажа
            cursor.execute("""
                SELECT mana, max_mana FROM player_characters 
                WHERE user_id = %s
            """, (user_id,))
            char_result = cursor.fetchone()
            
            if not char_result:
                conn.rollback()
                return False, "Персонаж не найден"
            
            current_mana, max_mana = char_result
            new_mana = min(max_mana, current_mana + effect_amount)
            mana_restored = new_mana - current_mana
            
            # Обновляем ману
            cursor.execute("""
                UPDATE player_characters 
                SET mana = %s
                WHERE user_id = %s
            """, (new_mana, user_id))
            
            message = f"Использовано {item_name}. Восстановлено {mana_restored} MP!"
        else:
            # Для других типов предметов (оружие, броня, артефакты)
            # Здесь можно добавить логику для применения эффектов предметов
            message = f"Предмет '{item_name}' использован!"
        
        conn.commit()
        return True, message
        
    except Exception as e:
        print(f"❌ Ошибка при использовании предмета: {e}")
        if conn:
            conn.rollback()
        return False, f"Ошибка: {e}"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def log_battle(user_id, enemy_type, enemy_name, result, damage_dealt=0, damage_taken=0, gold_earned=0, experience_earned=0, is_boss=False, is_mini_boss=False):
    """Логирование боя"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO battle_logs 
            (user_id, enemy_type, enemy_name, result, damage_dealt, damage_taken, gold_earned, experience_earned, is_boss, is_mini_boss)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (user_id, enemy_type, enemy_name, result, damage_dealt, damage_taken, gold_earned, experience_earned, is_boss, is_mini_boss))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Ошибка при логировании боя: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_player_stats(user_id):
    """Получение статистики игрока"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            return None
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                character_name,
                race,
                level,
                rank,
                experience,
                stat_points,
                battle_wins,
                battle_losses,
                boss_kills,
                mini_boss_kills,
                gold,
                created_at,
                physical_resistance,
                magic_resistance
            FROM player_characters 
            WHERE user_id = %s
        """, (user_id,))
        
        return cursor.fetchone()
        
    except Exception as e:
        print(f"❌ Ошибка при получении статистики: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_top_players(limit=10):
    """Получение топ-N игроков по уровню и опыту"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                character_name,
                race,
                level,
                rank,
                experience,
                battle_wins,
                battle_losses,
                boss_kills,
                mini_boss_kills,
                gold,
                created_at
            FROM player_characters 
            ORDER BY level DESC, experience DESC, boss_kills DESC, battle_wins DESC
            LIMIT %s
        """, (limit,))
        
        return cursor.fetchall()
        
    except Exception as e:
        print(f"❌ Ошибка при получении топа игроков: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ - УСЛОЖНЕННЫЕ ---

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
        'E': '#808080',
        'D': '#00FF00',
        'C': '#0000FF',
        'B': '#800080',
        'A': '#FF8C00',
        'S': '#FF0000'
    }
    return colors.get(rank, '#808080')

def get_difficulty_icon(difficulty):
    """Получение иконки для сложности врага"""
    icons = {
        'easy': '🟢',
        'medium': '🟡',
        'hard': '🟠',
        'very_hard': '🔴',
        'extreme': '💀',
        'legendary': '👑',
        'boss': '👑',
        'mini_boss': '⭐'
    }
    return icons.get(difficulty, '⚪')

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
    """Получение информации о следующем ранге - УСЛОЖНЕННЫЙ ВАРИАНТ"""
    rank_progression = {
        'E': {'next': 'D', 'level': 15},  # Повышены требования
        'D': {'next': 'C', 'level': 25},
        'C': {'next': 'B', 'level': 35},
        'B': {'next': 'A', 'level': 45},
        'A': {'next': 'S', 'level': 55},
        'S': {'next': None, 'level': None}
    }
    
    if current_rank == 'S':
        return "🏆 Ты достиг максимального ранга!"
    
    next_rank = rank_progression[current_rank]['next']
    required_level = rank_progression[current_rank]['level']
    
    if current_level >= required_level:
        return f"{get_rank_icon(next_rank)} {next_rank}-ранг (ДОСТИГНУТ!)"
    else:
        levels_needed = required_level - current_level
        return f"{get_rank_icon(next_rank)} {next_rank}-ранг (требуется {required_level} уровень, осталось {levels_needed} ур.)"

def get_xp_progress(level, experience):
    """Рассчитывает прогресс опыта для текущего уровня - УСЛОЖНЕННАЯ ВЕРСИЯ"""
    # Опыт, который был нужен для достижения текущего уровня
    if level > 1:
        # Сумма арифметической прогрессии: сумма от 1 до (level-1) (i * 150)
        xp_for_previous_levels = ((level - 1) * level * 150) // 2
    else:
        xp_for_previous_levels = 0
    
    # Опыт, который уже есть у игрока сверх необходимого для текущего уровня
    current_xp_on_level = experience - xp_for_previous_levels
    
    # Опыт нужный для перехода на следующий уровень
    xp_for_next_level = level * 150
    
    # Не даем превысить максимум
    if current_xp_on_level > xp_for_next_level:
        current_xp_on_level = xp_for_next_level
    
    percent = current_xp_on_level / xp_for_next_level if xp_for_next_level > 0 else 0
    
    return current_xp_on_level, xp_for_next_level, percent

def get_xp_bar(level, experience, length=10):
    """Создает индикатор опыта - УСЛОЖНЕННЫЙ ВАРИАНТ"""
    current_xp, max_xp, percent = get_xp_progress(level, experience)
    
    if max_xp <= 0:
        return "▯" * length
    
    filled = int(length * percent)
    empty = length - filled
    
    if percent >= 1.0:
        bar = "█" * length
    elif percent >= 0.7:
        bar = "▓" * filled + "░" * empty
    elif percent >= 0.4:
        bar = "▒" * filled + "░" * empty
    else:
        bar = "░" * filled + "░" * empty
    
    return f"{bar} {int(current_xp)}/{max_xp} XP"

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

def calculate_player_dodge_chance(agility):
    """Рассчитывает шанс уклонения игрока на основе ловкости - УСЛОЖНЕННЫЙ ВАРИАНТ"""
    base_chance = 0.03  # Уменьшен базовый шанс 3%
    agility_bonus = min(agility * 0.003, 0.15)  # 0.3% за 1 ловкости, максимум 15%
    return min(base_chance + agility_bonus, 0.25)  # Максимум 25%

def calculate_crit_chance(agility):
    """Рассчитывает шанс критического удара на основе ловкости - УСЛОЖНЕННЫЙ ВАРИАНТ"""
    base_chance = 0.03  # Уменьшен базовый шанс 3%
    agility_bonus = min(agility * 0.002, 0.10)  # 0.2% за 1 ловкости, максимум 10%
    return min(base_chance + agility_bonus, 0.15)  # Максимум 15%

def calculate_damage(character, enemy, damage_type='physical'):
    """Расчет урона с учетом сопротивлений - УСЛОЖНЕННЫЙ ВАРИАНТ"""
    # Базовый урон (сильнее уменьшен)
    if damage_type == 'physical':
        base_damage = max(1, character['strength'] // 3)  # Сила дает меньше урона
        enemy_resistance = enemy.get('physical_resistance', 0.0)
    else:  # magical
        base_damage = max(1, character['intelligence'] // 3)  # Интеллект дает меньше урона
        enemy_resistance = enemy.get('magic_resistance', 0.0)
    
    # Меньший разброс урона
    min_damage = int(base_damage * 0.8)
    max_damage = int(base_damage * 1.2)
    damage = random.randint(min_damage, max_damage)
    
    # Сильнее применяем сопротивление врага
    damage = max(1, int(damage * (1 - enemy_resistance)))
    
    # Учитываем шанс критического удара
    crit_chance = calculate_crit_chance(character.get('agility', 8))
    is_crit = random.random() < crit_chance
    
    if is_crit:
        damage = int(damage * 1.5)  # Уменьшен множитель крита
    
    return damage, is_crit

def calculate_enemy_damage(enemy, character):
    """Расчет урона врага с учетом сопротивлений персонажа - УСЛОЖНЕННЫЙ ВАРИАНТ"""
    if enemy['damage_type'] == 'physical':
        min_damage = enemy['min_physical_damage']
        max_damage = enemy['max_physical_damage']
        character_resistance = character.get('physical_resistance', 0.0)
    elif enemy['damage_type'] == 'magic':
        min_damage = enemy['min_magic_damage']
        max_damage = enemy['max_magic_damage']
        character_resistance = character.get('magic_resistance', 0.0)
    else:  # mixed
        if random.random() < 0.5:
            min_damage = enemy['min_physical_damage']
            max_damage = enemy['max_physical_damage']
            character_resistance = character.get('physical_resistance', 0.0)
        else:
            min_damage = enemy['min_magic_damage']
            max_damage = enemy['max_magic_damage']
            character_resistance = character.get('magic_resistance', 0.0)
    
    damage = random.randint(min_damage, max_damage)
    
    # Сильнее применяем сопротивление персонажа
    damage = int(damage * (1 - character_resistance))
    
    # Учитываем шанс уклонения игрока
    dodge_chance = calculate_player_dodge_chance(character.get('agility', 8))
    is_dodged = random.random() < dodge_chance
    
    return max(1, damage), is_dodged

# Функция для обработки специальных атак врагов
def process_enemy_special_attack(enemy, character, battle_log):
    """Обработка специальных атак врага"""
    damage = 0
    additional_effect = ""
    status_effect = None
    
    # Определяем, будет ли специальная атака
    if random.random() < enemy.get('special_chance', 0.15):
        # Выбираем случайную способность из доступных (кроме basic_attack)
        available_abilities = [a for a in enemy['abilities'] if a != 'basic_attack']
        if available_abilities:
            ability = random.choice(available_abilities)
            
            if ability == 'poison_spit':
                damage = random.randint(enemy['min_physical_damage'] // 2, enemy['max_physical_damage'] // 2)
                additional_effect = f" Яд наносит дополнительно {damage} урона в следующий ход!"
                battle_log.append(f"☠️ {enemy['name']} плюется ядом! Ты получаешь {damage} урона и отравлен!")
                status_effect = 'poisoned'
                
            elif ability == 'web_shot':
                damage = 0
                additional_effect = " Ты опутан паутиной и пропускаешь следующий ход!"
                battle_log.append(f"🕸️ {enemy['name']} опутывает тебя паутиной! Ты не можешь атаковать в следующем ходу!")
                status_effect = 'webbed'
                
            elif ability == 'blood_drain':
                damage = random.randint(enemy['min_physical_damage'], enemy['max_physical_damage'])
                heal_amount = damage // 2
                enemy['health'] = min(enemy['max_health'], enemy['health'] + heal_amount)
                additional_effect = f" Враг восстанавливает {heal_amount} здоровья!"
                battle_log.append(f"🩸 {enemy['name']} пьет твою кровь! Ты теряешь {damage} HP, враг восстанавливает {heal_amount} HP!")
                
            elif ability == 'hellfire':
                damage = random.randint(int(enemy['min_magic_damage'] * 1.5), int(enemy['max_magic_damage'] * 1.5))
                additional_effect = f" Адское пламя наносит {damage} урона!"
                battle_log.append(f"🔥 {enemy['name']} испускает адское пламя! Ты получаешь {damage} урона!")
                
            elif ability == 'dragon_breath':
                damage = random.randint(enemy['min_magic_damage'] * 2, enemy['max_magic_damage'] * 2)
                additional_effect = f" Дыхание дракона наносит {damage} урона!"
                battle_log.append(f"🐉 {enemy['name']} использует дыхание дракона! Ты получаешь {damage} урона!")
                
            elif ability == 'summon_skeletons':
                damage = 0
                additional_effect = " Враг призывает скелетов для помощи!"
                battle_log.append(f"💀 {enemy['name']} призывает скелетов! Они будут помогать ему в бою!")
                
            elif ability == 'healing_leaves':
                damage = 0
                heal_amount = enemy['max_health'] // 5
                enemy['health'] = min(enemy['max_health'], enemy['health'] + heal_amount)
                additional_effect = f" Враг восстанавливает {heal_amount} здоровья с помощью магии леса!"
                battle_log.append(f"🌿 {enemy['name']} использует исцеляющие листья! Враг восстанавливает {heal_amount} HP!")
                
            elif ability == 'apocalypse':
                damage = random.randint(enemy['min_physical_damage'] * 3, enemy['max_physical_damage'] * 3)
                additional_effect = f" Апокалипсис наносит {damage} урона!"
                battle_log.append(f"☄️ {enemy['name']} вызывает апокалипсис! Ты получаешь {damage} урона!")
                
            elif ability == 'omnipotence':
                damage = random.randint(enemy['min_magic_damage'] * 4, enemy['max_magic_damage'] * 4)
                additional_effect = f" Всемогущество бога наносит {damage} урона!"
                battle_log.append(f"⚡ {enemy['name']} использует свою божественную силу! Ты получаешь {damage} урона!")
                
            elif ability == 'stun_attack' or ability == 'mountain_slam':
                damage = random.randint(enemy['min_physical_damage'], enemy['max_physical_damage'])
                additional_effect = " Ты оглушен и пропускаешь следующий ход!"
                battle_log.append(f"💫 {enemy['name']} оглушает тебя! Ты теряешь {damage} HP и не можешь действовать в следующем ходу!")
                status_effect = 'stunned'
                
            else:
                # Базовая усиленная атака для других способностей
                if enemy['damage_type'] == 'physical':
                    damage = random.randint(int(enemy['min_physical_damage'] * 1.3), int(enemy['max_physical_damage'] * 1.3))
                else:
                    damage = random.randint(int(enemy['min_magic_damage'] * 1.3), int(enemy['max_magic_damage'] * 1.3))
                battle_log.append(f"✨ {enemy['name']} использует {ability.replace('_', ' ')}! Ты получаешь {damage} урона!")
    
    return damage, additional_effect, status_effect

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
                f"💪 СИЛА: {character['strength']} (+{max(1, character['strength']//3)} урон)",
                callback_data='levelup_strength'
            )
        ])
        keyboard.append([
            InlineKeyboardButton(
                f"🏹 ЛОВКОСТЬ: {character['agility']} (+{calculate_player_dodge_chance(character['agility'])*100:.1f}% уклонение)",
                callback_data='levelup_agility'
            )
        ])
        keyboard.append([
            InlineKeyboardButton(
                f"🧠 ИНТЕЛЛЕКТ: {character['intelligence']} (+{max(1, character['intelligence']//3)} магич. урон)",
                callback_data='levelup_intelligence'
            )
        ])
        keyboard.append([
            InlineKeyboardButton(
                f"❤️ ЖИВУЧЕСТЬ: {character['vitality']} (+{character['vitality']*RACES[character['race']]['health_multiplier']} HP)",
                callback_data='levelup_vitality'
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
        if 'potion' in item['item_key']:
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
                f"{race_data['name']} (💪{race_data['strength']} | 🏹{race_data['agility']} | 🧠{race_data['intelligence']} | ❤️{race_data['vitality']})",
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
        difficulty_icon = get_difficulty_icon(location['difficulty'])
        keyboard.append([
            InlineKeyboardButton(
                f"{rank_icon} {location['name']} {difficulty_icon}",
                callback_data=f'location_{rank_key}'
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Вернуться в лагерь", callback_data='back_to_main')])
    return InlineKeyboardMarkup(keyboard)

def get_location_enemies_keyboard(location_rank, player_level):
    """Клавиатура выбора врагов в локации"""
    keyboard = []
    
    location = LOCATIONS.get(location_rank)
    if not location:
        return InlineKeyboardMarkup(keyboard)
    
    # Сначала обычные враги
    for enemy_key in location['enemies']:
        if enemy_key == location['boss'] or enemy_key == location.get('mini_boss'):
            continue  # Боссов и мини-боссов добавляем отдельно
            
        enemy = create_enemy(enemy_key, player_level)
        if enemy:
            difficulty_icon = get_difficulty_icon(enemy['difficulty'])
            rank_icon = get_rank_icon(enemy['rank'])
            
            keyboard.append([
                InlineKeyboardButton(
                    f"{difficulty_icon} {enemy['name']} {rank_icon}",
                    callback_data=f'battle_{enemy_key}'
                )
            ])
    
    # Затем мини-босс локации (если есть)
    if location.get('mini_boss'):
        mini_boss = create_enemy(location['mini_boss'], player_level)
        if mini_boss:
            mini_boss_icon = "⭐"
            rank_icon = get_rank_icon(mini_boss['rank'])
            
            keyboard.append([
                InlineKeyboardButton(
                    f"{mini_boss_icon} {mini_boss['name']} (МИНИ-БОСС) {rank_icon}",
                    callback_data=f'battle_{location["mini_boss"]}'
                )
            ])
    
    # Затем босс локации (если есть)
    if location.get('boss'):
        boss = create_enemy(location['boss'], player_level)
        if boss:
            boss_icon = "👑"
            rank_icon = get_rank_icon(boss['rank'])
            
            keyboard.append([
                InlineKeyboardButton(
                    f"{boss_icon} {boss['name']} (БОСС) {rank_icon}",
                    callback_data=f'battle_{location["boss"]}'
                )
            ])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад к локациям", callback_data='back_to_battle_menu')])
    return InlineKeyboardMarkup(keyboard)

def get_battle_action_keyboard():
    """Клавиатура действий в бою"""
    keyboard = [
        [InlineKeyboardButton("⚔️ ФИЗИЧЕСКАЯ АТАКА", callback_data='attack_physical'),
         InlineKeyboardButton("🔮 МАГИЧЕСКАЯ АТАКА", callback_data='attack_magic')],
        [InlineKeyboardButton("🛡️ БЛОК", callback_data='defend'),
         InlineKeyboardButton("✨ РАСОВАЯ СПОСОБНОСТЬ", callback_data='ability')],
        [InlineKeyboardButton("💊 ЗЕЛЬЕ ЗДОРОВЬЯ", callback_data='use_health_potion'),
         InlineKeyboardButton("🔮 ЗЕЛЬЕ МАНЫ", callback_data='use_mana_potion')],
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
                f"💊 Малое зелье здоровья (+20 HP) - 40💰",
                callback_data='buy_small_health_potion'
            )
        ])
        
        keyboard.append([
            InlineKeyboardButton(
                f"💊 Большое зелье здоровья (+40 HP) - 75💰",
                callback_data='buy_large_health_potion'
            )
        ])
        
        keyboard.append([
            InlineKeyboardButton(
                f"🔮 Малое зелье маны (+15 MP) - 35💰",
                callback_data='buy_small_mana_potion'
            )
        ])
        
        keyboard.append([
            InlineKeyboardButton(
                f"🔮 Большое зелье маны (+30 MP) - 65💰",
                callback_data='buy_large_mana_potion'
            )
        ])
        
        # Предметы по рангам
        rank_order = ['E', 'D', 'C', 'B', 'A', 'S']
        player_rank_index = rank_order.index(rank)
        
        # Меч D-ранга
        if player_rank_index >= rank_order.index('D'):
            keyboard.append([
                InlineKeyboardButton(
                    "⚔️ Меч D-ранга (+3 силы) - 300💰",
                    callback_data='buy_0'
                )
            ])
        else:
            keyboard.append([
                InlineKeyboardButton(
                    "⚔️ Меч D-ранга [Требуется D-ранг] - 300💰",
                    callback_data='buy_info_rank_d'
                )
            ])
        
        # Броня C-ранга
        if player_rank_index >= rank_order.index('C'):
            keyboard.append([
                InlineKeyboardButton(
                    "🛡️ Броня C-ранга (+5 живучести) - 400💰",
                    callback_data='buy_1'
                )
            ])
        else:
            keyboard.append([
                InlineKeyboardButton(
                    "🛡️ Броня C-ранга [Требуется C-ранг] - 400💰",
                    callback_data='buy_info_rank_c'
                )
            ])
        
        # Кольцо ловкости
        if player_rank_index >= rank_order.index('C'):
            keyboard.append([
                InlineKeyboardButton(
                    "💍 Кольцо ловкости (+5 ловкости) - 450💰",
                    callback_data='buy_ring_of_agility'
                )
            ])
        else:
            keyboard.append([
                InlineKeyboardButton(
                    "💍 Кольцо ловкости [Требуется C-ранг] - 450💰",
                    callback_data='buy_info_ring_agility'
                )
            ])
        
        # Артефакт B-ранга
        if player_rank_index >= rank_order.index('B'):
            keyboard.append([
                InlineKeyboardButton(
                    "💎 Артефакт B-ранга (+8 интеллекта) - 600💰",
                    callback_data='buy_2'
                )
            ])
        else:
            keyboard.append([
                InlineKeyboardButton(
                    "💎 Артефакт B-ранга [Требуется B-ранг] - 600💰",
                    callback_data='buy_info_rank_b'
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
                f"Ты стоишь на главной площади деревня. Впереди — великие свершения!",
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

🏆 **УСЛОЖНЕННАЯ СИСТЕМА РАНГОВ:**
🆕 E-ранг — Начинающие охотники (уровень 1-14)
🟢 D-ранг — Рядовые бойцы (уровень 15-24)
🔵 C-ранг — Средний уровень (уровень 25-34)
🟣 B-ранг — Сильные охотники (уровень 35-44)
🟠 A-ранг — Элита (уровень 45-54)
⚡ S-ранг — Легенды (уровень 55+)

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
👨 **Человек** — `Баланс`
🧝 **Эльф** — `Магия` (+30% маны, +8% физического сопротивления)
⚒️ **Дварф** — `Живучесть` (+15% здоровья, +15% магического сопротивления)
👹 **Орк** — `Ярость` (Рискованные, но мощные атаки)

📈 **УСЛОЖНЕННАЯ ПРОКАЧКА:**
• За каждый уровень получаешь *2 очка характеристик* (вместо 3)
• Опыт для уровня: уровень × 150 (вместо 100)
• Можешь распределить их между:
  💪 *СИЛА* - Увеличивает физический урон (сила ÷ 3)
  🏹 *ЛОВКОСТЬ* - Увеличивает шанс уклонения (до 25%) и критического удара (до 15%)
  🧠 *ИНТЕЛЛЕКТ* - Увеличивает магический урон (интеллект ÷ 3) и ману
  ❤️ *ЖИВУЧЕСТЬ* - Увеличивает максимальное здоровье

🎒 **Инвентарь:**
• Теперь есть отдельная вкладка инвентаря!
• Используй зелья для восстановления здоровья и маны
• Все купленные предметы хранятся в инвентаре

💊 **Магазин:**
• Зелья здоровья - Быстрое восстановление в бою
• Зелья маны - Восполнение магической энергии
• Оружие и броня по рангам

⚔️ **УСИЛЕННАЯ СИСТЕМА ВРАГОВ:**
• Враги усиливаются с твоим уровнем (+15% за уровень)
• В каждой локации есть обычные враги, мини-боссы и боссы
• Мини-боссы и боссы дают больше опыта и золота
• У врагов есть особые способности (яд, лечение, призыв и т.д.)
• Враги имеют физическое и магическое сопротивление
• Враги имеют повышенные шансы уклонения и сопротивления

🛡️ **УСЛОЖНЕННАЯ СИСТЕМА БОЯ:**
• *Физический урон* - зависит от силы ÷ 3, сильно снижается физическим сопротивлением
• *Магический урон* - зависит от интеллекта ÷ 3, сильно снижается магическим сопротивлением
• *Шанс уклонения* - зависит от ловкости (до 25%)
• *Шанс крита* - зависит от ловкости (до 15%), множитель ×1.5
• *Сопротивления* - сильно уменьшают получаемый урон соответствующего типа

🗡 **Тактика боя:**
• ⚔️ *Физическая атака* - Удар оружием (зависит от силы)
• 🔮 *Магическая атака* - Магический удар (зависит от интеллекта)
• 🛡️ *Защита* - Снижает урон на 50%
• ✨ *Способность* - Уникальный навык твоей расы (тратит ману)
• 💊 *Зелье* - Использование зелья из инвентаря
• 🏃 *Сбежать* - Шанс 50% покинуть бой

🏆 **Соревнование:**
• Заходи в "👑 Топ игроков" чтобы увидеть лучших охотников
• Теперь учитываются убитые мини-боссы и боссы в статистике
• Повышай свой рейтинг, чтобы попасть в топ

_⚠️ ВНИМАНИЕ: Игра значительно усложнена!_
_⚠️ Прокачка теперь занимает в 2-3 раза больше времени_
_⚠️ Бои требуют тщательной тактики и подготовки_

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
                f"├ ❤️ Живучесть: `{race_data['vitality']}`\n"
                f"├ ❤️ Множитель здоровья: `{race_data['health_multiplier']}`\n"
                f"├ 🔮 Множитель маны: `{race_data['mana_multiplier']}`\n"
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
                f"🧠 Интеллект: `{race_data['intelligence']}`\n"
                f"❤️ Живучесть: `{race_data['vitality']}`\n\n"
                f"❤️ Множитель здоровья: `{race_data['health_multiplier']}`\n"
                f"🔮 Множитель маны: `{race_data['mana_multiplier']}`\n\n"
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
                   f"📈 <b>Стартовые очки:</b> 2 (распредели в профиле!)\n"
                   f"💰 <b>Начальное золото:</b> 50\n"
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
        
        if stat_type in ['strength', 'agility', 'intelligence', 'vitality']:
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
                    'intelligence': 'Интеллект 🧠',
                    'vitality': 'Живучесть ❤️'
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
                        f"💪 Сила: `{character_after['strength']}` (+{max(1, character_after['strength']//3)} урон)\n"
                        f"🏹 Ловкость: `{character_after['agility']}` (+{calculate_player_dodge_chance(character_after['agility'])*100:.1f}% уклонение)\n"
                        f"🧠 Интеллект: `{character_after['intelligence']}` (+{max(1, character_after['intelligence']//3)} маг. урон)\n"
                        f"❤️ Живучесть: `{character_after['vitality']}` (+{character_after['vitality']*RACES[character_after['race']]['health_multiplier']} HP)\n\n"
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
🏆 *УСЛОЖНЕННАЯ СИСТЕМА РАНГОВ ОХОТНИКОВ*

🆕 *E-ранг* — Начинающие охотники
• Уровень: 1-14
• Способности лишь немного выше человеческих
• Сон Джинву начинал свой путь здесь
• Доступно: Тренировочный лагерь

🟢 *D-ранг* — Рядовые бойцы
• Уровень: 15-24
• Могут справляться с низкоуровневыми подземельями
• Способны на базовые магические атаки
• Доступно: Лес призраков

🔵 *C-ранг* — Средний уровень
• Уровень: 25-34
• Могут зарабатывать на жизнь рейдами
• Имеют развитые боевые навыки
• Доступно: Заброшенные катакомбы

🟣 *B-ранг* — Сильные охотники
• Уровень: 35-44
• Часто лидеры в небольших группах
• Обладают уникальными способностями
• Доступно: Руины древнего замка

🟠 *A-ранг* — Элита
• Уровень: 45-54
• Обладают огромной мощью
• Могут в одиночку справляться с S-ранговыми угрозами
• Доступно: Врата в преисподнюю

⚡ *S-ранг* — Высший ранг
• Уровень: 55+
• Магическая сила не поддается измерению
• Легенды среди охотников
• Доступно: Трон божества

*Для повышения ранга:*
1. Повышай уровень персонажа
2. Набери необходимый опыт (уровень × 150)
3. Пройди испытание следующего ранга

⚠️ *ВНИМАНИЕ: Система прокачки усложнена!*
• Требуется больше опыта для уровней
• Меньше очков характеристик за уровень
• Враги сильнее адаптируются к твоему уровню

_Сила приходит с опытом, охотник. Стремись выше, но будь готов к трудностям!_
"""
    
    await query.edit_message_text(
        text=rank_info_text,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard(query.from_user.id)
    )

async def show_profile(query, user_id):
    """Показ профиля персонажа с УСЛОЖНЕННОЙ системой опыта"""
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
    
    # Получаем информацию об опыте с УСЛОЖНЕННОЙ функцией
    current_xp, max_xp, percent = get_xp_progress(character['level'], character['experience'])
    
    # Информация о прогрессе
    progress_info = ""
    if current_xp >= max_xp:
        progress_info = f"\n⚡ *ГОТОВ К ПОВЫШЕНИЮ УРОВНЯ!*"
    else:
        xp_needed_for_next_level = max_xp - current_xp
        progress_info = f"\n⏫ До следующего уровня: *{xp_needed_for_next_level}* XP"
    
    # Получаем следующий ранг
    next_rank_info = get_next_rank_info(rank, character['level'])
    
    # Рассчитываем боевые параметры с УСЛОЖНЕННЫМИ формулами
    dodge_chance = calculate_player_dodge_chance(character['agility'])
    crit_chance = calculate_crit_chance(character['agility'])
    physical_damage = max(1, character['strength'] // 3)
    magic_damage = max(1, character['intelligence'] // 3)
    
    await query.message.reply_photo(
        photo=image_url,
        caption=f"👤 *ПАСПОРТ ОХОТНИКА: {character['character_name']}*\n"
               f"{rank_icon} *{rank}-ранг* • ⭐ Уровень {character['level']}\n"
               f"✨ *Накопленный опыт:* `{character['experience']}` XP\n\n"
               f"❤️ ЗДОРОВЬЕ\n{health_bar}\n\n"
               f"🔮 МАНА\n{mana_bar}\n\n"
               f"✨ *ПРОГРЕСС УРОВНЯ*\n"
               f"📊 {get_xp_bar(character['level'], character['experience'])}"
               f"{progress_info}\n\n"
               f"🎯 *Следующий ранг:* {next_rank_info}",
        parse_mode='Markdown'
    )
    
    # Добавляем подробную информацию о прокачке
    if character['level'] < 70:  # Максимальный уровень
        next_level_xp_needed = max_xp - current_xp
        
        if next_level_xp_needed > 0:
            levelup_info = (
                f"\n📈 *Детали прокачки:*\n"
                f"• Уровень {character['level']} → {character['level'] + 1}\n"
                f"• Опыт на уровне: {int(current_xp)}/{max_xp} XP\n"
                f"• Прогресс: {percent:.1%}\n"
                f"• Осталось: {next_level_xp_needed} XP\n"
                f"• За уровень: +2 очка характеристик (вместо 3)"
            )
        else:
            levelup_info = "\n⚡ *ГОТОВ К ПОВЫШЕНИЮ УРОВНЯ!*\nЗагляни в главное меню для распределения характеристик!"
    else:
        levelup_info = "\n🏆 *ДОСТИГНУТ МАКСИМАЛЬНЫЙ УРОВЕНЬ!*"
    
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
    
    # Статистика характеристик
    stat_points = character.get('stat_points', 0)
    stats_info = ""
    if stat_points > 0:
        stats_info = f"\n\n🎯 *Нераспределенные очки характеристик:* `{stat_points}`\n"
        stats_info += f"_Нажми на кнопку '🌟 ПРОКАЧАТЬ ХАР-КИ' в главном меню!_"
    
    profile_text = (
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⚔️ *БОЕВЫЕ ПАРАМЕТРЫ*\n"
        f"💪 **Сила:**      `{character['strength']}` (+{physical_damage} физ. урон)\n"
        f"🏹 **Ловкость:**  `{character['agility']}` (+{dodge_chance*100:.1f}% уклонение, +{crit_chance*100:.1f}% крит)\n"
        f"🧠 **Интеллект:** `{character['intelligence']}` (+{magic_damage} маг. урон)\n"
        f"❤️ **Живучесть:** `{character['vitality']}` (+{character['vitality']*race_data['health_multiplier']} HP)\n"
        f"🛡️ **Физ. защита:** `{character.get('physical_resistance', 0)*100:.1f}%`\n"
        f"🔮 **Маг. защита:** `{character.get('magic_resistance', 0)*100:.1f}%`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 *БОГАТСТВО*\n"
        f"Золото: `{character['gold']}` монет\n\n"
        f"📜 *Достижения:*\n"
        f"⚔️ Побед: {character.get('battle_wins', 0)} | 💀 Поражений: {character.get('battle_losses', 0)}\n"
        f"⭐ Убито мини-боссов: {character.get('mini_boss_kills', 0)}\n"
        f"👑 Убито боссов: {character.get('boss_kills', 0)}\n\n"
        f"{levelup_info}\n"
        f"{stats_info}\n\n"
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
    potions_count = sum(item['quantity'] for item in inventory if 'potion' in item['item_key']) if inventory else 0
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
    
    # Отправляем текстовое сообщение
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
    
    # Получаем текущего персонажа до использования
    character_before = get_character(user_id)
    
    # Используем предмет
    success, message = use_item(
        user_id=user_id,
        item_key=item_key,
        item_type=item_to_use['item_type'],
        item_name=item_to_use['item_name'],
        effect_amount=item_to_use.get('effect_amount', 0)
    )
    
    if success:
        # Получаем обновленного персонажа после использования
        character_after = get_character(user_id)
        
        # Показываем сообщение об успешном использовании
        response_text = f"✅ *Предмет использован!*\n\n"
        
        # Добавляем информацию о восстановлении
        if 'health_potion' in item_key and character_before and character_after:
            health_restored = character_after['health'] - character_before['health']
            response_text += f"❤️ Восстановлено: *{health_restored}* здоровья\n"
            response_text += f"❤️ Текущее здоровье: *{character_after['health']}/{character_after['max_health']}*\n"
        elif 'mana_potion' in item_key and character_before and character_after:
            mana_restored = character_after['mana'] - character_before['mana']
            response_text += f"🔮 Восстановлено: *{mana_restored}* маны\n"
            response_text += f"🔮 Текущая мана: *{character_after['mana']}/{character_after['max_mana']}*\n"
        
        await query.answer(f"✅ {message}", show_alert=True)
        
        # Показываем обновленный инвентарь
        inventory = get_inventory(user_id)
        
        if inventory:
            # Обновляем сообщение с инвентарем
            total_items = sum(item['quantity'] for item in inventory)
            
            inventory_text = f"🎒 *ТВОЙ ИНВЕНТАРЬ*\n\n"
            inventory_text += response_text + "\n"
            inventory_text += f"📦 В инвентаре осталось `{total_items}` предметов"
            
            await query.edit_message_text(
                text=inventory_text,
                reply_markup=get_inventory_keyboard(inventory, 0),
                parse_mode='Markdown'
            )
        else:
            # Инвентарь пуст
            inventory_text = f"🎒 *ТВОЙ ИНВЕНТАРЬ*\n\n"
            inventory_text += response_text + "\n"
            inventory_text += f"📦 Твой инвентарь теперь пуст"
            
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

# --- ОБРАБОТЧИКИ БОЯ И ЛОКАЦИЙ ---

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
    difficulty_icon = get_difficulty_icon(location['difficulty'])
    
    # Показываем информацию о локации
    await query.message.reply_photo(
        photo=location['image'],
        caption=f"📍 *{location['name']}*\n{rank_icon} {location_rank}-ранг локация {difficulty_icon}\n\n"
               f"📜 {location['description']}\n\n"
               f"⭐ *Рекомендуемый уровень:* {location['min_level']}-{location['max_level']}\n\n"
               f"⚔️ *Доступные враги:*",
        parse_mode='Markdown'
    )
    
    await query.message.reply_text(
        text=f"Твой уровень: {character['level']}\nВыбери противника для боя:",
        reply_markup=get_location_enemies_keyboard(location_rank, character['level']),
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
    
    # Создаем врага с учетом уровня игрока
    enemy = create_enemy(enemy_type, character['level'])
    
    if not enemy:
        await query.edit_message_text(
            text="❌ Враг не найден!",
            reply_markup=get_main_menu_keyboard(user_id),
            parse_mode='Markdown'
        )
        return
    
    # Проверяем, доступен ли враг для ранга игрока
    player_rank = character.get('rank', 'E')
    enemy_rank = enemy['rank']
    
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
        'enemy': enemy,
        'character': character.copy(),
        'turn': 0,
        'player_defending': False,
        'enemy_defending': False,
        'log': [],
        'enemy_type': enemy_type,
        'poisoned': False,
        'webbed': False,
        'stunned': False,
        'player_damage_dealt': 0,
        'player_damage_taken': 0
    }
    
    enemy_rank_icon = get_rank_icon(enemy_rank)
    difficulty_icon = get_difficulty_icon(enemy['difficulty'])
    
    # Особое сообщение для боссов и мини-боссов
    if enemy.get('is_boss', False):
        boss_message = f"👑 *ВНИМАНИЕ! ЭТО БОСС ЛОКАЦИИ!* 👑\n\n"
        boss_message += f"{enemy['name']} - самый сильный враг в этой локации!\n"
        boss_message += f"Победа над ним принесет огромные награды!\n\n"
        await query.message.reply_text(boss_message, parse_mode='Markdown')
    elif enemy.get('is_mini_boss', False):
        mini_boss_message = f"⭐ *ВНИМАНИЕ! ЭТО МИНИ-БОСС!* ⭐\n\n"
        mini_boss_message += f"{enemy['name']} - сильный противник!\n"
        mini_boss_message += f"Победа принесет хорошие награды!\n\n"
        await query.message.reply_text(mini_boss_message, parse_mode='Markdown')
    
    await query.message.reply_photo(
        photo=enemy['image'],
        caption=f"🔥 *БОЙ НАЧАЛСЯ!* 🔥\n━━━━━━━━━━━━━━━━\n"
               f"👿 Противник: *{enemy['name']}*\n"
               f"{enemy_rank_icon} *Ранг врага:* {enemy_rank} {difficulty_icon}\n"
               f"📊 *Уровень врага:* усилен в {enemy['level_multiplier']}x\n"
               f"🛡️ *Физ. защита:* {enemy['physical_resistance']*100:.1f}%\n"
               f"🔮 *Маг. защита:* {enemy['magic_resistance']*100:.1f}%\n"
               f"🏹 *Уклонение:* {enemy['dodge_chance']*100:.1f}%\n"
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
    """Обработчик действий в бою с учетом маны и специальных атак"""
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
    
    # Проверяем статусные эффекты
    if battle_data.get('webbed', False):
        battle_log.append(f"🕸️ Ты все еще опутан паутиной и не можешь атаковать!")
        battle_data['webbed'] = False
        # Пропускаем ход игрока
    elif battle_data.get('stunned', False):
        battle_log.append(f"💫 Ты оглушен и не можешь действовать!")
        battle_data['stunned'] = False
        # Пропускаем ход игрока
    else:
        # Действие игрока
        if data == 'attack_physical':
            # Физическая атака
            damage, is_crit = calculate_damage(character, enemy, 'physical')
            
            # Учитываем уклонение врага
            if random.random() < enemy.get('dodge_chance', 0.08):
                battle_log.append(f"💨 {enemy['name']} уворачивается от твоей атаки!")
                damage = 0
            else:
                if is_crit:
                    battle_log.append(f"💥 *КРИТИЧЕСКИЙ УДАР!* Ты наносишь *{damage}* физического урона!")
                elif battle_data['enemy_defending']:
                    damage = max(1, damage // 2)
                    battle_log.append(f"🛡️ Враг в блоке! Ты наносишь *{damage}* физического урона.")
                else:
                    battle_log.append(f"⚔️ Ты наносишь *{damage}* физического урона!")
            
            enemy['health'] -= damage
            enemy['health'] = max(0, enemy['health'])
            battle_data['player_damage_dealt'] += damage
            
        elif data == 'attack_magic':
            # Магическая атака
            damage, is_crit = calculate_damage(character, enemy, 'magic')
            
            # Учитываем уклонение врага
            if random.random() < enemy.get('dodge_chance', 0.08):
                battle_log.append(f"💨 {enemy['name']} уворачивается от твоей магической атаки!")
                damage = 0
            else:
                if is_crit:
                    battle_log.append(f"💥 *КРИТИЧЕСКИЕ ЧАРЫ!* Ты наносишь *{damage}* магического урона!")
                elif battle_data['enemy_defending']:
                    damage = max(1, damage // 2)
                    battle_log.append(f"🛡️ Враг в блоке! Ты наносишь *{damage}* магического урона.")
                else:
                    battle_log.append(f"🔮 Ты наносишь *{damage}* магического урона!")
            
            enemy['health'] -= damage
            enemy['health'] = max(0, enemy['health'])
            battle_data['player_damage_dealt'] += damage
            
        elif data == 'defend':
            # Защита
            battle_data['player_defending'] = True
            battle_log.append(f"🛡️ Ты поднял щит! Урон снижен на 50%")
            
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
                    # Адаптивность: увеличение всех характеристик
                    battle_data['player_defending'] = True
                    battle_log.append(f"✨ *Адаптивность!* Затрачено {mana_cost} маны. Все характеристики временно увеличены на 5% и поднят щит!")
                    
                elif character['race'] == 'elf':
                    # Магический дар: урон зависит от интеллекта
                    base_magic = max(1, character['intelligence'] // 2)
                    damage = base_magic
                    if random.random() < 0.3:
                        damage = int(base_magic * 1.5)
                        battle_log.append(f"🏹 *КРИТИЧЕСКИЙ ВЫСТРЕЛ!* Затрачено {mana_cost} маны. Магия наносит *{damage}* урона!")
                        enemy['health'] -= damage
                    else:
                        battle_log.append(f"🏹 *Точный выстрел!* Затрачено {mana_cost} маны. Наносится *{damage}* урона!")
                        enemy['health'] -= damage
                    
                elif character['race'] == 'dwarf':
                    # Каменная кожа: лечение
                    heal_amount = character['max_health'] // 10 + random.randint(5, 15)
                    character['health'] = min(character['max_health'], character['health'] + heal_amount)
                    battle_data['player_defending'] = True
                    battle_log.append(f"🏔 *Каменная кожа!* Затрачено {mana_cost} маны. Восстановлено *{heal_amount}* HP и поднят щит!")
                    
                elif character['race'] == 'orc':
                    # Ярость: урон зависит от силы
                    damage = max(1, character['strength'] // 2) + random.randint(0, 5)
                    self_damage = random.randint(1, 5)
                    enemy['health'] -= damage
                    character['health'] -= self_damage
                    battle_log.append(f"🩸 *ЯРОСТЬ!* Затрачено {mana_cost} маны. Сокрушительный удар на *{damage}*, но ты ранил себя на *{self_damage}*.")
                
                battle_log.append(f"🔮 Осталось маны: {character['mana']}/{character['max_mana']}")
                
        elif data == 'use_health_potion':
            # Пытаемся использовать зелье здоровья
            inventory = get_inventory(user_id)
            health_potion = None
            
            # Ищем любое зелье здоровья
            for item in inventory:
                if 'health_potion' in item['item_key']:
                    health_potion = item
                    break
            
            if health_potion:
                success, message = use_item(
                    user_id=user_id,
                    item_key=health_potion['item_key'],
                    item_type=health_potion['item_type'],
                    item_name=health_potion['item_name'],
                    effect_amount=health_potion.get('effect_amount', 0)
                )
                
                if success:
                    # Обновляем здоровье персонажа в сессии боя
                    updated_character = get_character(user_id)
                    if updated_character:
                        old_health = character['health']
                        character['health'] = updated_character['health']
                        health_restored = character['health'] - old_health
                        battle_log.append(f"💊 Использовано {health_potion['item_name']}! Восстановлено *{health_restored}* HP!")
                else:
                    battle_log.append(f"❌ {message}")
            else:
                battle_log.append(f"❌ В инвентаре нет зелий здоровья!")
                
        elif data == 'use_mana_potion':
            # Пытаемся использовать зелье маны
            inventory = get_inventory(user_id)
            mana_potion = None
            
            # Ищем любое зелье маны
            for item in inventory:
                if 'mana_potion' in item['item_key']:
                    mana_potion = item
                    break
            
            if mana_potion:
                success, message = use_item(
                    user_id=user_id,
                    item_key=mana_potion['item_key'],
                    item_type=mana_potion['item_type'],
                    item_name=mana_potion['item_name'],
                    effect_amount=mana_potion.get('effect_amount', 0)
                )
                
                if success:
                    # Обновляем ману персонажа в сессии боя
                    updated_character = get_character(user_id)
                    if updated_character:
                        old_mana = character['mana']
                        character['mana'] = updated_character['mana']
                        mana_restored = character['mana'] - old_mana
                        battle_log.append(f"🔮 Использовано {mana_potion['item_name']}! Восстановлено *{mana_restored}* MP!")
                else:
                    battle_log.append(f"❌ {message}")
            else:
                battle_log.append(f"❌ В инвентаре нет зелий маны!")
                
        elif data == 'flee':
            # Шанс сбежать зависит от ловкости
            agility_bonus = character['agility'] // 5
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
        
        # Особое сообщение для боссов и мини-боссов
        if enemy.get('is_boss', False):
            battle_log.append(f"👑 *ВЕЛИКАЯ ПОБЕДА НАД БОССОМ!* 👑")
            battle_log.append(f"Ты победил {enemy['name']}!")
        elif enemy.get('is_mini_boss', False):
            battle_log.append(f"⭐ *ПОБЕДА НАД МИНИ-БОССОМ!* ⭐")
            battle_log.append(f"Ты победил {enemy['name']}!")
        else:
            battle_log.append("🏆 *ВЕЛИКАЯ ПОБЕДА!*")
            battle_log.append(f"Монстр {enemy['name']} повержен!")
        
        exp_gained = enemy['exp']
        gold_gained = enemy['gold']
        
        battle_log.append(f"💰 Трофеи: *{gold_gained}* золота")
        battle_log.append(f"🌟 Опыт: *{exp_gained}* XP")
        
        # Бонус за босса или мини-босса
        if enemy.get('is_boss', False):
            bonus_exp = exp_gained // 2
            bonus_gold = gold_gained // 2
            exp_gained += bonus_exp
            gold_gained += bonus_gold
            battle_log.append(f"👑 Бонус за босса: +{bonus_exp} XP, +{bonus_gold} золота")
        elif enemy.get('is_mini_boss', False):
            bonus_exp = exp_gained // 4
            bonus_gold = gold_gained // 4
            exp_gained += bonus_exp
            gold_gained += bonus_gold
            battle_log.append(f"⭐ Бонус за мини-босса: +{bonus_exp} XP, +{bonus_gold} золота")
        
        # Добавляем опыт и проверяем повышение уровня
        success, level_up, new_level, stat_points_gained = add_experience(user_id, exp_gained)
        
        if success and level_up:
            # Рассчитываем новый ранг
            new_rank = calculate_rank(new_level, character['experience'] + exp_gained)
            battle_log.append(f"🎯 *НОВЫЙ УРОВЕНЬ!* Ты достиг {new_level} уровня!")
            battle_log.append(f"✨ Получено *{stat_points_gained}* очков характеристик!")
            
            if new_rank != character.get('rank', 'E'):
                battle_log.append(f"🏆 *НОВЫЙ РАНГ!* Теперь ты {get_rank_icon(new_rank)} {new_rank}-ранг охотник!")
        
        # Обновляем статистику
        update_character_stats(
            user_id, 
            health=character['health'],
            mana=character['mana'],
            battle_wins=character.get('battle_wins', 0) + 1,
            gold=character['gold'] + gold_gained
        )
        
        # Добавляем золото
        add_gold(user_id, gold_gained)
        
        # Если это босс или мини-босс, увеличиваем счетчик
        if enemy.get('is_boss', False):
            increment_boss_kills(user_id, is_mini_boss=False)
        elif enemy.get('is_mini_boss', False):
            increment_boss_kills(user_id, is_mini_boss=True)
        
        # Логируем бой
        log_battle(
            user_id, 
            battle_data['enemy_type'], 
            enemy['name'],
            'победа', 
            battle_data['player_damage_dealt'], 
            battle_data['player_damage_taken'], 
            gold_gained, 
            exp_gained,
            enemy.get('is_boss', False),
            enemy.get('is_mini_boss', False)
        )
        
        del battle_sessions[user_id]
        
        await query.edit_message_text(
            text="\n".join(battle_log),
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(user_id)
        )
        return MAIN_MENU
    
    # Если враг еще жив, он делает ход
    if enemy['health'] > 0:
        # Проверяем отравление (урон в начале хода врага)
        if battle_data.get('poisoned', False):
            poison_damage = enemy['max_health'] // 20  # 5% от максимального здоровья
            enemy['health'] -= poison_damage
            battle_log.append(f"☠️ Враг страдает от яда и теряет *{poison_damage}* HP!")
            battle_data['poisoned'] = False
        
        # Обычная атака врага
        enemy_damage, is_dodged = calculate_enemy_damage(enemy, character)
        
        # Учитываем уклонение игрока
        if is_dodged:
            battle_log.append(f"💨 Ты уворачиваешься от атаки {enemy['name']}!")
            enemy_damage = 0
        else:
            # Защита игрока снижает урон
            if battle_data['player_defending']:
                enemy_damage = max(1, enemy_damage // 2)
                battle_log.append(f"🛡️ Твой блок поглотил 50% урона! Получено *{enemy_damage}* ед.")
            else:
                battle_log.append(f"💔 {enemy['name']} атаковал тебя на *{enemy_damage}* урона!")
        
        character['health'] -= enemy_damage
        character['health'] = max(0, character['health'])
        battle_data['player_damage_taken'] += enemy_damage
        battle_data['player_defending'] = False
        
        # Специальная атака врага
        special_damage, special_effect, status_effect = process_enemy_special_attack(enemy, character, battle_log)
        if special_damage > 0:
            character['health'] -= special_damage
            character['health'] = max(0, character['health'])
            battle_data['player_damage_taken'] += special_damage
        
        # Применяем статусные эффекты от специальных атак
        if status_effect == 'webbed':
            battle_data['webbed'] = True
        elif status_effect == 'stunned':
            battle_data['stunned'] = True
        elif status_effect == 'poisoned':
            battle_data['poisoned'] = True
    
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
        log_battle(
            user_id, 
            battle_data['enemy_type'], 
            enemy['name'],
            'поражение', 
            battle_data['player_damage_dealt'], 
            battle_data['player_damage_taken'], 0, 0,
            enemy.get('is_boss', False),
            enemy.get('is_mini_boss', False)
        )
        
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
    
    # Показываем статусные эффекты
    status_effects = []
    if battle_data.get('poisoned', False):
        status_effects.append("☠️ Отравлен")
    if battle_data.get('webbed', False):
        status_effects.append("🕸️ Опутан")
    if battle_data.get('stunned', False):
        status_effects.append("💫 Оглушен")
    
    status_text = ""
    if status_effects:
        status_text = f"📊 *Статус:* {', '.join(status_effects)}\n"
    
    turn_text = (
        f"⚔️ *Ход №{battle_data['turn']}*\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"👤 *ТЫ:* {player_health_bar}\n"
        f"🔮 *МАНА:* {player_mana_bar}\n"
        f"👿 *ВРАГ:* {enemy_health_bar}\n\n"
        f"{status_text}\n"
        f"{chr(10).join(battle_log)}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"⚡️ *Твои действия:*"
    )
    
    await query.edit_message_text(
        text=turn_text,
        parse_mode='Markdown',
        reply_markup=get_battle_action_keyboard()
    )
    return IN_BATTLE

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

# --- ОБРАБОТЧИКИ МАГАЗИНА ---

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
        "• Малое (+20 HP) — `40 золота`\n"
        "• Большое (+40 HP) — `75 золота`\n\n"
        "🔮 *ЭЛИКСИРЫ МАНЫ*\n"
        "• Малый (+15 MP) — `35 золота`\n"
        "• Большой (+30 MP) — `65 золота`\n\n"
        "⚔️ *Оружие и броня по рангам:*\n"
    )
    
    # Добавляем предметы по рангам
    rank_order = ['E', 'D', 'C', 'B', 'A', 'S']
    player_rank_index = rank_order.index(rank)
    
    for rank_key, item_key in [('D', 'rank_d_weapon'), ('C', 'rank_c_armor'), ('C', 'ring_of_agility'), ('B', 'rank_b_artifact')]:
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
        item_map = {
            'buy_small_health_potion': 'small_health_potion',
            'buy_large_health_potion': 'large_health_potion', 
            'buy_small_mana_potion': 'small_mana_potion',
            'buy_large_mana_potion': 'large_mana_potion',
            'buy_0': 'rank_d_weapon',
            'buy_1': 'rank_c_armor',
            'buy_2': 'rank_b_artifact',
            'buy_ring_of_agility': 'ring_of_agility'
        }
        
        if data not in item_map:
            await query.answer("❌ Неизвестный товар!", show_alert=True)
            return SHOP_MENU
        
        item_key = item_map[data]
        
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
            effect_amount=item.get('effect', 0)
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
    
    elif data.startswith('buy_info_'):
        # Информационные кнопки о требованиях ранга
        await query.answer("❌ У тебя недостаточно высокий ранг для этого предмета!", show_alert=True)
        return SHOP_MENU

# --- ОБРАБОТЧИКИ СТАТИСТИКИ И ТОПА ---

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
    
    # Получаем прогресс опыта
    current_xp, max_xp, percent = get_xp_progress(character['level'], character['experience'])
    
    rank = character.get('rank', 'E')
    rank_icon = get_rank_icon(rank)
    
    # Рассчитываем боевые параметры
    dodge_chance = calculate_player_dodge_chance(character['agility'])
    crit_chance = calculate_crit_chance(character['agility'])
    
    stats_text = (
        f"🏆 *ЗАЛ СЛАВЫ: {character['character_name']}*\n"
        f"{rank_icon} *Ранг:* {rank}-ранг\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⭐ *Уровень:* `{character['level']}`\n"
        f"✨ *Опыт:* `{character['experience']}` XP\n"
        f"📊 *Прогресс на уровне:* `{int(current_xp)}/{max_xp}` ({percent:.1%})\n"
        f"{get_xp_bar(character['level'], character['experience'], length=15)}\n\n"
        f"💪 *Характеристики:*\n"
        f"Сила: `{character['strength']}` | "
        f"Ловкость: `{character['agility']}` | "
        f"Интеллект: `{character['intelligence']}` | "
        f"Живучесть: `{character['vitality']}`\n\n"
        f"⚔️ *Боевые параметры:*\n"
        f"🛡️ Физ. защита: `{character.get('physical_resistance', 0)*100:.1f}%`\n"
        f"🔮 Маг. защита: `{character.get('magic_resistance', 0)*100:.1f}%`\n"
        f"🏹 Уклонение: `{dodge_chance*100:.1f}%`\n"
        f"💥 Крит. шанс: `{crit_chance*100:.1f}%`\n\n"
        f"❤️ *Здоровье:* `{character['health']}/{character['max_health']}`\n"
        f"{get_health_bar(character['health'], character['max_health'], length=15)}\n\n"
        f"🔮 *Мана:* `{character['mana']}/{character['max_mana']}`\n"
        f"{get_mana_bar(character['mana'], character['max_mana'], length=10)}\n\n"
        f"💰 *Богатство:* `{character['gold']}` золотых\n\n"
        f"⚔️ *Боевая сводка:*\n"
        f"✅ Побед: `{character.get('battle_wins', 0)}`\n"
        f"❌ Поражений: `{character.get('battle_losses', 0)}`\n"
        f"📉 Всего битв: `{total_battles}`\n"
        f"📈 Эффективность: `{win_rate:.1f}%`\n"
        f"⭐ Убито мини-боссов: `{character.get('mini_boss_kills', 0)}`\n"
        f"👑 Убито боссов: `{character.get('boss_kills', 0)}`\n\n"
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
                f"   ⚔️ {player.get('battle_wins', 0)}/{total_player_battles} побед ({win_rate_player:.1f}%)\n"
                f"   👑 Боссов: {player.get('boss_kills', 0)} | ⭐ Мини-боссов: {player.get('mini_boss_kills', 0)}\n"
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
    top_players = get_top_players(10)
    
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
        all_players = get_top_players(100)
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
            f"   👑 Боссов: {player.get('boss_kills', 0)} | ⭐ Мини-боссов: {player.get('mini_boss_kills', 0)}\n"
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
    top_text += "• Повышай уровень и ранг\n• Побеждай в боях, особенно боссов\n• Накопай золота\n• Стань легендой!"
    
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

🏆 **УСЛОЖНЕННАЯ СИСТЕМА РАНГОВ:**
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

📈 **УСЛОЖНЕННАЯ СИСТЕМА ПРОКАЧКИ:**
• За каждый уровень: *+2 очка характеристик* (вместо 3)
• Опыт для уровня: уровень × 150 (вместо 100)
• Распределяй между:
  💪 *СИЛА* - Физ. урон в ближнем бою (сила ÷ 3)
  🏹 *ЛОВКОСТЬ* - Шанс уклонения (до 25%) и критического удара (до 15%)
  🧠 *ИНТЕЛЛЕКТ* - Магический урон (интеллект ÷ 3) и мана
  ❤️ *ЖИВУЧЕСТЬ* - Максимальное здоровье

🎒 **Инвентарь:**
• Нажми на кнопку 🎒 в главном меню
• Используй зелья для восстановления здоровья и маны
• Все купленные предметы хранятся здесь

💊 **Магазин:**
• Малое зелье здоровья (20 HP) - 40💰
• Большое зелье здоровья (40 HP) - 75💰
• Малое зелье маны (15 MP) - 35💰
• Большое зелье маны (30 MP) - 65💰
• Оружие и броня доступны по мере повышения ранга

⚔️ **УСИЛЕННАЯ СИСТЕМА ВРАГОВ:**
• Враги усиливаются с твоим уровнем (+15% за уровень)
• В каждой локации есть обычные враги, мини-боссы и боссы
• Мини-боссы и боссы дают больше опыта и золота
• У врагов есть особые способности (яд, лечение, призыв и т.д.)
• Враги имеют физическое и магическое сопротивление
• Враги имеют повышенные шансы уклонения и сопротивления

🛡️ **УСЛОЖНЕННАЯ СИСТЕМА БОЯ:**
• *Физический урон* - зависит от силы ÷ 3, сильно снижается физическим сопротивлением
• *Магический урон* - зависит от интеллекта ÷ 3, сильно снижается магическим сопротивлением
• *Шанс уклонения* - зависит от ловкости (до 25%)
• *Шанс крита* - зависит от ловкости (до 15%), множитель ×1.5
• *Сопротивления* - сильно уменьшают получаемый урон соответствующего типа

🗡 **Тактика боя:**
• ⚔️ *Физическая атака* - Удар оружием (зависит от силы)
• 🔮 *Магическая атака* - Магический удар (зависит от интеллекта)
• 🛡️ *Защита* - Снижает урон на 50%
• ✨ *Способность* - Уникальный навык твоей расы (тратит ману)
• 💊 *Зелье* - Использование зелья из инвентаря
• 🏃 *Сбежать* - Шанс 50% покинуть бой

⚡ **Советы против боссов:**
1. _Убедись, что у тебя достаточно зелий!_
2. Используй расовую способность в ключевые моменты
3. Не забывай блокировать атаки боссов
4. Боссы имеют особые способности - будь готов к неожиданностям
5. Победа над боссом даст тебе огромные награды

⚠️ *ВНИМАНИЕ: Игра значительно усложнена!*
• Прокачка занимает в 2-3 раза больше времени
• Бои требуют тщательной тактики и подготовки
• Статистики героев не будут зашкаливать
• Каждая победа будет действительно ценной

_Создай свою легенду, но будь готов к трудностям!_ 🏹
"""
    await query.edit_message_text(
        text=help_text,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard(query.from_user.id)
    )

# --- ОСНОВНАЯ ФУНКЦИЯ ---

def main():
    """Запуск бота"""
    print("🚀 Запуск RPG бота с УСЛОЖНЕННОЙ СИСТЕМОЙ...")
    
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
                    CallbackQueryHandler(battle_action_handler, pattern='^(attack_physical|attack_magic|defend|ability|use_health_potion|use_mana_potion|flee)$')
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
        
        # Устанавливаем настройки для предотвращения конфликтов
        application.run_polling(
            drop_pending_updates=True,
            close_loop=False,
            allowed_updates=Update.ALL_TYPES,
            poll_interval=1.0
        )
        
    except Exception as e:
        print(f"❌ Критическая ошибка при запуске бота: {e}")
        print("\nВозможные решения:")
        print("1. Проверьте токен бота в Railway Variables")
        print("2. Убедитесь, что запущен только один экземпляр бота")
        print("3. Проверьте подключение к интернету")
        print("4. Остановите все предыдущие экземпляры бота в Railway Dashboard")

if __name__ == '__main__':
    main()
