import os
import logging
import random
import html
from datetime import datetime, time
from telegram.error import BadRequest
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    ContextTypes, ConversationHandler, MessageHandler, filters
)
import database

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния
CHOOSE_RACE, ENTER_NAME, MAIN_MENU, BATTLE_MENU, IN_BATTLE, SHOP_MENU, LEVEL_UP, INVENTORY_MENU, CRAFT_MENU = range(9)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
battle_sessions = {}

# --- ВИЗУАЛ (DARK FANTASY) ---
IMAGE_URLS = {
    # Расы
    'human': 'https://i126.fastpic.org/thumb/2026/0130/2c/_d2515d33e45fa7ffb5246cacabdaba2c.jpeg',
    'elf': 'https://i126.fastpic.org/thumb/2026/0130/81/_d3d94be5aa45b9239aeb5adc41443081.jpeg',
    'dwarf': 'https://i126.fastpic.org/thumb/2026/0130/5b/_c188fac4eb6d205bd9fc0486c9b9355b.jpeg',
    'orc': 'https://i126.fastpic.org/thumb/2026/0130/20/_b8c1f666bd21bb415e8fb35145eb3e20.jpeg',
    # Враги
    'wolf': 'https://i.pinimg.com/736x/9f/8e/25/9f8e2507aceaa217060d249c308e2a13.jpg',
    'goblin': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRv_JCAj5bxf0VGHSS_-brpxVZfOz-T-CUR7w&s',
    'slime': 'https://papik.pro/uploads/posts/2023-02/1676176492_papik-pro-p-risunok-sliz-1.jpg',
    'hot_goblin': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSXgGesfRif8L7MrmHFJruGNuxRWf3G_SFgTw&s', 
    'zombie': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQRBEAcmeuf4tt0xnFUG1E8wcvZlSkLQcZkUw&s',
    'skeleton': 'https://img.freepik.com/free-photo/skeleton-warrior_23-2150911306.jpg',
    'mage': 'https://abrakadabra.fun/uploads/posts/2022-01/1642490542_3-abrakadabra-fun-p-temnii-mag-art-5.jpg',
    'vampire': 'https://img.freepik.com/free-photo/vampire_23-2150762308.jpg',
    'knight': 'https://i.pinimg.com/736x/93/84/9f/93849fa5c577756a346cd6c4172b384d.jpg',
    'demon': 'https://img.freepik.com/free-photo/demon_23-2150762325.jpg',
    'lich': 'https://img.freepik.com/free-photo/lich_23-2150911246.jpg',
    'dragon': 'https://abrakadabra.fun/uploads/posts/2022-03/1646721873_1-abrakadabra-fun-p-pauk-fantezi-art-1.jpg',
    'dragon_ancient': 'https://img.freepik.com/free-photo/ancient-dragon_23-2150762338.jpg',
    'titan': 'https://img.freepik.com/free-photo/titan_23-2150911270.jpg',
    'fallen_god': 'https://img.freepik.com/free-photo/fallen-god_23-2150911258.jpg',
    # Локации и интерфейс
    'village': 'https://img.freepik.com/premium-photo/tavern-like-game_808092-1770.jpg',
    'forest': 'https://img.freepik.com/premium-photo/ancient-forest-ai-generated_1127-13930.jpg',
    'castle': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTrAoGzKjgZxurLbxZ_Dyhtkm1gBqMUMtA87w&s',
    'dungeon': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSTZd9YHDcPOGmD8ezmHB0xD-HfA9O7OpgVyA&s',
    'training_camp': 'https://img1.liveinternet.ru/images/attach/b/2/1/726/1726838_full0011.jpg',
    'hell_gate': 'https://abrakadabra.fun/uploads/posts/2022-01/1642490542_3-abrakadabra-fun-p-temnii-mag-art-5.jpg',
    'throne_god': 'https://abrakadabra.fun/uploads/posts/2022-03/1646721873_1-abrakadabra-fun-p-pauk-fantezi-art-1.jpg',
    'shop': 'https://img.freepik.com/premium-photo/medieval-market-stall_23-2150911310.jpg',
    'inventory': 'https://freepngimg.com/thumb/backpack/22202-6-backpack-painting.png',
    'craft': 'https://img.freepik.com/free-photo/blacksmith-workshop_23-2150911315.jpg'
}

# --- НОВАЯ БАЗА ПРЕДМЕТОВ ---
ITEMS_DB = {
    # ЕДА И ЗЕЛЬЯ
    'bread': {'name': '🍞 Хлеб', 'price': 15, 'type': 'food', 'effect': 10, 'cat': 'food', 'rank': 'E'},
    'apple': {'name': '🍎 Яблоко', 'price': 20, 'type': 'food', 'effect': 15, 'cat': 'food', 'rank': 'E'},
    'meat_stew': {'name': '🍲 Рагу', 'price': 45, 'type': 'food', 'effect': 35, 'cat': 'food', 'rank': 'D'},
    'roast_boar': {'name': '🍖 Кабан', 'price': 80, 'type': 'food', 'effect': 60, 'cat': 'food', 'rank': 'C'},
    'elven_wine': {'name': '🍷 Вино', 'price': 150, 'type': 'food', 'effect': 100, 'cat': 'food', 'rank': 'B'},
    'small_hp': {'name': '🧪 Малое зелье HP', 'price': 50, 'type': 'potion', 'effect': 30, 'cat': 'food', 'rank': 'E'},
    'medium_hp': {'name': '🧪 Зелье HP', 'price': 100, 'type': 'potion', 'effect': 70, 'cat': 'food', 'rank': 'D'},
    'large_hp': {'name': '🧪 Эликсир HP', 'price': 250, 'type': 'potion', 'effect': 150, 'cat': 'food', 'rank': 'B'},
    'small_mp': {'name': '🔮 Малое зелье MP', 'price': 40, 'type': 'potion', 'effect': 20, 'cat': 'food', 'rank': 'E'},

    # ОРУЖИЕ (cat: weapon)
    'rusty_sword': {'name': '⚔️ Ржавый меч (+2 STR)', 'price': 150, 'type': 'weapon', 'effect': 2, 'cat': 'weapon', 'rank': 'E'},
    'iron_axe': {'name': '🪓 Топор (+5 STR)', 'price': 400, 'type': 'weapon', 'effect': 5, 'cat': 'weapon', 'rank': 'D'},
    'steel_saber': {'name': '⚔️ Сабля (+10 STR)', 'price': 900, 'type': 'weapon', 'effect': 10, 'cat': 'weapon', 'rank': 'C'},
    'dark_blade': {'name': '🗡️ Клинок Тьмы (+18 STR)', 'price': 2500, 'type': 'weapon', 'effect': 18, 'cat': 'weapon', 'rank': 'B'},
    'demon_slayer': {'name': '🔥 Убийца Демонов (+30 STR)', 'price': 6000, 'type': 'weapon', 'effect': 30, 'cat': 'weapon', 'rank': 'A'},

    # БРОНЯ (cat: armor)
    'leather_vest': {'name': '🛡️ Кожанка (+3 HP)', 'price': 120, 'type': 'armor', 'effect': 3, 'cat': 'armor', 'rank': 'E'},
    'chainmail': {'name': '🛡️ Кольчуга (+8 HP)', 'price': 350, 'type': 'armor', 'effect': 8, 'cat': 'armor', 'rank': 'D'},
    'plate_armor': {'name': '🛡️ Латы (+15 HP)', 'price': 850, 'type': 'armor', 'effect': 15, 'cat': 'armor', 'rank': 'C'},
    'mithril_armor': {'name': '💠 Мифрил (+25 HP)', 'price': 2200, 'type': 'armor', 'effect': 25, 'cat': 'armor', 'rank': 'B'},

    # АКСЕССУАРЫ (cat: acc)
    'wooden_ring': {'name': '💍 Кольцо (+2 INT)', 'price': 200, 'type': 'artifact', 'effect': 2, 'cat': 'acc', 'rank': 'E'},
    'silver_amulet': {'name': '🧿 Амулет (+5 INT)', 'price': 500, 'type': 'artifact', 'effect': 5, 'cat': 'acc', 'rank': 'D'},
    'gold_ring': {'name': '💍 Перстень (+10 INT)', 'price': 1200, 'type': 'artifact', 'effect': 10, 'cat': 'acc', 'rank': 'C'},
    'skull_necklace': {'name': '💀 Ожерелье (+20 INT)', 'price': 3000, 'type': 'artifact', 'effect': 20, 'cat': 'acc', 'rank': 'B'},

    # РЕСУРСЫ (cat: mat)
    'wolf_pelt': {'name': '🐺 Шкура волка', 'price': 5, 'type': 'material', 'cat': 'mat', 'rank': 'E'},
    'goblin_ear': {'name': '👂 Ухо гоблина', 'price': 8, 'type': 'material', 'cat': 'mat', 'rank': 'E'},
    'slime_goo': {'name': '🟢 Слизь', 'price': 6, 'type': 'material', 'cat': 'mat', 'rank': 'E'},
    'iron_ore': {'name': '🪨 Руда', 'price': 15, 'type': 'material', 'cat': 'mat', 'rank': 'D'},
    'spider_silk': {'name': '🕸️ Шелк', 'price': 20, 'type': 'material', 'cat': 'mat', 'rank': 'D'},
    'bone_dust': {'name': '💀 Пыль костей', 'price': 25, 'type': 'material', 'cat': 'mat', 'rank': 'C'},
    'demon_horn': {'name': '😈 Рог демона', 'price': 100, 'type': 'material', 'cat': 'mat', 'rank': 'A'}
}

# --- РЕЦЕПТЫ КРАФТА ---
CRAFT_RECIPES = {
    'small_hp': {'result': 'small_hp', 'cost': 10, 'mats': {'slime_goo': 2, 'wolf_pelt': 1}},
    'leather_vest': {'result': 'leather_vest', 'cost': 50, 'mats': {'wolf_pelt': 5}},
    'rusty_sword': {'result': 'rusty_sword', 'cost': 60, 'mats': {'goblin_ear': 5, 'wolf_pelt': 2}},
    'medium_hp': {'result': 'medium_hp', 'cost': 30, 'mats': {'small_hp': 2, 'spider_silk': 1}},
    'iron_axe': {'result': 'iron_axe', 'cost': 150, 'mats': {'iron_ore': 5, 'wolf_pelt': 3}},
    'chainmail': {'result': 'chainmail', 'cost': 120, 'mats': {'iron_ore': 8, 'spider_silk': 4}},
    'dark_blade': {'result': 'dark_blade', 'cost': 1000, 'mats': {'demon_horn': 2, 'bone_dust': 10, 'iron_ore': 20}}
}

# --- БЕСТИАРИЙ С ЛУТОМ ---
BASE_ENEMIES = {
    # --- РАНГ E ---
    'wolf': {'name': '🐺 Волк', 'base_health': 30, 'base_min_physical_damage': 4, 'base_max_physical_damage': 7, 'base_min_magic_damage': 0, 'base_max_magic_damage': 0, 'base_exp': 12, 'base_gold': 8, 'rank': 'E', 'description': 'Бешеный зверь.', 'image': IMAGE_URLS['wolf'], 'difficulty': 'easy', 'abilities': ['basic_attack'], 'damage_type': 'physical', 'dodge_chance': 0.08, 'drops': ['wolf_pelt', 'apple']},
    'goblin': {'name': '👹 Гоблин', 'base_health': 35, 'base_min_physical_damage': 5, 'base_max_physical_damage': 9, 'base_min_magic_damage': 0, 'base_max_magic_damage': 0, 'base_exp': 16, 'base_gold': 12, 'rank': 'E', 'description': 'Мелкий вор.', 'image': IMAGE_URLS['goblin'], 'difficulty': 'easy', 'abilities': ['basic_attack', 'dirty_trick'], 'damage_type': 'physical', 'dodge_chance': 0.12, 'drops': ['goblin_ear', 'bread']},
    'slime': {'name': '🟢 Слизь', 'base_health': 40, 'base_min_physical_damage': 2, 'base_max_physical_damage': 7, 'base_min_magic_damage': 1, 'base_max_magic_damage': 4, 'base_exp': 10, 'base_gold': 7, 'rank': 'E', 'description': 'Едкая жижа.', 'image': IMAGE_URLS['slime'], 'difficulty': 'easy', 'abilities': ['basic_attack', 'poison_spit'], 'damage_type': 'mixed', 'dodge_chance': 0.02, 'drops': ['slime_goo']},
    'goblin_elite': {'name': '👹 Вожак Гоблинов', 'base_health': 80, 'base_min_physical_damage': 10, 'base_max_physical_damage': 18, 'base_min_magic_damage': 0, 'base_max_magic_damage': 0, 'base_exp': 35, 'base_gold': 25, 'rank': 'E', 'description': 'Лидер банды.', 'image': IMAGE_URLS['hot_goblin'], 'difficulty': 'mini_boss', 'abilities': ['basic_attack', 'power_strike'], 'damage_type': 'physical', 'dodge_chance': 0.15, 'drops': ['goblin_ear', 'iron_ore']},
    'training_master': {'name': '⚔️ Ветеран', 'base_health': 110, 'base_min_physical_damage': 12, 'base_max_physical_damage': 22, 'base_min_magic_damage': 0, 'base_max_magic_damage': 0, 'base_exp': 50, 'base_gold': 40, 'rank': 'E', 'description': 'Безумный воин.', 'image': IMAGE_URLS['knight'], 'difficulty': 'boss', 'abilities': ['basic_attack', 'whirlwind_strike'], 'damage_type': 'physical', 'dodge_chance': 0.20, 'drops': ['iron_ore', 'small_hp']},

    # --- РАНГ D ---
    'forest_spider': {'name': '🕷️ Паук', 'base_health': 60, 'base_min_physical_damage': 7, 'base_max_physical_damage': 14, 'base_min_magic_damage': 0, 'base_max_magic_damage': 0, 'base_exp': 25, 'base_gold': 16, 'rank': 'D', 'description': 'Ткач смерти.', 'image': 'https://img.freepik.com/free-photo/giant-spider_23-2150911307.jpg', 'difficulty': 'medium', 'abilities': ['basic_attack', 'web_shot'], 'damage_type': 'physical', 'dodge_chance': 0.15, 'drops': ['spider_silk']},
    'ghost': {'name': '👻 Призрак', 'base_health': 50, 'base_min_physical_damage': 6, 'base_max_physical_damage': 12, 'base_min_magic_damage': 3, 'base_max_magic_damage': 8, 'base_exp': 28, 'base_gold': 20, 'rank': 'D', 'description': 'Нематериальный дух.', 'image': 'https://img.freepik.com/free-photo/ghost_23-2150762306.jpg', 'difficulty': 'medium', 'abilities': ['basic_attack', 'fear'], 'damage_type': 'magic', 'dodge_chance': 0.25, 'drops': ['small_mp']},
    'wild_boar': {'name': '🐗 Кабан', 'base_health': 85, 'base_min_physical_damage': 10, 'base_max_physical_damage': 20, 'base_min_magic_damage': 0, 'base_max_magic_damage': 0, 'base_exp': 32, 'base_gold': 24, 'rank': 'D', 'description': 'Клыкастая угроза.', 'image': 'https://img.freepik.com/free-photo/wild-boar_23-2150911295.jpg', 'difficulty': 'medium', 'abilities': ['basic_attack', 'charge'], 'damage_type': 'physical', 'dodge_chance': 0.08, 'drops': ['wolf_pelt', 'meat_stew']},
    'forest_troll': {'name': '🌳 Тролль', 'base_health': 110, 'base_min_physical_damage': 15, 'base_max_physical_damage': 23, 'base_min_magic_damage': 0, 'base_max_magic_damage': 0, 'base_exp': 48, 'base_gold': 36, 'rank': 'D', 'description': 'Регенерирующий гигант.', 'image': 'https://img.freepik.com/free-photo/troll_23-2150911292.jpg', 'difficulty': 'mini_boss', 'abilities': ['basic_attack', 'regeneration'], 'damage_type': 'physical', 'dodge_chance': 0.12, 'drops': ['iron_ore', 'roast_boar']},
    'forest_guardian': {'name': '🌳 Энт', 'base_health': 150, 'base_min_physical_damage': 13, 'base_max_physical_damage': 25, 'base_min_magic_damage': 7, 'base_max_magic_damage': 13, 'base_exp': 80, 'base_gold': 64, 'rank': 'D', 'description': 'Древний страж.', 'image': 'https://img.freepik.com/free-photo/treant_23-2150911290.jpg', 'difficulty': 'boss', 'abilities': ['basic_attack', 'root_grab'], 'damage_type': 'mixed', 'dodge_chance': 0.08, 'drops': ['medium_hp', 'wooden_ring']},

    # --- РАНГ C ---
    'skeleton_warrior': {'name': '💀 Скелет', 'base_health': 100, 'base_min_physical_damage': 13, 'base_max_physical_damage': 23, 'base_min_magic_damage': 0, 'base_max_magic_damage': 0, 'base_exp': 48, 'base_gold': 32, 'rank': 'C', 'description': 'Костяной воин.', 'image': IMAGE_URLS['skeleton'], 'difficulty': 'hard', 'abilities': ['basic_attack', 'shield_bash'], 'damage_type': 'physical', 'dodge_chance': 0.12, 'drops': ['bone_dust']},
    'ghoul': {'name': '🧟 Гуль', 'base_health': 115, 'base_min_physical_damage': 12, 'base_max_physical_damage': 22, 'base_min_magic_damage': 0, 'base_max_magic_damage': 0, 'base_exp': 52, 'base_gold': 36, 'rank': 'C', 'description': 'Трупоед.', 'image': IMAGE_URLS['zombie'], 'difficulty': 'hard', 'abilities': ['basic_attack', 'life_drain'], 'damage_type': 'physical', 'dodge_chance': 0.10, 'drops': ['bone_dust', 'meat_stew']},
    'dark_priest': {'name': '🕯️ Еретик', 'base_health': 90, 'base_min_physical_damage': 7, 'base_max_physical_damage': 13, 'base_min_magic_damage': 15, 'base_max_magic_damage': 28, 'base_exp': 60, 'base_gold': 44, 'rank': 'C', 'description': 'Темный маг.', 'image': IMAGE_URLS['mage'], 'difficulty': 'hard', 'abilities': ['basic_attack', 'dark_bolt'], 'damage_type': 'magic', 'dodge_chance': 0.15, 'drops': ['small_mp', 'silver_amulet']},
    'crypt_keeper': {'name': '💀 Некромант', 'base_health': 140, 'base_min_physical_damage': 15, 'base_max_physical_damage': 25, 'base_min_magic_damage': 10, 'base_max_magic_damage': 19, 'base_exp': 72, 'base_gold': 56, 'rank': 'C', 'description': 'Хозяин склепа.', 'image': 'https://img.freepik.com/free-photo/necromancer_23-2150911284.jpg', 'difficulty': 'mini_boss', 'abilities': ['basic_attack', 'raise_dead'], 'damage_type': 'mixed', 'dodge_chance': 0.18, 'drops': ['bone_dust', 'medium_hp']},
    'catacomb_lord': {'name': '👑 Лич', 'base_health': 225, 'base_min_physical_damage': 19, 'base_max_physical_damage': 32, 'base_min_magic_damage': 13, 'base_max_magic_damage': 23, 'base_exp': 160, 'base_gold': 120, 'rank': 'C', 'description': 'Король мертвых.', 'image': 'https://img.freepik.com/free-photo/skeleton-king_23-2150911291.jpg', 'difficulty': 'boss', 'abilities': ['basic_attack', 'royal_decree'], 'damage_type': 'mixed', 'dodge_chance': 0.15, 'drops': ['large_hp', 'gold_ring']},

    # --- РАНГ B ---
    'knight': {'name': '⚔️ Темный Рыцарь', 'base_health': 150, 'base_min_physical_damage': 19, 'base_max_physical_damage': 32, 'base_min_magic_damage': 0, 'base_max_magic_damage': 0, 'base_exp': 80, 'base_gold': 64, 'rank': 'B', 'description': 'Падший воин.', 'image': IMAGE_URLS['knight'], 'difficulty': 'very_hard', 'abilities': ['basic_attack', 'shield_wall'], 'damage_type': 'physical', 'dodge_chance': 0.20, 'drops': ['iron_ore', 'medium_hp']},
    'vampire': {'name': '🦇 Носферату', 'base_health': 125, 'base_min_physical_damage': 23, 'base_max_physical_damage': 35, 'base_min_magic_damage': 0, 'base_max_magic_damage': 0, 'base_exp': 96, 'base_gold': 80, 'rank': 'B', 'description': 'Древний кровопийца.', 'image': IMAGE_URLS['vampire'], 'difficulty': 'very_hard', 'abilities': ['basic_attack', 'blood_drain'], 'damage_type': 'physical', 'dodge_chance': 0.25, 'drops': ['elven_wine']},
    'warlock': {'name': '🔮 Чернокнижник', 'base_health': 115, 'base_min_physical_damage': 7, 'base_max_physical_damage': 13, 'base_min_magic_damage': 25, 'base_max_magic_damage': 40, 'base_exp': 104, 'base_gold': 88, 'rank': 'B', 'description': 'Призыватель демонов.', 'image': IMAGE_URLS['mage'], 'difficulty': 'very_hard', 'abilities': ['basic_attack', 'shadow_bolt'], 'damage_type': 'magic', 'dodge_chance': 0.18, 'drops': ['demon_horn', 'small_mp']},
    'death_knight': {'name': '💀 Рыцарь Смерти', 'base_health': 190, 'base_min_physical_damage': 25, 'base_max_physical_damage': 38, 'base_min_magic_damage': 13, 'base_max_magic_damage': 23, 'base_exp': 144, 'base_gold': 112, 'rank': 'B', 'description': 'Генерал мертвых.', 'image': 'https://img.freepik.com/free-photo/death-knight_23-2150911264.jpg', 'difficulty': 'mini_boss', 'abilities': ['basic_attack', 'death_coil'], 'damage_type': 'mixed', 'dodge_chance': 0.23, 'drops': ['plate_armor', 'dark_blade']},
    'castle_overlord': {'name': '🏰 Император', 'base_health': 315, 'base_min_physical_damage': 25, 'base_max_physical_damage': 44, 'base_min_magic_damage': 19, 'base_max_magic_damage': 32, 'base_exp': 280, 'base_gold': 200, 'rank': 'B', 'description': 'Безумный тиран.', 'image': 'https://img.freepik.com/free-photo/dark-king_23-2150911261.jpg', 'difficulty': 'boss', 'abilities': ['basic_attack', 'royal_command'], 'damage_type': 'mixed', 'dodge_chance': 0.20, 'drops': ['skull_necklace', 'large_hp']},

    # --- РАНГ A ---
    'demon': {'name': '😈 Демон', 'base_health': 190, 'base_min_physical_damage': 32, 'base_max_physical_damage': 50, 'base_min_magic_damage': 13, 'base_max_magic_damage': 25, 'base_exp': 160, 'base_gold': 120, 'rank': 'A', 'description': 'Отродье бездны.', 'image': IMAGE_URLS['demon'], 'difficulty': 'extreme', 'abilities': ['basic_attack', 'hellfire'], 'damage_type': 'mixed', 'dodge_chance': 0.25, 'drops': ['demon_horn']},
    'pit_fiend': {'name': '😈 Архидемон', 'base_health': 275, 'base_min_physical_damage': 35, 'base_max_physical_damage': 53, 'base_min_magic_damage': 25, 'base_max_magic_damage': 40, 'base_exp': 240, 'base_gold': 176, 'rank': 'A', 'description': 'Лорд преисподней.', 'image': 'https://img.freepik.com/free-photo/pit-fiend_23-2150911286.jpg', 'difficulty': 'mini_boss', 'abilities': ['basic_attack', 'summon_demons'], 'damage_type': 'mixed', 'dodge_chance': 0.28, 'drops': ['demon_horn', 'large_hp']},
    'demon_general': {'name': '😈 Генерал Ада', 'base_health': 440, 'base_min_physical_damage': 38, 'base_max_physical_damage': 63, 'base_min_magic_damage': 32, 'base_max_magic_damage': 50, 'base_exp': 400, 'base_gold': 280, 'rank': 'A', 'description': 'Правая рука Дьявола.', 'image': 'https://img.freepik.com/free-photo/demon-general_23-2150911263.jpg', 'difficulty': 'boss', 'abilities': ['basic_attack', 'army_command'], 'damage_type': 'mixed', 'dodge_chance': 0.25, 'drops': ['demon_slayer', 'mithril_armor']},

    # --- РАНГ S ---
    'dragon_ancient': {'name': '🐉 Дракон', 'base_health': 500, 'base_min_physical_damage': 44, 'base_max_physical_damage': 69, 'base_min_magic_damage': 32, 'base_max_magic_damage': 50, 'base_exp': 480, 'base_gold': 320, 'rank': 'S', 'description': 'Древнее зло.', 'image': IMAGE_URLS['dragon_ancient'], 'difficulty': 'legendary', 'abilities': ['basic_attack', 'dragon_breath'], 'damage_type': 'mixed', 'dodge_chance': 0.30, 'drops': ['large_hp']},
    'final_god': {'name': '⚡ Бог Разрушения', 'base_health': 1250, 'base_min_physical_damage': 63, 'base_max_physical_damage': 100, 'base_min_magic_damage': 50, 'base_max_magic_damage': 88, 'base_exp': 1200, 'base_gold': 800, 'rank': 'S', 'description': 'Конец времен.', 'image': IMAGE_URLS['fallen_god'], 'difficulty': 'boss', 'abilities': ['basic_attack', 'divine_judgment'], 'damage_type': 'mixed', 'dodge_chance': 0.45, 'drops': ['elven_wine', 'large_hp']}
}

# Локации
LOCATIONS = {
    'E': {'name': '🎪 Тренировочный лагерь', 'description': 'Начинай свой путь здесь. Враги слабые, но хороши для тренировки.', 'enemies': ['wolf', 'goblin', 'slime', 'goblin_elite', 'training_master'], 'mini_boss': 'goblin_elite', 'boss': 'training_master', 'image': IMAGE_URLS['training_camp'], 'min_level': 1, 'max_level': 15, 'difficulty': 'easy'},
    'D': {'name': '🌲 Лес призраков', 'description': 'Лес наполнен низкоуровневыми монстрами. Подходит для охотников D-ранга.', 'enemies': ['forest_spider', 'ghost', 'wild_boar', 'forest_troll', 'forest_guardian'], 'mini_boss': 'forest_troll', 'boss': 'forest_guardian', 'image': IMAGE_URLS['forest'], 'min_level': 10, 'max_level': 25, 'difficulty': 'medium'},
    'C': {'name': '🪦 Заброшенные катакомбы', 'description': 'Катакомбы наполнены опасными существами. Требует навыков C-ранга.', 'enemies': ['skeleton_warrior', 'ghoul', 'dark_priest', 'crypt_keeper', 'catacomb_lord'], 'mini_boss': 'crypt_keeper', 'boss': 'catacomb_lord', 'image': IMAGE_URLS['dungeon'], 'min_level': 20, 'max_level': 35, 'difficulty': 'hard'},
    'B': {'name': '🏰 Руины древнего замка', 'description': 'Замок охраняют могущественные существа. Только для охотников B-ранга.', 'enemies': ['knight', 'vampire', 'warlock', 'death_knight', 'castle_overlord'], 'mini_boss': 'death_knight', 'boss': 'castle_overlord', 'image': IMAGE_URLS['castle'], 'min_level': 30, 'max_level': 45, 'difficulty': 'very_hard'},
    'A': {'name': '🌋 Врата в преисподнюю', 'description': 'Портал в мир демонов. Только сильнейшие A-ранга могут здесь выжить.', 'enemies': ['demon', 'pit_fiend', 'demon_general'], 'mini_boss': 'pit_fiend', 'boss': 'demon_general', 'image': IMAGE_URLS['hell_gate'], 'min_level': 40, 'max_level': 55, 'difficulty': 'extreme'},
    'S': {'name': '⚡ Трон божества', 'description': 'Последнее испытание. Только S-ранг может бросить вызов богу.', 'enemies': ['dragon_ancient', 'final_god'], 'mini_boss': 'dragon_ancient', 'boss': 'final_god', 'image': IMAGE_URLS['throne_god'], 'min_level': 50, 'max_level': 70, 'difficulty': 'legendary'}
}

# --- ФУНКЦИИ БОТА (ОБЕРТКИ) ---

async def safe_edit(query, text=None, keyboard=None, media=None):
    try:
        if media:
            await query.edit_message_media(media=media, reply_markup=keyboard)
        elif text:
            try:
                await query.edit_message_caption(caption=text, parse_mode='Markdown', reply_markup=keyboard)
            except BadRequest as e:
                if "There is no caption" in str(e) or "Message is not modified" not in str(e):
                     await query.edit_message_text(text=text, parse_mode='Markdown', reply_markup=keyboard)
        elif keyboard:
             await query.edit_message_reply_markup(reply_markup=keyboard)
             
    except BadRequest as e:
        if "Message is not modified" in str(e): return 
        logger.error(f"Ошибка UI: {e}")
        if "Message to edit not found" in str(e) or "Media not found" in str(e):
            try: await query.delete_message()
            except: pass
            if media: await query.message.reply_photo(photo=media.media, caption=media.caption, parse_mode='Markdown', reply_markup=keyboard)
            elif text: await query.message.reply_text(text, parse_mode='Markdown', reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Критическая ошибка safe_edit: {e}")

def create_enemy(enemy_key, player_level):
    if enemy_key not in BASE_ENEMIES: 
        if 'wolf' in BASE_ENEMIES: return create_enemy('wolf', player_level)
        return None
    base = BASE_ENEMIES[enemy_key].copy()
    level_multiplier = 1.0 + (player_level - 1) * 0.10
    bonus = 1.0
    if base.get('difficulty') == 'mini_boss': bonus = 1.8
    elif base.get('difficulty') == 'boss': bonus = 2.5
    final_multiplier = level_multiplier * bonus
    enemy = base.copy()
    enemy['health'] = int(base['base_health'] * final_multiplier * 0.85)
    enemy['max_health'] = enemy['health']
    nerf = 0.85 
    enemy['min_physical_damage'] = int(base['base_min_physical_damage'] * level_multiplier * nerf)
    enemy['max_physical_damage'] = int(base['base_max_physical_damage'] * level_multiplier * nerf)
    enemy['min_magic_damage'] = int(base['base_min_magic_damage'] * level_multiplier * nerf)
    enemy['max_magic_damage'] = int(base['base_max_magic_damage'] * level_multiplier * nerf)
    enemy['exp'] = int(base['base_exp'] * final_multiplier * 0.8)
    enemy['gold'] = int(base['base_gold'] * final_multiplier * 0.8)
    if enemy.get('difficulty') == 'boss': enemy['is_boss'] = True
    elif enemy.get('difficulty') == 'mini_boss': enemy['is_mini_boss'] = True
    return enemy

def get_rank_icon(rank): return {'E': '🆕', 'D': '🟢', 'C': '🔵', 'B': '🟣', 'A': '🟠', 'S': '⚡'}.get(rank, '🆕')
def get_xp_bar(level, exp, length=10):
    needed = (level * (level + 1) * 150) // 2
    prev_needed = ((level - 1) * level * 150) // 2
    current_level_exp = exp - prev_needed
    level_diff = needed - prev_needed
    if level_diff <= 0: return "█" * length
    percent = min(1.0, max(0.0, current_level_exp / level_diff))
    filled = int(length * percent)
    return "█" * filled + "░" * (length - filled) + f" {exp}/{needed}"
def get_health_bar(current, maximum, length=15):
    if maximum <= 0: return "💀"
    percent = current / maximum
    filled = int(length * percent)
    empty = length - filled
    bar = "🟩" * filled + "⬜" * empty if percent > 0.3 else "🟥" * filled + "⬜" * empty
    return f"{bar} {current}/{maximum}"
def get_mana_bar(current, maximum, length=10):
    if maximum <= 0: return "⚪"
    percent = current / maximum
    filled = int(length * percent)
    empty = length - filled
    return "🟦" * filled + "⬜" * empty + f" {current}/{maximum}"
def calculate_player_dodge_chance(agility): return min(0.03 + (agility * 0.003), 0.25)
def calculate_crit_chance(agility): return min(0.03 + (agility * 0.002), 0.15)
def calculate_damage(character, enemy, damage_type='physical'):
    base_damage = max(1, character['strength' if damage_type == 'physical' else 'intelligence'] // 2)
    res = enemy.get('physical_resistance' if damage_type == 'physical' else 'magic_resistance', 0.0)
    damage = random.randint(int(base_damage*0.8), int(base_damage*1.2))
    damage = max(1, int(damage * (1 - res)))
    is_crit = random.random() < calculate_crit_chance(character.get('agility', 8))
    if is_crit: damage = int(damage * 1.5)
    return damage, is_crit
def calculate_enemy_damage(enemy, character):
    if enemy['damage_type'] == 'physical': min_d, max_d, res = enemy['min_physical_damage'], enemy['max_physical_damage'], character.get('physical_resistance', 0.0)
    elif enemy['damage_type'] == 'magic': min_d, max_d, res = enemy['min_magic_damage'], enemy['max_magic_damage'], character.get('magic_resistance', 0.0)
    else:
        if random.random() < 0.5: min_d, max_d, res = enemy['min_physical_damage'], enemy['max_physical_damage'], character.get('physical_resistance', 0.0)
        else: min_d, max_d, res = enemy['min_magic_damage'], enemy['max_magic_damage'], character.get('magic_resistance', 0.0)
    damage = random.randint(min_d, max_d)
    damage = int(damage * (1 - float(res)) * 0.85)
    is_dodged = random.random() < calculate_player_dodge_chance(character.get('agility', 8))
    return max(1, damage), is_dodged
def process_enemy_special_attack(enemy, character, log):
    dmg = 0
    effect = ""
    status = None
    if enemy['name'] == '⚔️ Забытый Ветеран' and random.random() < 0.25:
        dmg = random.randint(enemy['min_physical_damage']*2, enemy['max_physical_damage']*3)
        effect = f"🌪 *ВИХРЬ КЛИНКОВ!* Ветеран наносит {dmg} урона!"
        log.append(effect)
        return dmg, effect, None
    if random.random() < enemy.get('special_chance', 0.15):
        if not enemy.get('abilities'): return 0, "", None
        ability = random.choice(enemy['abilities'])
        if ability == 'poison_spit':
            dmg = random.randint(5, 10)
            effect = f"Яд нанес {dmg} урона!"
            status = 'poisoned'
        log.append(f"⚠️ {enemy['name']} использует {ability}! {effect}")
    return dmg, effect, status
def get_available_locations(rank, level):
    ranks = ['E', 'D', 'C', 'B', 'A', 'S']
    try: p_idx = ranks.index(rank)
    except: p_idx = 0
    avail = []
    for k, v in LOCATIONS.items():
        if ranks.index(k) <= p_idx and level >= v['min_level']:
            avail.append((k, v))
    return avail

# --- КЛАВИАТУРЫ ---

def get_main_menu_keyboard(user_id):
    char = database.get_character(user_id)
    kb = [
        [InlineKeyboardButton(f"{get_rank_icon(char['rank'])} {char['rank']}-ранг", callback_data='rank_info')],
        [InlineKeyboardButton("📜 Герой", callback_data='profile'), InlineKeyboardButton("🎒 Инвентарь", callback_data='inventory')],
        [InlineKeyboardButton("⚔️ НА БИТВУ!", callback_data='battle_menu')],
        [InlineKeyboardButton("🛍 Торговец", callback_data='shop'), InlineKeyboardButton("🛠 Крафт", callback_data='craft_menu')],
        [InlineKeyboardButton("🏆 Топ игроков", callback_data='top_players')],
        [InlineKeyboardButton("📜 Помощь", callback_data='help'), InlineKeyboardButton("🔄 Обновить", callback_data='refresh')]
    ]
    if char and char['stat_points'] > 0:
        kb.insert(2, [InlineKeyboardButton(f"🌟 ПРОКАЧАТЬ ({char['stat_points']})", callback_data='level_up_menu')])
    return InlineKeyboardMarkup(kb)

def get_shop_categories_keyboard():
    kb = [
        [InlineKeyboardButton("🍗 Еда и Зелья", callback_data='shop_cat_food'), InlineKeyboardButton("🧱 Ресурсы", callback_data='shop_cat_mat')],
        [InlineKeyboardButton("⚔️ Оружие", callback_data='shop_cat_weapon'), InlineKeyboardButton("🛡️ Броня", callback_data='shop_cat_armor')],
        [InlineKeyboardButton("💍 Аксессуары", callback_data='shop_cat_acc')],
        [InlineKeyboardButton("🔙 Выход", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(kb)

def get_shop_items_keyboard(category, user_gold):
    kb = []
    for k, v in ITEMS_DB.items():
        if v.get('cat') == category:
            icon = "💰" if user_gold >= v['price'] else "🔒"
            kb.append([InlineKeyboardButton(f"{v['name']} ({v['price']}g) {icon}", callback_data=f"buy_{k}")])
    kb.append([InlineKeyboardButton("🔙 Назад", callback_data='shop')])
    return InlineKeyboardMarkup(kb)

def get_craft_keyboard(inventory):
    kb = []
    for key, recipe in CRAFT_RECIPES.items():
        item_data = ITEMS_DB.get(recipe['result'])
        if not item_data: continue
        
        # Простая проверка для UI
        cost_text = f"{recipe['cost']}g"
        
        kb.append([InlineKeyboardButton(f"🔨 {item_data['name']} ({cost_text})", callback_data=f"craft_{key}")])
        
    kb.append([InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')])
    return InlineKeyboardMarkup(kb)

def get_battle_menu_keyboard(char):
    kb = []
    avail = get_available_locations(char['rank'], char['level'])
    for k, v in avail:
        kb.append([InlineKeyboardButton(f"{v['name']} (Ранг {k})", callback_data=f"location_{k}")])
    kb.append([InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')])
    return InlineKeyboardMarkup(kb)

def get_location_enemies_keyboard(rank, level):
    loc = LOCATIONS[rank]
    kb = []
    for e in loc['enemies']:
        if e in BASE_ENEMIES:
            name = BASE_ENEMIES[e]['name']
            kb.append([InlineKeyboardButton(f"⚔️ {name}", callback_data=f"battle_{e}")])
    kb.append([InlineKeyboardButton("🔙 Назад", callback_data='back_to_battle_menu')])
    return InlineKeyboardMarkup(kb)

def get_battle_action_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚔️ Атака", callback_data='attack_physical'), InlineKeyboardButton("🔮 Магия", callback_data='attack_magic')],
        [InlineKeyboardButton("🛡 Блок", callback_data='defend'), InlineKeyboardButton("🏃 Сбежать", callback_data='flee')]
    ])

def get_inventory_keyboard(items, page):
    kb = []
    # items - список словарей (RealDictCursor) из DB
    for i in items:
        key = i['item_key']
        item_data = ITEMS_DB.get(key, {})
        # Если еда или зелье - даем кнопку использовать
        if item_data.get('type') in ['food', 'potion']:
            kb.append([InlineKeyboardButton(f"Использовать {i['item_name']} (x{i['quantity']})", callback_data=f"use_{key}")])
        else:
            # Иначе просто показываем
            kb.append([InlineKeyboardButton(f"{i['item_name']} (x{i['quantity']})", callback_data="ignore")])
            
    kb.append([InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')])
    return InlineKeyboardMarkup(kb)

def get_level_up_keyboard(char, points):
    kb = [
        [InlineKeyboardButton("Сила", callback_data='levelup_strength'), InlineKeyboardButton("Ловкость", callback_data='levelup_agility')],
        [InlineKeyboardButton("Интеллект", callback_data='levelup_intelligence'), InlineKeyboardButton("Живучесть", callback_data='levelup_vitality')],
        [InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(kb)

def get_race_selection_keyboard():
    kb = [[InlineKeyboardButton(v['name'], callback_data=f"race_{k}")] for k, v in database.RACES.items()]
    return InlineKeyboardMarkup(kb)

# --- HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    char = database.get_character(user.id)
    if char:
        await update.message.reply_photo(IMAGE_URLS['village'], caption=f"С возвращением, {char['character_name']}!", reply_markup=get_main_menu_keyboard(user.id))
        return MAIN_MENU
    else:
        await update.message.reply_text("Выберите расу:", reply_markup=get_race_selection_keyboard())
        return CHOOSE_RACE

async def choose_race(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['race'] = query.data.split('_')[1]
    await query.message.reply_text("Как зовут героя?")
    return ENTER_NAME

async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    user = update.effective_user
    database.create_character(user.id, user.username, name, context.user_data['race'])
    await update.message.reply_photo(IMAGE_URLS['village'], caption="Герой создан!", reply_markup=get_main_menu_keyboard(user.id))
    return MAIN_MENU

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    
    if data == 'profile':
        char = database.get_character(user_id)
        phys = max(1, char['strength'] // 2)
        mag = max(1, char['intelligence'] // 2)
        dodge = int(calculate_player_dodge_chance(char['agility']) * 100)
        
        txt = (f"👤 *{char['character_name']}* ({database.RACES[char['race']]['name']})\n"
               f"HP: {get_health_bar(char['health'], char['max_health'])} | MP: {get_mana_bar(char['mana'], char['max_mana'])}\n"
               f"Золото: {char['gold']} | Опыт: {get_xp_bar(char['level'], char['experience'])}\n\n"
               f"⚔️ Урон: {phys} (Физ) / {mag} (Маг)\n"
               f"💨 Уклонение: {dodge}%\n"
               f"❤️ Регенерация: 5% в минуту (вне боя)")
        
        await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['village'], caption=txt, parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
    elif data == 'inventory':
        await show_inventory_menu(update, context)
        return INVENTORY_MENU
    elif data == 'battle_menu':
        char = database.get_character(user_id)
        if char['health'] <= 0:
             await query.answer("Вы мертвы! Воскресните в деревне.", show_alert=True)
             return MAIN_MENU
        await safe_edit(query, text="Выбор локации:", media=InputMediaPhoto(IMAGE_URLS['forest'], caption="Выбор локации:", parse_mode='Markdown'), keyboard=get_battle_menu_keyboard(char))
        return BATTLE_MENU
    elif data == 'shop':
        char = database.get_character(user_id)
        txt = f"🏪 *Магазин*\nЗолото: {char['gold']}💰\nЧего желаете?"
        await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['shop'], caption=txt, parse_mode='Markdown'), keyboard=get_shop_categories_keyboard())
        return SHOP_MENU
    elif data == 'craft_menu':
        await show_craft_menu(query, user_id)
        return CRAFT_MENU
    elif data == 'stats' or data == 'top_players':
        await show_top_players(query, user_id)
    elif data == 'refresh':
        char = database.get_character(user_id)
        txt = (f"👤 *{char['character_name']}* ({database.RACES[char['race']]['name']})\n"
               f"HP: {get_health_bar(char['health'], char['max_health'])} | MP: {get_mana_bar(char['mana'], char['max_mana'])}\n"
               f"Золото: {char['gold']}")
        await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['village'], caption=txt, parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
    elif data == 'level_up_menu':
        char = database.get_character(user_id)
        await query.edit_message_caption("Выберите стат:", reply_markup=get_level_up_keyboard(char, char['stat_points']))
        return LEVEL_UP
    elif data == 'rank_info':
        rank_info = """🏆 *РАНГИ*\n🆕 E: 1-14 ур\n🟢 D: 15-24 ур\n🔵 C: 25-34 ур\n🟣 B: 35-44 ур\n🟠 A: 45-54 ур\n⚡ S: 55+ ур"""
        await query.edit_message_caption(rank_info, parse_mode='Markdown', reply_markup=get_main_menu_keyboard(user_id))
    elif data == 'help':
        await help_command(update, context)
        
    return MAIN_MENU

async def battle_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    
    if data == 'back_to_main':
        await safe_edit(query, text="В деревне", media=InputMediaPhoto(IMAGE_URLS['village'], caption="В деревне", parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
        return MAIN_MENU
    
    elif data.startswith('location_'):
        rank = data.split('_')[1]
        char = database.get_character(user_id)
        loc = LOCATIONS.get(rank, LOCATIONS['E'])
        txt = f"🌲 *{loc['name']}*\n\n{loc['description']}\n\n⚠️ _Будь осторожен, {char['character_name']}..._"
        await safe_edit(query, text=txt, media=InputMediaPhoto(loc['image'], caption=txt, parse_mode='Markdown'), keyboard=get_location_enemies_keyboard(rank, char['level']))
    
    elif data.startswith('battle_'):
        enemy_key = data.split('_', 1)[1]
        char = database.get_character(user_id)
        
        if char['health'] < 5:
            await query.answer("🩸 Вы слишком ранены! Купите еды в магазине.", show_alert=True)
            return BATTLE_MENU
            
        enemy = create_enemy(enemy_key, char['level'])
        if not enemy:
            await query.answer("Ошибка: враг не найден.", show_alert=True)
            return BATTLE_MENU

        # Инициализация боя
        battle_sessions[user_id] = {
            'char': char, 
            'enemy': enemy, 
            'log': [f"⚔️ *ВЫЗОВ БРОШЕН!*\n{enemy['description']}"], 
            'turn': 1,
            'status_effects': [],
            'last_image': None,
            'processing': False
        }
        await render_battle(query, user_id)
        return IN_BATTLE
        
    elif data == 'back_to_battle_menu':
        char = database.get_character(user_id)
        await safe_edit(query, text="Куда направимся?", media=InputMediaPhoto(IMAGE_URLS['forest'], caption="Куда направимся?", parse_mode='Markdown'), keyboard=get_battle_menu_keyboard(char))
        
    return BATTLE_MENU

async def render_battle(query, user_id):
    s = battle_sessions.get(user_id)
    if not s: return 
    
    c, e = s['char'], s['enemy']
    
    log_entries = s['log'][-5:]
    log_str = "\n".join(log_entries)
    
    player_hp = get_health_bar(c['health'], c['max_health'])
    enemy_hp = get_health_bar(e['health'], e['max_health'])
    enemy_rank = e.get('rank', '?')
    enemy_icon = "☠️" if e.get('is_boss') else "👺"
    unique_id = random.randint(100, 999)
    
    txt = (
        f"{enemy_icon} *{e['name']}* `[Ранг {enemy_rank}]`\n"
        f"{enemy_hp}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 *{c['character_name']}* `[{c['level']} ур.]`\n"
        f"{player_hp} | 🌀 MP: {c['mana']}/{c['max_mana']}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{log_str}"
        f"\n`⏱ {datetime.now().strftime('%H:%M:%S')} | {unique_id}`" 
    )
    
    current_image = e['image']
    last_image = s.get('last_image')
    
    if last_image == current_image:
        await safe_edit(query, text=txt, keyboard=get_battle_action_keyboard(), media=None)
    else:
        s['last_image'] = current_image
        media_obj = InputMediaPhoto(current_image, caption=txt, parse_mode='Markdown')
        await safe_edit(query, text=None, media=media_obj, keyboard=get_battle_action_keyboard())

async def battle_action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    s = battle_sessions.get(user_id)
    if not s: 
        await query.answer()
        await safe_edit(query, text="⌛ *Время вышло или бой завершен.*", keyboard=get_main_menu_keyboard(user_id))
        return MAIN_MENU

    if s.get('processing'):
        await query.answer("⏳ ...", show_alert=False)
        return IN_BATTLE
    
    s['processing'] = True
    
    try:
        await query.answer()
        action = query.data
        c, e, log = s['char'], s['enemy'], s['log']
        
        # --- ХОД ИГРОКА ---
        player_damage = 0
        player_action_text = ""
        
        if action == 'flee':
            if e.get('is_boss') or e.get('is_mini_boss'):
                 log.append("🚫 *ОТ БОССА НЕЛЬЗЯ СБЕЖАТЬ!*")
            elif random.random() < 0.6: 
                database.update_character_stats(user_id, health=c['health'], mana=c['mana'])
                del battle_sessions[user_id]
                txt = "🏃 *ПОЗОРНОЕ БЕГСТВО!*"
                await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['village'], caption=txt, parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
                return MAIN_MENU
            else:
                log.append("⛓ *ПОБЕГ НЕ УДАЛСЯ!*")
                
        elif action == 'defend':
            log.append("🛡 Вы ушли в глухую оборону.")
            
        elif action == 'attack_physical':
            dmg, is_crit = calculate_damage(c, e, 'physical')
            player_damage = dmg
            verbs = ["рубанули", "пронзили", "ударили", "сокрушили"]
            verb = random.choice(verbs)
            crit_txt = "💥 *КРИТ!* " if is_crit else ""
            player_action_text = f"{crit_txt}Вы {verb} врага на *{dmg}*!"
                
        elif action == 'attack_magic':
            if c['mana'] >= 10:
                c['mana'] -= 10
                dmg, is_crit = calculate_damage(c, e, 'magic')
                dmg = int(dmg * 1.2)
                player_damage = dmg
                spells = ["Огненная стрела", "Ледяной шип", "Разряд молнии"]
                spell = random.choice(spells)
                crit_txt = " (КРИТ!)" if is_crit else ""
                player_action_text = f"🔮 {spell} нанес *{dmg}* урона{crit_txt}!"
            else:
                log.append("💧 *НЕТ МАНЫ!*")
                player_damage = max(1, c['strength'] // 4)
                player_action_text = f"👊 Удар рукой на {player_damage}."

        if player_damage > 0:
            e['health'] -= player_damage
            log.append(player_action_text)

        # --- ПОБЕДА ---
        if e['health'] <= 0:
            gold_win = int(e['gold'] * random.uniform(0.9, 1.2))
            xp_win = e['exp']
            
            # ЛУТ СИСТЕМА
            dropped_items = []
            if e.get('drops'):
                for drop in e['drops']:
                    if random.random() < 0.4: # 40% шанс дропа
                        item_info = ITEMS_DB.get(drop)
                        if item_info:
                            # Добавляем в инвентарь (price=0 = лут)
                            database.buy_item(user_id, drop, 'material', item_info['name'], 0, 0)
                            dropped_items.append(item_info['name'])

            database.add_experience(user_id, xp_win)
            database.add_gold(user_id, gold_win)
            
            # НЕТ АВТО-ХИЛА: Сохраняем текущее здоровье
            database.update_character_stats(user_id, health=c['health'], mana=c['mana'], battle_wins=c.get('battle_wins',0)+1)
            
            if e.get('is_boss'): database.increment_boss_kills(user_id, False)
            if e.get('is_mini_boss'): database.increment_boss_kills(user_id, True)
            
            del battle_sessions[user_id]
            
            loot_text = f"\n🎒 Лут: {', '.join(dropped_items)}" if dropped_items else ""
            win_msg = (f"🏆 *ПОБЕДА!*\n\n☠️ {e['name']} повержен.\n💰 +{gold_win}g | 📚 +{xp_win}xp{loot_text}\n"
                       f"⚠️ Здоровье не восстановлено! Ешьте или пейте зелья.")
            await safe_edit(query, text=win_msg, media=InputMediaPhoto(IMAGE_URLS['village'], caption=win_msg, parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
            return MAIN_MENU

        # --- ХОД ВРАГА ---
        if action != 'flee' or (action == 'flee' and "ПОБЕГ НЕ УДАЛСЯ" in log[-1]):
            spec_dmg, spec_desc, spec_status = process_enemy_special_attack(e, c, log)
            if spec_dmg > 0:
                enemy_dmg = spec_dmg
                if action == 'defend': 
                    enemy_dmg = int(enemy_dmg * 0.6)
                    log.append(f"🛡 Блок снизил урон до {enemy_dmg}!")
                c['health'] -= enemy_dmg
            else:
                base_dmg, is_dodged = calculate_enemy_damage(e, c)
                if is_dodged:
                    log.append(f"💨 *УВОРОТ!* {e['name']} промазал!")
                else:
                    if action == 'defend':
                        base_dmg //= 2
                        log.append(f"🛡 Блок! Урон: *{base_dmg}*")
                    else:
                        log.append(f"💔 {e['name']} нанес *{base_dmg}* урона!")
                    c['health'] -= base_dmg

        # --- ПОРАЖЕНИЕ ---
        if c['health'] <= 0:
            database.update_character_stats(user_id, health=0, battle_losses=c.get('battle_losses',0)+1)
            del battle_sessions[user_id]
            death_msg = "💀 *ВЫ ПОГИБЛИ...* Жрецы воскресили вас в деревне."
            await safe_edit(query, text=death_msg, media=InputMediaPhoto("https://img.freepik.com/free-photo/graveyard-fog_23-2150911249.jpg", caption=death_msg, parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
            return MAIN_MENU
        
        s['turn'] += 1
        await render_battle(query, user_id)
        
    finally:
        if user_id in battle_sessions:
            battle_sessions[user_id]['processing'] = False
            
    return IN_BATTLE

async def shop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    char = database.get_character(user_id)
    
    if data == 'back_to_main':
        await query.answer()
        await safe_edit(query, text="В деревне", media=InputMediaPhoto(IMAGE_URLS['village'], caption="В деревне", parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
        return MAIN_MENU
    elif data == 'shop': 
        txt = f"🏪 *Магазин*\nЗолото: {char['gold']}💰\nЧего желаете?"
        await safe_edit(query, text=txt, keyboard=get_shop_categories_keyboard())
        return SHOP_MENU
    elif data.startswith('shop_cat_'):
        cat = data.split('_')[2]
        txt = f"Категория: {cat.upper()}"
        await safe_edit(query, text=txt, keyboard=get_shop_items_keyboard(cat, char['gold']))
        return SHOP_MENU
    elif data.startswith('buy_'):
        item_key = data.split('_', 1)[1]
        item = ITEMS_DB.get(item_key)
        
        if not item: return SHOP_MENU

        # Проверка ранга для снаряжения
        if item.get('rank'):
            ranks_order = ['E', 'D', 'C', 'B', 'A', 'S']
            try:
                p_rank_idx = ranks_order.index(char['rank'])
                i_rank_idx = ranks_order.index(item['rank'])
                if p_rank_idx < i_rank_idx:
                    await query.answer(f"🔒 Нужен ранг {item['rank']}!", show_alert=True)
                    return SHOP_MENU
            except: pass

        if char['gold'] >= item['price']:
            # Покупка через DB (она же надевает шмот и обновляет статы)
            res, msg = database.buy_item(user_id, item_key, item['type'], item['name'], item['price'], item.get('effect', 0))
            await query.answer(msg, show_alert=True)
            # Обновляем меню
            char = database.get_character(user_id)
            await query.edit_message_reply_markup(reply_markup=get_shop_items_keyboard(item['cat'], char['gold']))
        else:
            await query.answer("💸 Не хватает золота!", show_alert=True)
            
    return SHOP_MENU

async def show_craft_menu(query, user_id):
    items = database.get_inventory(user_id)
    # Конвертируем список словарей из БД в простой словарь {item_key: qty}
    inv_dict = {i['item_key']: i['quantity'] for i in items}
    
    txt = "🛠 *Мастерская*\nСоздавайте предметы из ресурсов."
    await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['craft'], caption=txt, parse_mode='Markdown'), keyboard=get_craft_keyboard(inv_dict))

async def craft_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    
    if data == 'back_to_main':
        await safe_edit(query, text="В деревне", media=InputMediaPhoto(IMAGE_URLS['village'], caption="В деревне", parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
        return MAIN_MENU
    
    elif data.startswith('craft_'):
        recipe_key = data.split('_')[1]
        recipe = CRAFT_RECIPES.get(recipe_key)
        if not recipe: return CRAFT_MENU
        
        char = database.get_character(user_id)
        if char['gold'] < recipe['cost']:
            await query.answer("Не хватает золота на работу!", show_alert=True)
            return CRAFT_MENU
            
        items = database.get_inventory(user_id)
        inv_dict = {i['item_key']: i['quantity'] for i in items}
        
        # Проверка материалов
        for mat, amt in recipe['mats'].items():
            if inv_dict.get(mat, 0) < amt:
                await query.answer(f"Не хватает: {ITEMS_DB[mat]['name']}", show_alert=True)
                return CRAFT_MENU
        
        # Списание материалов
        for mat, amt in recipe['mats'].items():
            for _ in range(amt):
                database.use_item(user_id, mat, 'material', 'Craft', 0)
        
        # Получение результата (через покупку за цену крафта)
        res_item = ITEMS_DB[recipe['result']]
        database.buy_item(user_id, recipe['result'], res_item['type'], res_item['name'], recipe['cost'], res_item.get('effect', 0))
        
        await query.answer(f"Создано: {res_item['name']}!", show_alert=True)
        await show_craft_menu(query, user_id)
        
    return CRAFT_MENU

async def inventory_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    
    if data == 'back_to_main':
        await safe_edit(query, text="Главное меню", media=InputMediaPhoto(IMAGE_URLS['village'], caption="Главное меню", parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
        return MAIN_MENU
    elif data.startswith('use_'):
        key = data.split('_', 1)[1]
        item = ITEMS_DB.get(key)
        effect = item['effect'] if item else 0
        
        # Используем предмет через DB
        res, msg = database.use_item(user_id, key, 'potion', 'Potion', effect) 
        await query.answer(msg, show_alert=True)
        
        items = database.get_inventory(user_id)
        if items:
            await query.edit_message_reply_markup(reply_markup=get_inventory_keyboard(items, 0))
        else:
            await safe_edit(query, text="Пусто", media=InputMediaPhoto(IMAGE_URLS['village'], caption="Пусто", parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
            return MAIN_MENU
    return INVENTORY_MENU

async def show_inventory_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query if update.callback_query else update
    user_id = query.from_user.id
    items = database.get_inventory(user_id)
    txt = "Инвентарь:" if items else "Инвентарь пуст"
    kb = get_inventory_keyboard(items, 0) if items else get_main_menu_keyboard(user_id)
    await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['inventory'], caption=txt, parse_mode='Markdown'), keyboard=kb)
    return INVENTORY_MENU

async def show_top_players(query, user_id):
    top_players = database.get_top_players(10)
    top_text = "🏆 *ТОП ЛЕГЕНД СЕРВЕРА*\n━━━━━━━━━━━━━━━━\n"
    for i, player in enumerate(top_players, 1):
        name = html.escape(player['character_name'])
        lvl = player['level']
        race_key = player['race']
        race_name = database.RACES.get(race_key, {}).get('name', 'Неизвестно')
        bosses = player.get('boss_kills', 0)
        medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
        top_text += f"{medal} <b>{name}</b>\n   └ 🎭 {race_name} | ⭐ {lvl} ур.\n   └ ☠️ Убито боссов: {bosses}\n\n"
    await safe_edit(query, text=top_text, media=InputMediaPhoto(IMAGE_URLS['village'], caption=top_text, parse_mode='HTML'), keyboard=get_main_menu_keyboard(user_id))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🆘 *Помощь*\n• 📜 **Герой** - Статы\n• ⚔️ **Битва** - Сражения\n• 🛍 **Торговец** - Еда и снаряжение\n• 🛠 **Крафт** - Создание предметов\n• 🎒 **Инвентарь** - Предметы\n❤️ **Внимание:** Здоровье не восстанавливается после боя! Используйте еду."
    if update.callback_query:
         await safe_edit(update.callback_query, text=text, media=InputMediaPhoto(IMAGE_URLS['village'], caption=text, parse_mode='Markdown'), keyboard=get_main_menu_keyboard(update.effective_user.id))
    else:
         await update.message.reply_text(text, parse_mode='Markdown')

async def daily_reminder(context: ContextTypes.DEFAULT_TYPE):
    users = database.get_all_users()
    for uid in users:
        try: await context.bot.send_message(chat_id=uid, text="🌅 Новый день настал! Ваш герой готов к подвигам! (/start)")
        except: pass

async def unknown_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Напишите /start")

async def unknown_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("Сессия устарела. Напишите /start.")

def main():
    database.init_db()
    app = Application.builder().token(TOKEN).build()
    if app.job_queue:
        app.job_queue.run_daily(daily_reminder, time=datetime.strptime("12:00", "%H:%M").time(), days=(0,1,2,3,4,5,6))
    
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSE_RACE: [CallbackQueryHandler(choose_race, pattern='^race_')],
            ENTER_NAME: [MessageHandler(filters.TEXT, enter_name)],
            MAIN_MENU: [CallbackQueryHandler(main_menu_handler)],
            BATTLE_MENU: [CallbackQueryHandler(battle_menu_handler)],
            IN_BATTLE: [CallbackQueryHandler(battle_action_handler)],
            SHOP_MENU: [CallbackQueryHandler(shop_handler)],
            CRAFT_MENU: [CallbackQueryHandler(craft_handler)],
            LEVEL_UP: [CallbackQueryHandler(level_up_handler)],
            INVENTORY_MENU: [CallbackQueryHandler(inventory_menu_handler)]
        },
        fallbacks=[CommandHandler('start', start)]
    )
    app.add_handler(conv)
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_text))
    app.add_handler(CallbackQueryHandler(unknown_callback))
    print("Бот запущен!")
    app.run_polling()

if __name__ == '__main__':
    main()
