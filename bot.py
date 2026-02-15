import os
import logging
import random
import html
import asyncio
from datetime import datetime, time
from telegram.error import BadRequest
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
CHOOSE_RACE, ENTER_NAME, MAIN_MENU, BATTLE_MENU, IN_BATTLE, SHOP_MENU, LEVEL_UP, INVENTORY_MENU, CRAFT_MENU, GUILD_MENU= range(10)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
battle_sessions = {}

# --- ВИЗУАЛ (DARK FANTASY) ---
IMAGE_URLS = {
    'human': 'https://i126.fastpic.org/thumb/2026/0130/2c/_d2515d33e45fa7ffb5246cacabdaba2c.jpeg',
    'elf': 'https://i126.fastpic.org/thumb/2026/0130/81/_d3d94be5aa45b9239aeb5adc41443081.jpeg',
    'dwarf': 'https://i126.fastpic.org/thumb/2026/0130/5b/_c188fac4eb6d205bd9fc0486c9b9355b.jpeg',
    'orc': 'https://i126.fastpic.org/thumb/2026/0130/20/_b8c1f666bd21bb415e8fb35145eb3e20.jpeg',
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
    'village': 'https://i.pinimg.com/736x/50/b6/36/50b636f399c41e8697972676ebe85dff.jpg',
    'forest': 'https://img.freepik.com/premium-photo/ancient-forest-ai-generated_1127-13930.jpg',
    'castle': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTrAoGzKjgZxurLbxZ_Dyhtkm1gBqMUMtA87w&s',
    'dungeon': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSTZd9YHDcPOGmD8ezmHB0xD-HfA9O7OpgVyA&s',
    'training_camp': 'https://img1.liveinternet.ru/images/attach/b/2/1/726/1726838_full0011.jpg',
    'hell_gate': 'https://abrakadabra.fun/uploads/posts/2022-01/1642490542_3-abrakadabra-fun-p-temnii-mag-art-5.jpg',
    'throne_god': 'https://abrakadabra.fun/uploads/posts/2022-03/1646721873_1-abrakadabra-fun-p-pauk-fantezi-art-1.jpg',
    'shop': 'https://cubiq.ru/wp-content/uploads/2021/07/picture-1-15.jpeg',
    'inventory': 'https://freepngimg.com/thumb/backpack/22202-6-backpack-painting.png',
    'craft': 'https://abrakadabra.fun/uploads/posts/2022-01/1643486640_1-abrakadabra-fun-p-kuznitsa-art-1.jpg',
    'guild': 'https://www.worldanvil.com/uploads/images/9a7f5886e9dde2f96801a33e70e75345.jpg'
}
# --- СПОСОБНОСТИ РАС ---
# type: heal (лечение), dmg (урон), buff (усиление)
# scale: множитель (например, 2.0 = 200% урона)
RACE_ABILITIES = {
    'human': {
        10: {'key': 'h1', 'name': '🙏 Молитва', 'mana': 20, 'cd': 4, 'type': 'heal', 'val': 0.4, 'desc': 'Восстанавливает 40% здоровья.'},
        25: {'key': 'h2', 'name': '⚔️ Удар Героя', 'mana': 40, 'cd': 3, 'type': 'dmg', 'val': 2.5, 'desc': 'Мощный удар (250% урона).'},
        40: {'key': 'h3', 'name': '🛡️ Божественный щит', 'mana': 60, 'cd': 6, 'type': 'buff_def', 'val': 500, 'desc': 'Полная защита на 1 ход.'}
    },
    'elf': {
        10: {'key': 'e1', 'name': '🏹 Точный выстрел', 'mana': 15, 'cd': 2, 'type': 'dmg', 'val': 1.8, 'desc': 'Быстрый выстрел (180% урона).'},
        25: {'key': 'e2', 'name': '🍃 Сила Леса', 'mana': 45, 'cd': 4, 'type': 'heal_mana', 'val': 0.5, 'desc': 'Лечит 50% HP и снимает эффекты.'},
        40: {'key': 'e3', 'name': '⚡ Гроза', 'mana': 80, 'cd': 5, 'type': 'magic_nuke', 'val': 3.5, 'desc': 'Магический взрыв (350% маг. урона).'}
    },
    'orc': {
        10: {'key': 'o1', 'name': '💢 Ярость', 'mana': 10, 'cd': 4, 'type': 'buff_str', 'val': 0.5, 'desc': '+50% к Силе на ход.'},
        25: {'key': 'o2', 'name': '🩸 Кровожадность', 'mana': 30, 'cd': 3, 'type': 'lifesteal', 'val': 1.5, 'desc': 'Удар (150%) + лечение от урона.'},
        40: {'key': 'o3', 'name': '🪓 Казнь', 'mana': 50, 'cd': 5, 'type': 'dmg_exec', 'val': 4.0, 'desc': 'Сокрушительный удар (400% урона).'}
    },
    'dwarf': {
        10: {'key': 'd1', 'name': '🪨 Каменная кожа', 'mana': 20, 'cd': 4, 'type': 'buff_def', 'val': 0.8, 'desc': 'Снижает урон на 80% (1 ход).'},
        25: {'key': 'd2', 'name': '🔨 Удар Молотом', 'mana': 35, 'cd': 3, 'type': 'stun_dmg', 'val': 2.0, 'desc': 'Урон (200%) + шанс оглушить.'},
        40: {'key': 'd3', 'name': '🍺 Живая вода', 'mana': 50, 'cd': 5, 'type': 'heal', 'val': 1.0, 'desc': 'Полное восстановление здоровья.'}
    }
}
ELF_MAGIC_TYPES = {
    'solar': {'name': '☀️ Магия Солнца', 'desc': 'Испепеляющий жар.'},
    'lunar': {'name': '🌙 Магия Луны', 'desc': 'Холодный свет ночи.'},
    'star':  {'name': '✨ Магия Звезд', 'desc': 'Космическая энергия.'}
}
# --- ЭЛЬФИЙСКАЯ КНИГА ЗАКЛИНАНИЙ ---
ELF_SPELLS = {
    # СОЛНЦЕ (Чистый урон)
    'sun': {
        'name': '☀️ Школа Солнца',
        'spells': {
            'sun_ray': {'name': 'Лучевой ожог', 'lvl': 1, 'mana': 10, 'desc': 'Базовый урон огнем (120%).', 'type': 'dmg', 'val': 1.2},
            'sun_flare': {'name': 'Солнечная вспышка', 'lvl': 15, 'mana': 25, 'desc': 'Мощный взрыв (200% урона).', 'type': 'dmg', 'val': 2.0},
            'supernova': {'name': 'Сверхновая', 'lvl': 30, 'mana': 60, 'desc': 'Испепеление (350% урона).', 'type': 'dmg', 'val': 3.5}
        }
    },
    # ЛУНА (Вампиризм и дебаффы)
    'moon': {
        'name': '🌙 Школа Луны',
        'spells': {
            'moon_bolt': {'name': 'Лунная стрела', 'lvl': 1, 'mana': 12, 'desc': 'Урон (100%) + кража 30% HP.', 'type': 'drain', 'val': 1.0},
            'nightmare': {'name': 'Кошмар', 'lvl': 15, 'mana': 30, 'desc': 'Снижает урон врага на 50% и бьет.', 'type': 'debuff_dmg', 'val': 1.5},
            'eclipse': {'name': 'Затмение', 'lvl': 30, 'mana': 55, 'desc': 'Крадет много жизни (250% урона).', 'type': 'drain', 'val': 2.5}
        }
    },
    # ЗВЕЗДЫ (Мана и усиление)
    'star': {
        'name': '✨ Школа Звезд',
        'spells': {
            'star_dust': {'name': 'Звездная пыль', 'lvl': 1, 'mana': 5, 'desc': 'Слабый урон, но почти без маны.', 'type': 'dmg', 'val': 1.1},
            'comet': {'name': 'Комета', 'lvl': 15, 'mana': 20, 'desc': 'Урон (150%) + шанс оглушить.', 'type': 'stun', 'val': 1.5},
            'galaxy': {'name': 'Парад планет', 'lvl': 30, 'mana': 50, 'desc': 'Серия ударов (300% урона).', 'type': 'dmg', 'val': 3.0}
        }
    }
}
# --- БАЗА ПРЕДМЕТОВ ---
ITEMS_DB = {
    # --- ЕДА И ЗЕЛЬЯ ---
    'bread': {'name': '🍞 Заплесневелый хлеб', 'desc': 'На вкус как пыль.', 'price': 15, 'type': 'food', 'effect': 10, 'cat': 'food', 'rank': 'E'},
    'apple': {'name': '🍎 Дикое яблоко', 'desc': 'Кислое, но съедобное.', 'price': 20, 'type': 'food', 'effect': 15, 'cat': 'food', 'rank': 'E'},
    'meat_stew': {'name': '🍲 Похлебка бедняка', 'desc': 'Варево из неизвестного мяса.', 'price': 45, 'type': 'food', 'effect': 35, 'cat': 'food', 'rank': 'D'},
    'roast_boar': {'name': '🍖 Окорок вепря', 'desc': 'Жирное мясо, дающее силы.', 'price': 80, 'type': 'food', 'effect': 60, 'cat': 'food', 'rank': 'C'},
    'elven_wine': {'name': '🍷 Кровь Лозы', 'desc': 'Вино, настоянное на лунном свете.', 'price': 150, 'type': 'food', 'effect': 100, 'cat': 'food', 'rank': 'B'},
    'ambrosia': {'name': '🏺 Амброзия', 'desc': 'Пища богов.', 'price': 500, 'type': 'food', 'effect': 300, 'cat': 'food', 'rank': 'A'},
    
    'small_hp': {'name': '🧪 Слабый отвар', 'desc': 'Пахнет тиной.', 'price': 50, 'type': 'potion', 'effect': 30, 'cat': 'food', 'rank': 'E'},
    'medium_hp': {'name': '🧪 Зелье Крови', 'desc': 'Бурлящая алая жидкость.', 'price': 100, 'type': 'potion', 'effect': 70, 'cat': 'food', 'rank': 'D'},
    'large_hp': {'name': '🧪 Эссенция Жизни', 'desc': 'Чистая жизненная сила.', 'price': 250, 'type': 'potion', 'effect': 150, 'cat': 'food', 'rank': 'B'},
    'full_hp': {'name': '🧪 Слеза Феникса', 'desc': 'Восстанавливает тело из пепла.', 'price': 600, 'type': 'potion', 'effect': 500, 'cat': 'food', 'rank': 'S'},
    
    'small_mp': {'name': '🔮 Отвар ясности', 'desc': 'Просветляет разум.', 'price': 40, 'type': 'potion', 'effect': 20, 'cat': 'food', 'rank': 'E'},
    'large_mp': {'name': '🔮 Эликсир Бездны', 'desc': 'Наполняет вены магией.', 'price': 200, 'type': 'potion', 'effect': 100, 'cat': 'food', 'rank': 'B'},

    # --- ОРУЖИЕ ---
    'rusty_sword': {'name': '⚔️ Ржавый клинок', 'desc': 'Оружие мертвеца. (+5 Силы)', 'price': 150, 'type': 'weapon', 'effect': 5, 'cat': 'weapon', 'rank': 'E'},
    'iron_axe': {'name': '🪓 Топор палача', 'desc': 'Тяжелый, в крови. (+10 Силы)', 'price': 400, 'type': 'weapon', 'effect': 10, 'cat': 'weapon', 'rank': 'D'},
    'steel_saber': {'name': '⚔️ Гвардейская сабля', 'desc': 'Оружие рыцаря. (+15 Силы)', 'price': 900, 'type': 'weapon', 'effect': 15, 'cat': 'weapon', 'rank': 'C'},
    'dark_blade': {'name': '🗡️ Клинок Скорби', 'desc': 'Шепчет проклятия. (+20 Силы)', 'price': 2500, 'type': 'weapon', 'effect': 20, 'cat': 'weapon', 'rank': 'B'},
    'demon_slayer': {'name': '🔥 Убийца Демонов', 'desc': 'Пылает яростью. (+30 Силы)', 'price': 6000, 'type': 'weapon', 'effect': 30, 'cat': 'weapon', 'rank': 'A'},
    'god_killer': {'name': '⚡ Гнев Титана', 'desc': 'Раскалывает небо. (+50 Силы)', 'price': 15000, 'type': 'weapon', 'effect': 50, 'cat': 'weapon', 'rank': 'S'},

    # --- БРОНЯ ---
    'leather_vest': {'name': '🛡️ Шкура волка', 'desc': 'Греет. (+3 ХП)', 'price': 120, 'type': 'armor', 'effect': 3, 'cat': 'armor', 'rank': 'E'},
    'chainmail': {'name': '🛡️ Ржавая кольчуга', 'desc': 'Надежная. (+8 ХП)', 'price': 350, 'type': 'armor', 'effect': 8, 'cat': 'armor', 'rank': 'D'},
    'plate_armor': {'name': '🛡️ Латы Крестоносца', 'desc': 'Освященная сталь. (+15 ХП)', 'price': 850, 'type': 'armor', 'effect': 15, 'cat': 'armor', 'rank': 'C'},
    'mithril_armor': {'name': '💠 Доспех Ночи', 'desc': 'Сливается с тенями. (+25 ХП)', 'price': 2200, 'type': 'armor', 'effect': 25, 'cat': 'armor', 'rank': 'B'},
    'dragon_mail': {'name': '🐉 Чешуя Дракона', 'desc': 'Легендарная. (+40 ХП)', 'price': 5500, 'type': 'armor', 'effect': 40, 'cat': 'armor', 'rank': 'A'},
    'void_plate': {'name': '🌌 Доспех Пустоты', 'desc': 'Сама тьма. (+70 ХП)', 'price': 12000, 'type': 'armor', 'effect': 70, 'cat': 'armor', 'rank': 'S'},

    # --- АКСЕССУАРЫ ---
    'wooden_ring': {'name': '💍 Кольцо из корня', 'desc': 'Слабый оберег. (+2 Инт)', 'price': 200, 'type': 'artifact', 'effect': 2, 'cat': 'acc', 'rank': 'E'},
    'silver_amulet': {'name': '🧿 Глаз Ведьмы', 'desc': 'Смотрит в душу. (+5 Инт)', 'price': 500, 'type': 'artifact', 'effect': 5, 'cat': 'acc', 'rank': 'D'},
    'gold_ring': {'name': '💍 Перстень Барона', 'desc': 'Украден с трупа. (+10 Инт)', 'price': 1200, 'type': 'artifact', 'effect': 10, 'cat': 'acc', 'rank': 'C'},
    'skull_necklace': {'name': '💀 Лик Смерти', 'desc': 'Усиливает магию. (+20 Инт)', 'price': 3000, 'type': 'artifact', 'effect': 20, 'cat': 'acc', 'rank': 'B'},
    'demon_eye': {'name': '👁️ Око Бездны', 'desc': 'Запретные знания. (+35 Инт)', 'price': 7000, 'type': 'artifact', 'effect': 35, 'cat': 'acc', 'rank': 'A'},

    # --- МАТЕРИАЛЫ ---
    'wolf_pelt': {'name': '🐺 Волчья шкура', 'desc': 'Жесткая шерсть.', 'price': 5, 'type': 'material', 'cat': 'mat', 'rank': 'E'},
    'goblin_ear': {'name': '👂 Ухо гоблина', 'desc': 'Трофей.', 'price': 8, 'type': 'material', 'cat': 'mat', 'rank': 'E'},
    'slime_goo': {'name': '🟢 Едкая слизь', 'desc': 'Прожигает ткань.', 'price': 6, 'type': 'material', 'cat': 'mat', 'rank': 'E'},
    'iron_ore': {'name': '🪨 Железная руда', 'desc': 'Тяжелый кусок.', 'price': 15, 'type': 'material', 'cat': 'mat', 'rank': 'D'},
    'spider_silk': {'name': '🕸️ Живая паутина', 'desc': 'Прочная.', 'price': 20, 'type': 'material', 'cat': 'mat', 'rank': 'D'},
    'bone_dust': {'name': '💀 Прах мертвеца', 'desc': 'Холодный.', 'price': 25, 'type': 'material', 'cat': 'mat', 'rank': 'C'},
    'vampire_fang': {'name': '🧛 Клык вампира', 'desc': 'Острый.', 'price': 60, 'type': 'material', 'cat': 'mat', 'rank': 'B'},
    'demon_horn': {'name': '😈 Рог демона', 'desc': 'Излучает жар.', 'price': 100, 'type': 'material', 'cat': 'mat', 'rank': 'A'},
    'void_crystal': {'name': '🌌 Осколок Пустоты', 'desc': 'Из другого мира.', 'price': 300, 'type': 'material', 'cat': 'mat', 'rank': 'S'}
}

# --- РЕЦЕПТЫ КРАФТА ---
CRAFT_RECIPES = {
    'small_hp': {'result': 'small_hp', 'cost': 10, 'mats': {'slime_goo': 2, 'wolf_pelt': 1}},
    'leather_vest': {'result': 'leather_vest', 'cost': 50, 'mats': {'wolf_pelt': 5}},
    'rusty_sword': {'result': 'rusty_sword', 'cost': 60, 'mats': {'goblin_ear': 5, 'wolf_pelt': 2}},
    'medium_hp': {'result': 'medium_hp', 'cost': 30, 'mats': {'small_hp': 2, 'spider_silk': 1}},
    'iron_axe': {'result': 'iron_axe', 'cost': 150, 'mats': {'iron_ore': 5, 'wolf_pelt': 3}},
    'chainmail': {'result': 'chainmail', 'cost': 120, 'mats': {'iron_ore': 8, 'spider_silk': 4}},
    'dark_blade': {'result': 'dark_blade', 'cost': 1000, 'mats': {'demon_horn': 1, 'bone_dust': 10, 'iron_ore': 20}},
    'mithril_armor': {'result': 'mithril_armor', 'cost': 800, 'mats': {'iron_ore': 30, 'bone_dust': 15, 'vampire_fang': 2}},
    'god_killer': {'result': 'god_killer', 'cost': 5000, 'mats': {'void_crystal': 5, 'demon_horn': 20, 'dragon_mail': 1}}
}

# --- БЕСТИАРИЙ ---
BASE_ENEMIES = {
    'wolf': {'name': '🐺 Бешеный Волк', 'base_health': 30, 'base_min_physical_damage': 4, 'base_max_physical_damage': 7, 'base_min_magic_damage': 0, 'base_max_magic_damage': 0, 'base_exp': 12, 'base_gold': 8, 'rank': 'E', 'description': 'Облезлый зверь с пеной у рта.', 'image': IMAGE_URLS['wolf'], 'difficulty': 'easy', 'abilities': ['basic_attack'], 'damage_type': 'physical', 'dodge_chance': 0.08, 'drops': ['wolf_pelt', 'apple']},
    'goblin': {'name': '👹 Гоблин-Мародер', 'base_health': 35, 'base_min_physical_damage': 5, 'base_max_physical_damage': 9, 'base_min_magic_damage': 0, 'base_max_magic_damage': 0, 'base_exp': 16, 'base_gold': 12, 'rank': 'E', 'description': 'Мерзкое создание.', 'image': IMAGE_URLS['goblin'], 'difficulty': 'easy', 'abilities': ['basic_attack', 'dirty_trick'], 'damage_type': 'physical', 'dodge_chance': 0.12, 'drops': ['goblin_ear', 'bread']},
    'slime': {'name': '🟢 Кислотная Жижа', 'base_health': 40, 'base_min_physical_damage': 2, 'base_max_physical_damage': 7, 'base_min_magic_damage': 1, 'base_max_magic_damage': 4, 'base_exp': 10, 'base_gold': 7, 'rank': 'E', 'description': 'Аморфная масса.', 'image': IMAGE_URLS['slime'], 'difficulty': 'easy', 'abilities': ['basic_attack', 'poison_spit'], 'damage_type': 'mixed', 'dodge_chance': 0.02, 'drops': ['slime_goo']},
    'goblin_elite': {'name': '👹 Вожак Гоблинов', 'base_health': 80, 'base_min_physical_damage': 10, 'base_max_physical_damage': 18, 'base_min_magic_damage': 0, 'base_max_magic_damage': 0, 'base_exp': 35, 'base_gold': 25, 'rank': 'E', 'description': 'Громила в украденных доспехах.', 'image': IMAGE_URLS['hot_goblin'], 'difficulty': 'mini_boss', 'abilities': ['basic_attack', 'power_strike'], 'damage_type': 'physical', 'dodge_chance': 0.15, 'drops': ['goblin_ear', 'iron_ore', 'rusty_sword']},
    'training_master': {'name': '⚔️ Падший Рыцарь', 'base_health': 110, 'base_min_physical_damage': 12, 'base_max_physical_damage': 22, 'base_min_magic_damage': 0, 'base_max_magic_damage': 0, 'base_exp': 50, 'base_gold': 40, 'rank': 'E', 'description': 'Безумный воин, охраняющий руины.', 'image': IMAGE_URLS['knight'], 'difficulty': 'boss', 'abilities': ['basic_attack', 'whirlwind_strike'], 'damage_type': 'physical', 'dodge_chance': 0.20, 'drops': ['iron_ore', 'small_hp', 'leather_vest']},
    'forest_spider': {'name': '🕷️ Арахнид', 'base_health': 60, 'base_min_physical_damage': 7, 'base_max_physical_damage': 14, 'base_min_magic_damage': 0, 'base_max_magic_damage': 0, 'base_exp': 25, 'base_gold': 16, 'rank': 'D', 'description': 'Восьмилапый кошмар.', 'image': IMAGE_URLS['dragon'], 'difficulty': 'medium', 'abilities': ['basic_attack', 'web_shot'], 'damage_type': 'physical', 'dodge_chance': 0.15, 'drops': ['spider_silk']},
    'ghost': {'name': '👻 Заблудшая Душа', 'base_health': 50, 'base_min_physical_damage': 6, 'base_max_physical_damage': 12, 'base_min_magic_damage': 3, 'base_max_magic_damage': 8, 'base_exp': 28, 'base_gold': 20, 'rank': 'D', 'description': 'Призрак путника.', 'image': IMAGE_URLS['mage'], 'difficulty': 'medium', 'abilities': ['basic_attack', 'fear'], 'damage_type': 'magic', 'dodge_chance': 0.25, 'drops': ['small_mp']},
    'wild_boar': {'name': '🐗 Секач-Людоед', 'base_health': 85, 'base_min_physical_damage': 10, 'base_max_physical_damage': 20, 'base_min_magic_damage': 0, 'base_max_magic_damage': 0, 'base_exp': 32, 'base_gold': 24, 'rank': 'D', 'description': 'Массивная туша.', 'image': IMAGE_URLS['wolf'], 'difficulty': 'medium', 'abilities': ['basic_attack', 'charge'], 'damage_type': 'physical', 'dodge_chance': 0.08, 'drops': ['wolf_pelt', 'meat_stew']},
    'forest_troll': {'name': '🌳 Болотный Тролль', 'base_health': 110, 'base_min_physical_damage': 15, 'base_max_physical_damage': 23, 'base_min_magic_damage': 0, 'base_max_magic_damage': 0, 'base_exp': 48, 'base_gold': 36, 'rank': 'D', 'description': 'Тупая гора мышц.', 'image': IMAGE_URLS['orc'], 'difficulty': 'mini_boss', 'abilities': ['basic_attack', 'regeneration'], 'damage_type': 'physical', 'dodge_chance': 0.12, 'drops': ['iron_ore', 'roast_boar']},
    'forest_guardian': {'name': '🌳 Проклятый Энт', 'base_health': 150, 'base_min_physical_damage': 13, 'base_max_physical_damage': 25, 'base_min_magic_damage': 7, 'base_max_magic_damage': 13, 'base_exp': 80, 'base_gold': 64, 'rank': 'D', 'description': 'Древний страж леса.', 'image': IMAGE_URLS['titan'], 'difficulty': 'boss', 'abilities': ['basic_attack', 'root_grab'], 'damage_type': 'mixed', 'dodge_chance': 0.08, 'drops': ['medium_hp', 'wooden_ring', 'apple']},
    'skeleton_warrior': {'name': '💀 Костяной Легионер', 'base_health': 100, 'base_min_physical_damage': 13, 'base_max_physical_damage': 23, 'base_min_magic_damage': 0, 'base_max_magic_damage': 0, 'base_exp': 48, 'base_gold': 32, 'rank': 'C', 'description': 'Скелет в ржавых латах.', 'image': IMAGE_URLS['skeleton'], 'difficulty': 'hard', 'abilities': ['basic_attack', 'shield_bash'], 'damage_type': 'physical', 'dodge_chance': 0.12, 'drops': ['bone_dust']},
    'ghoul': {'name': '🧟 Трупоед', 'base_health': 115, 'base_min_physical_damage': 12, 'base_max_physical_damage': 22, 'base_min_magic_damage': 0, 'base_max_magic_damage': 0, 'base_exp': 52, 'base_gold': 36, 'rank': 'C', 'description': 'Сгорбленная тварь.', 'image': IMAGE_URLS['zombie'], 'difficulty': 'hard', 'abilities': ['basic_attack', 'life_drain'], 'damage_type': 'physical', 'dodge_chance': 0.10, 'drops': ['bone_dust', 'meat_stew']},
    'dark_priest': {'name': '🕯️ Культист Смерти', 'base_health': 90, 'base_min_physical_damage': 7, 'base_max_physical_damage': 13, 'base_min_magic_damage': 15, 'base_max_magic_damage': 28, 'base_exp': 60, 'base_gold': 44, 'rank': 'C', 'description': 'Безумец в балахоне.', 'image': IMAGE_URLS['mage'], 'difficulty': 'hard', 'abilities': ['basic_attack', 'dark_bolt'], 'damage_type': 'magic', 'dodge_chance': 0.15, 'drops': ['small_mp', 'silver_amulet']},
    'crypt_keeper': {'name': '💀 Некромант', 'base_health': 140, 'base_min_physical_damage': 15, 'base_max_physical_damage': 25, 'base_min_magic_damage': 10, 'base_max_magic_damage': 19, 'base_exp': 72, 'base_gold': 56, 'rank': 'C', 'description': 'Хозяин склепа.', 'image': IMAGE_URLS['lich'], 'difficulty': 'mini_boss', 'abilities': ['basic_attack', 'raise_dead'], 'damage_type': 'mixed', 'dodge_chance': 0.18, 'drops': ['bone_dust', 'medium_hp']},
    'catacomb_lord': {'name': '👑 Король Лич', 'base_health': 225, 'base_min_physical_damage': 19, 'base_max_physical_damage': 32, 'base_min_magic_damage': 13, 'base_max_magic_damage': 23, 'base_exp': 160, 'base_gold': 120, 'rank': 'C', 'description': 'Древний правитель.', 'image': IMAGE_URLS['lich'], 'difficulty': 'boss', 'abilities': ['basic_attack', 'royal_decree'], 'damage_type': 'mixed', 'dodge_chance': 0.15, 'drops': ['large_hp', 'gold_ring', 'bone_dust']},
    'dark_knight': {'name': '⚔️ Черный Страж', 'base_health': 150, 'base_min_physical_damage': 19, 'base_max_physical_damage': 32, 'base_min_magic_damage': 0, 'base_max_magic_damage': 0, 'base_exp': 80, 'base_gold': 64, 'rank': 'B', 'description': 'Элитный воин.', 'image': IMAGE_URLS['knight'], 'difficulty': 'very_hard', 'abilities': ['basic_attack', 'shield_wall'], 'damage_type': 'physical', 'dodge_chance': 0.20, 'drops': ['iron_ore', 'medium_hp']},
    'vampire': {'name': '🦇 Носферату', 'base_health': 125, 'base_min_physical_damage': 23, 'base_max_physical_damage': 35, 'base_min_magic_damage': 0, 'base_max_magic_damage': 0, 'base_exp': 96, 'base_gold': 80, 'rank': 'B', 'description': 'Аристократ ночи.', 'image': IMAGE_URLS['vampire'], 'difficulty': 'very_hard', 'abilities': ['basic_attack', 'blood_drain'], 'damage_type': 'physical', 'dodge_chance': 0.25, 'drops': ['elven_wine', 'vampire_fang']},
    'gargoyle': {'name': '🗿 Ожившая Горгулья', 'base_health': 180, 'base_min_physical_damage': 20, 'base_max_physical_damage': 30, 'base_min_magic_damage': 0, 'base_max_magic_damage': 0, 'base_exp': 90, 'base_gold': 70, 'rank': 'B', 'description': 'Каменная тварь.', 'image': IMAGE_URLS['demon'], 'difficulty': 'very_hard', 'abilities': ['basic_attack', 'stone_skin'], 'damage_type': 'physical', 'dodge_chance': 0.05, 'drops': ['iron_ore']},
    'death_knight': {'name': '💀 Генерал Тьмы', 'base_health': 190, 'base_min_physical_damage': 25, 'base_max_physical_damage': 38, 'base_min_magic_damage': 13, 'base_max_magic_damage': 23, 'base_exp': 144, 'base_gold': 112, 'rank': 'B', 'description': 'Командующий проклятым легионом.', 'image': IMAGE_URLS['knight'], 'difficulty': 'mini_boss', 'abilities': ['basic_attack', 'death_coil'], 'damage_type': 'mixed', 'dodge_chance': 0.23, 'drops': ['plate_armor', 'dark_blade']},
    'castle_overlord': {'name': '🏰 Безумный Император', 'base_health': 315, 'base_min_physical_damage': 25, 'base_max_physical_damage': 44, 'base_min_magic_damage': 19, 'base_max_magic_damage': 32, 'base_exp': 280, 'base_gold': 200, 'rank': 'B', 'description': 'Тиран, продавший королевство.', 'image': IMAGE_URLS['vampire'], 'difficulty': 'boss', 'abilities': ['basic_attack', 'royal_command'], 'damage_type': 'mixed', 'dodge_chance': 0.20, 'drops': ['skull_necklace', 'large_hp']},
    'imp': {'name': '😈 Адский бес', 'base_health': 120, 'base_min_physical_damage': 25, 'base_max_physical_damage': 35, 'base_min_magic_damage': 20, 'base_max_magic_damage': 30, 'base_exp': 110, 'base_gold': 90, 'rank': 'A', 'description': 'Мелкий демон.', 'image': IMAGE_URLS['goblin'], 'difficulty': 'extreme', 'abilities': ['basic_attack', 'fireball'], 'damage_type': 'mixed', 'dodge_chance': 0.30, 'drops': ['demon_horn']},
    'demon': {'name': '😈 Демон Разрушения', 'base_health': 190, 'base_min_physical_damage': 32, 'base_max_physical_damage': 50, 'base_min_magic_damage': 13, 'base_max_magic_damage': 25, 'base_exp': 160, 'base_gold': 120, 'rank': 'A', 'description': 'Воплощение ненависти.', 'image': IMAGE_URLS['demon'], 'difficulty': 'extreme', 'abilities': ['basic_attack', 'hellfire'], 'damage_type': 'mixed', 'dodge_chance': 0.25, 'drops': ['demon_horn']},
    'succubus': {'name': '💋 Суккуб', 'base_health': 150, 'base_min_physical_damage': 20, 'base_max_physical_damage': 30, 'base_min_magic_damage': 40, 'base_max_magic_damage': 60, 'base_exp': 180, 'base_gold': 140, 'rank': 'A', 'description': 'Прекрасная и смертоносная.', 'image': IMAGE_URLS['elf'], 'difficulty': 'extreme', 'abilities': ['basic_attack', 'charm'], 'damage_type': 'magic', 'dodge_chance': 0.35, 'drops': ['large_mp']},
    'pit_fiend': {'name': '😈 Архидемон', 'base_health': 275, 'base_min_physical_damage': 35, 'base_max_physical_damage': 53, 'base_min_magic_damage': 25, 'base_max_magic_damage': 40, 'base_exp': 240, 'base_gold': 176, 'rank': 'A', 'description': 'Один из лордов преисподней.', 'image': IMAGE_URLS['demon'], 'difficulty': 'mini_boss', 'abilities': ['basic_attack', 'summon_demons'], 'damage_type': 'mixed', 'dodge_chance': 0.28, 'drops': ['demon_horn', 'large_hp']},
    'demon_general': {'name': '😈 Принц Ада', 'base_health': 440, 'base_min_physical_damage': 38, 'base_max_physical_damage': 63, 'base_min_magic_damage': 32, 'base_max_magic_damage': 50, 'base_exp': 400, 'base_gold': 280, 'rank': 'A', 'description': 'Правая рука Дьявола.', 'image': IMAGE_URLS['demon'], 'difficulty': 'boss', 'abilities': ['basic_attack', 'apocalypse'], 'damage_type': 'mixed', 'dodge_chance': 0.25, 'drops': ['demon_slayer', 'mithril_armor']},
    'void_walker': {'name': '🌑 Странник Пустоты', 'base_health': 300, 'base_min_physical_damage': 40, 'base_max_physical_damage': 60, 'base_min_magic_damage': 40, 'base_max_magic_damage': 60, 'base_exp': 300, 'base_gold': 200, 'rank': 'S', 'description': 'Существо из антиматерии.', 'image': IMAGE_URLS['mage'], 'difficulty': 'legendary', 'abilities': ['basic_attack', 'warp'], 'damage_type': 'mixed', 'dodge_chance': 0.40, 'drops': ['void_crystal']},
    'dragon_ancient': {'name': '🐉 Дракон Хаоса', 'base_health': 500, 'base_min_physical_damage': 44, 'base_max_physical_damage': 69, 'base_min_magic_damage': 32, 'base_max_magic_damage': 50, 'base_exp': 480, 'base_gold': 320, 'rank': 'S', 'description': 'Существо, видевшее рождение звезд.', 'image': IMAGE_URLS['dragon_ancient'], 'difficulty': 'legendary', 'abilities': ['basic_attack', 'dragon_breath'], 'damage_type': 'mixed', 'dodge_chance': 0.30, 'drops': ['dragon_mail', 'large_hp']},
    'final_god': {'name': '⚡ Падший Творец', 'base_health': 1250, 'base_min_physical_damage': 63, 'base_max_physical_damage': 100, 'base_min_magic_damage': 50, 'base_max_magic_damage': 88, 'base_exp': 1200, 'base_gold': 800, 'rank': 'S', 'description': 'Бог, решивший стереть этот мир.', 'image': IMAGE_URLS['fallen_god'], 'difficulty': 'boss', 'abilities': ['basic_attack', 'divine_judgment', 'omnipotence'], 'damage_type': 'mixed', 'dodge_chance': 0.45, 'drops': ['god_killer', 'ambrosia']}
}

# --- ЛОКАЦИИ ---
LOCATIONS = {
    'E': {'name': '🏚️ Руины Деревни', 'description': 'Здесь лишь пепел и безумцы.', 'image': IMAGE_URLS['village'], 'min_level': 1, 'enemies': ['wolf', 'goblin', 'slime', 'goblin_elite', 'training_master']},
    'D': {'name': '🌲 Шепчущий Лес', 'description': 'Тени здесь длиннее, чем кажется.', 'image': IMAGE_URLS['forest'], 'min_level': 10, 'enemies': ['forest_spider', 'ghost', 'wild_boar', 'forest_troll', 'forest_guardian']},
    'C': {'name': '☠️ Катакомбы Скорби', 'description': 'Подземелья, пропахшие гнилью.', 'image': IMAGE_URLS['dungeon'], 'min_level': 20, 'enemies': ['skeleton_warrior', 'ghoul', 'dark_priest', 'crypt_keeper', 'catacomb_lord']},
    'B': {'name': '🏰 Проклятая Цитадель', 'description': 'Обитель вампиров.', 'image': IMAGE_URLS['castle'], 'min_level': 30, 'enemies': ['dark_knight', 'vampire', 'gargoyle', 'death_knight', 'castle_overlord']},
    'A': {'name': '🔥 Врата Ада', 'description': 'Земля раскалена.', 'image': IMAGE_URLS['hell_gate'], 'min_level': 40, 'enemies': ['imp', 'demon', 'succubus', 'pit_fiend', 'demon_general']},
    'S': {'name': '🌌 Трон Хаоса', 'description': 'Пустота за пределами реальности.', 'image': IMAGE_URLS['throne_god'], 'min_level': 50, 'enemies': ['void_walker', 'dragon_ancient', 'final_god']}
}

# --- ФУНКЦИИ ---

async def safe_edit(query, text=None, keyboard=None, media=None):
    """Безопасное редактирование сообщений, чтобы избежать ошибок API Telegram"""
    try:
        if media:
            await query.edit_message_media(media=media, reply_markup=keyboard)
        elif text:
            try:
                await query.edit_message_caption(caption=text, parse_mode='Markdown', reply_markup=keyboard)
            except BadRequest as e:
                # Если у сообщения нет caption (это был просто текст), то редактируем текст
                if "There is no caption" in str(e) or "Message is not modified" not in str(e):
                     await query.edit_message_text(text=text, parse_mode='Markdown', reply_markup=keyboard)
        elif keyboard:
             await query.edit_message_reply_markup(reply_markup=keyboard)
    except BadRequest as e:
        if "Message is not modified" in str(e): return 
        logger.error(f"Ошибка UI: {e}")
        # Если сообщение слишком старое или удалено, шлем новое
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
    # Базовый урон от статов
    base_damage = max(1, character['strength' if damage_type == 'physical' else 'intelligence'] // 2)
    
    # --- БОНУС ЭЛЬФОВ ---
    # Если атакует эльф и использует магию
    if character.get('race') == 'elf' and damage_type == 'magic':
        magic_type = character.get('elf_magic_type')
        if magic_type: # Если магия выбрана
            # Формула: (Уровень / 3) * 3. 
            # Пример: 10 ур = +9 урона. 30 ур = +30 урона.
            elf_bonus = (character['level'] // 3) * 3
            base_damage += elf_bonus
            # Можно даже немного увеличить разброс рандома для магии
            
    # Сопротивление врага
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
    if enemy['name'] == '⚔️ Падший Рыцарь' and random.random() < 0.25:
        dmg = random.randint(enemy['min_physical_damage']*2, enemy['max_physical_damage']*3)
        effect = f"🌪 *ВИХРЬ КЛИНКОВ!* Рыцарь наносит {dmg} урона!"
        log.append(effect)
        return dmg, effect, None
    if random.random() < enemy.get('special_chance', 0.15):
        if not enemy.get('abilities'): return 0, "", None
        ability = random.choice(enemy['abilities'])
        if ability == 'poison_spit':
            dmg = random.randint(5, 10)
            effect = f"Яд нанес {dmg} урона!"
            status = 'poisoned'
        else:
             effect = f"⚠️ {enemy['name']} использует {ability}!"
        log.append(effect)
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
        [InlineKeyboardButton("📜 Гильдия", callback_data='guild_menu')], 
        [InlineKeyboardButton("🏆 Топ игроков", callback_data='top_players')],
        [InlineKeyboardButton("📜 Помощь", callback_data='help'), InlineKeyboardButton("🔄 Обновить", callback_data='refresh')]
    ]
    
    # --- ОТЛАДКА ---
    # Это напечатает расу в консоль (черное окно), когда вы откроете меню.
    # Посмотрите, что там написано.
    print(f"DEBUG: User {user_id} race is '{char['race']}'") 
    
    # --- ПРОВЕРКА РАСЫ ---
    # .lower().strip() защищает от ошибок "Elf " или "ELF"
    if char['race'] and char['race'].lower().strip() == 'elf':
        kb.insert(1, [InlineKeyboardButton("🔮 Магия Древних", callback_data='elf_magic_menu')])
    
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
        
        cost_text = f"({recipe['cost']}g) "
        kb.append([InlineKeyboardButton(f"🔨 {item_data['name']} {cost_text}", callback_data=f"craft_{key}")])
        
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

def get_battle_action_keyboard(level=1):
    kb = [
        [InlineKeyboardButton("⚔️ Атака", callback_data='attack_physical'), InlineKeyboardButton("🔮 Магия", callback_data='attack_magic')],
        [InlineKeyboardButton("🛡 Блок", callback_data='defend'), InlineKeyboardButton("🏃 Сбежать", callback_data='flee')]
    ]
    # Добавляем кнопку способностей, если уровень >= 10
    if level >= 10:
        kb.insert(1, [InlineKeyboardButton("💫 Способности", callback_data='abilities_menu')])
    
    return InlineKeyboardMarkup(kb)
def get_inventory_keyboard(items, page):
    kb = []
    for i in items:
        key = i['item_key']
        item_data = ITEMS_DB.get(key, {})
        # Кнопки использования только для расходников
        if item_data.get('type') in ['food', 'potion']:
            kb.append([InlineKeyboardButton(f"Использовать {i['item_name']} (x{i['quantity']})", callback_data=f"use_{key}")])
        else:
            # Просто отображаем название для экипировки/материалов
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
        await update.message.reply_photo(IMAGE_URLS['village'], caption=f"С возвращением, {char['character_name']}! Темные времена настали, надеюсь ты готов к новым испытаниям.", reply_markup=get_main_menu_keyboard(user.id))
        return MAIN_MENU
    else:
        await update.message.reply_text("Мир погрузился во тьму. Выберите, кем вы родились в этот проклятый век:", reply_markup=get_race_selection_keyboard())
        return CHOOSE_RACE

async def choose_race(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['race'] = query.data.split('_')[1]
    await query.message.reply_text("Как будут звать героя, бросившего вызов Бездне?")
    return ENTER_NAME

async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    user = update.effective_user
    database.create_character(user.id, user.username, name, context.user_data['race'])
    await update.message.reply_photo(IMAGE_URLS['village'], caption="Ваша легенда начинается. Вы стоите посреди руин...", reply_markup=get_main_menu_keyboard(user.id))
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
        await safe_edit(query, text="Куда лежит твой путь, путник?", media=InputMediaPhoto(IMAGE_URLS['forest'], caption="Куда лежит твой путь, путник?", parse_mode='Markdown'), keyboard=get_battle_menu_keyboard(char))
        return BATTLE_MENU
    elif data == 'shop':
        char = database.get_character(user_id)
        txt = f"🏪 *Мрачная лавка*\nТорговец смотрит на тебя из-под капюшона.\nЗолото: {char['gold']}💰"
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
        await query.edit_message_caption("Выберите характеристику для улучшения:", reply_markup=get_level_up_keyboard(char, char['stat_points']))
        return LEVEL_UP
    elif data == 'guild_menu':
        await guild_menu_handler(update, context)
        return GUILD_MENU
    elif data == 'rank_info':
        rank_info = """🏆 *РАНГИ*\n🆕 E: 1-14 ур (Руины)\n🟢 D: 15-24 ур (Лес)\n🔵 C: 25-34 ур (Катакомбы)\n🟣 B: 35-44 ур (Замок)\n🟠 A: 45-54 ур (Ад)\n⚡ S: 55+ ур (Трон Хаоса)"""
        await query.edit_message_caption(rank_info, parse_mode='Markdown', reply_markup=get_main_menu_keyboard(user_id))
    elif data == 'help':
        await help_command(update, context)
    elif data == 'elf_magic_menu':
        await elf_magic_menu_handler(update, context)
    elif data.startswith('set_magic_'):
        # Это нужно, если обработка клика происходит здесь, 
        # но лучше, если она внутри elf_magic_menu_handler.
        # Если вы сделали отдельную функцию elf_magic_menu_handler, этот блок здесь не нужен.
        await elf_magic_menu_handler(update, context)    
    return MAIN_MENU

async def level_up_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id

    if data == 'back_to_main':
        await safe_edit(query, text="В деревне", media=InputMediaPhoto(IMAGE_URLS['village'], caption="В деревне", parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
        return MAIN_MENU
    
    stat_map = {
        'levelup_strength': 'strength',
        'levelup_agility': 'agility',
        'levelup_intelligence': 'intelligence',
        'levelup_vitality': 'vitality'
    }
    
    if data in stat_map:
        stat = stat_map[data]
        success, msg = database.add_stat_point(user_id, stat)
        if success:
            await query.answer(f"Характеристика {stat} повышена!", show_alert=False)
            char = database.get_character(user_id)
            if char['stat_points'] > 0:
                await query.edit_message_reply_markup(reply_markup=get_level_up_keyboard(char, char['stat_points']))
            else:
                await safe_edit(query, text="Очки распределены.", media=InputMediaPhoto(IMAGE_URLS['village'], caption="Очки распределены.", parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
                return MAIN_MENU
        else:
            await query.answer(msg, show_alert=True)
            
    return LEVEL_UP

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
            'enemy_key': enemy_key,
            'log': [f"⚔️ *ВЫЗОВ БРОШЕН!*\n{enemy['description']}"], 
            'turn': 1,
            'status_effects': [],
            'cooldowns': {},
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
        await safe_edit(query, text=txt, keyboard=get_battle_action_keyboard(c['level']), media=None)
    else:
        s['last_image'] = current_image
        media_obj = InputMediaPhoto(current_image, caption=txt, parse_mode='Markdown')
        await safe_edit(query, text=None, media=media_obj, keyboard=get_battle_action_keyboard(c['level']))

async def battle_action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    # 1. Проверяем, идет ли бой
    s = battle_sessions.get(user_id)
    if not s: 
        await query.answer()
        await safe_edit(query, text="⌛ *Бой завершен или сессия истекла.*", keyboard=get_main_menu_keyboard(user_id))
        return MAIN_MENU

    # Защита от двойных нажатий (спама кнопок)
    if s.get('processing'):
        await query.answer("⏳ ...", show_alert=False)
        return IN_BATTLE
    
    # --- 2. ОБРАБОТКА МЕНЮ СПОСОБНОСТЕЙ (НЕ ТРАТИТ ХОД) ---
    if query.data == 'abilities_menu':
        char = s['char']
        race_skills = RACE_ABILITIES.get(char['race'], {})
        kb = []
        
        # Генерируем кнопки навыков
        for lvl, skill in race_skills.items():
            if char['level'] >= lvl:
                # Проверка маны и кулдауна для иконки
                cd_left = s['cooldowns'].get(skill['key'], 0)
                status_icon = "✅"
                if cd_left > 0: status_icon = f"⏳ {cd_left}"
                elif char['mana'] < skill['mana']: status_icon = "💧"
                
                btn_text = f"{skill['name']} ({skill['mana']} MP) {status_icon}"
                kb.append([InlineKeyboardButton(btn_text, callback_data=f"use_skill_{skill['key']}")])
        
        kb.append([InlineKeyboardButton("🔙 Назад в бой", callback_data='back_to_fight')])
        await safe_edit(query, text=None, keyboard=InlineKeyboardMarkup(kb))
        return IN_BATTLE

    if query.data == 'back_to_fight':
        await render_battle(query, user_id)
        return IN_BATTLE

    # --- 3. НАЧАЛО ХОДА (ТРАТИТ ХОД) ---
    s['processing'] = True
    try:
        await query.answer()
        action = query.data
        c, e, log = s['char'], s['enemy'], s['log']
        
        player_damage = 0
        enemy_damage_mod = 1.0 # Модификатор урона по игроку (1.0 = 100%, 0.5 = 50%)
        
        # Уменьшаем кулдауны способностей в начале хода
        for k in list(s['cooldowns'].keys()):
            if s['cooldowns'][k] > 0: s['cooldowns'][k] -= 1

        # === ДЕЙСТВИЯ ИГРОКА ===
        
        # А) Использование способности
        if action.startswith('use_skill_'):
            skill_key = action.split('_')[2]
            
            # Ищем навык в базе
            skill = None
            for lvl, sk in RACE_ABILITIES.get(c['race'], {}).items():
                if sk['key'] == skill_key: skill = sk
            
            if not skill: return IN_BATTLE # Если навык не найден
            
            # Проверки перед использованием
            if s['cooldowns'].get(skill_key, 0) > 0:
                s['processing'] = False
                await query.answer(f"⏳ Перезарядка! Ждите {s['cooldowns'][skill_key]} ход.", show_alert=True)
                return IN_BATTLE
            if c['mana'] < skill['mana']:
                s['processing'] = False
                await query.answer("💧 Не хватает маны!", show_alert=True)
                return IN_BATTLE

            # Списание маны и старт кулдауна
            c['mana'] -= skill['mana']
            s['cooldowns'][skill_key] = skill['cd']
            
            # Эффекты навыков
            if skill['type'] == 'heal':
                heal = int(c['max_health'] * skill['val'])
                c['health'] = min(c['max_health'], c['health'] + heal)
                log.append(f"✨ *{skill['name']}* восстановил {heal} HP!")
            
            elif skill['type'] == 'heal_mana':
                heal = int(c['max_health'] * skill['val'])
                c['health'] = min(c['max_health'], c['health'] + heal)
                log.append(f"🍃 *{skill['name']}* лечит раны!")
            
            elif skill['type'] == 'dmg':
                player_damage = int(c['strength'] * skill['val'])
                log.append(f"⚔️ *{skill['name']}* нанес {player_damage} урона!")

            elif skill['type'] == 'magic_nuke':
                player_damage = int(c['intelligence'] * skill['val'])
                log.append(f"⚡ *{skill['name']}* испепеляет врага на {player_damage}!")
            
            elif skill['type'] == 'lifesteal':
                player_damage = int(c['strength'] * skill['val'])
                heal = int(player_damage * 0.5)
                c['health'] = min(c['max_health'], c['health'] + heal)
                log.append(f"🩸 *{skill['name']}* нанес {player_damage} и вылечил {heal} HP!")
            
            elif skill['type'] == 'buff_def':
                enemy_damage_mod = 0.1 # Враг нанесет только 10% урона
                log.append(f"🛡 *{skill['name']}* поглощает почти весь урон!")
            
            elif skill['type'] == 'buff_str':
                player_damage = int(c['strength'] * 2.0)
                log.append(f"💢 *{skill['name']}* позволяет нанести {player_damage} сокрушительного урона!")
            
            elif skill['type'] == 'stun_dmg':
                player_damage = int(c['strength'] * skill['val'])
                if random.random() < 0.5: # 50% шанс стана
                    enemy_damage_mod = 0.0 # Враг пропускает ход
                    log.append(f"🔨 *{skill['name']}* оглушил врага! ({player_damage} ур.)")
                else:
                    log.append(f"🔨 *{skill['name']}* нанес {player_damage} урона.")
            
            elif skill['type'] == 'dmg_exec':
                base = c['strength'] * skill['val']
                if e['health'] < (e['max_health'] * 0.3):
                    base *= 2
                    log.append("☠️ *КАЗНЬ!* Критический удар по слабому врагу!")
                player_damage = int(base)
                log.append(f"🪓 *{skill['name']}* наносит {player_damage} урона!")

        # Б) Обычные действия
        elif action == 'flee':
            if e.get('is_boss') or e.get('is_mini_boss'):
                log.append("🚫 *ОТ БОССА НЕЛЬЗЯ СБЕЖАТЬ!*")
            elif random.random() < 0.6: # Шанс побега 60%
                database.update_character_stats(user_id, health=c['health'], mana=c['mana'])
                del battle_sessions[user_id]
                txt = "🏃 *ПОЗОРНОЕ БЕГСТВО!*"
                await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['village'], caption=txt, parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
                return MAIN_MENU
            else:
                log.append("⛓ *ПОБЕГ НЕ УДАЛСЯ!*")
        
        elif action == 'defend':
            log.append("🛡 Вы ушли в глухую оборону.")
            enemy_damage_mod = 0.5 # Получаем 50% урона
            
        elif action == 'attack_physical':
            dmg, is_crit = calculate_damage(c, e, 'physical')
            player_damage = dmg
            crit_txt = "💥 *КРИТ!* " if is_crit else ""
            log.append(f"{crit_txt}Вы ударили врага на *{dmg}*!")
                
        elif action == 'attack_magic':
            # 1. Определяем заклинание
            active_spell_key = c.get('elf_active_spell')
            spell = None
            
            # Ищем параметры заклинания в словаре
            if c['race'] == 'elf' and active_spell_key:
                for school in ELF_SPELLS.values():
                    if active_spell_key in school['spells']:
                        spell = school['spells'][active_spell_key]
                        break
            
            # 2. Определяем стоимость маны
            mana_cost = spell['mana'] if spell else 10
            
            # 3. Проверка маны
            if c['mana'] >= mana_cost:
                c['mana'] -= mana_cost
                
                # --- ЕСЛИ ЭТО ОБЫЧНАЯ МАГИЯ (НЕ ЭЛЬФ ИЛИ НЕ ВЫБРАНО) ---
                if not spell:
                    dmg, is_crit = calculate_damage(c, e, 'magic')
                    player_damage = int(dmg * 1.2)
                    crit_txt = " (КРИТ!)" if is_crit else ""
                    log.append(f"🔮 Магия нанесла *{player_damage}* урона{crit_txt}!")
                
                # --- ЕСЛИ ЭТО ЭЛЬФИЙСКОЕ ЗАКЛИНАНИЕ ---
                else:
                    # Базовый маг. урон
                    base_mag = c['intelligence'] // 2
                    is_crit = random.random() < calculate_crit_chance(c['agility'])
                    crit_mult = 1.5 if is_crit else 1.0
                    crit_txt = " (КРИТ!)" if is_crit else ""
                    
                    # Логика эффектов
                    if spell['type'] == 'dmg':
                        dmg = int(base_mag * spell['val'] * crit_mult)
                        # Разброс урона
                        dmg = random.randint(int(dmg*0.9), int(dmg*1.1))
                        player_damage = dmg
                        log.append(f"🔥 *{spell['name']}* нанес {dmg} урона{crit_txt}!")
                        
                    elif spell['type'] == 'drain':
                        dmg = int(base_mag * spell['val'] * crit_mult)
                        player_damage = dmg
                        heal = int(dmg * 0.3) if spell['val'] < 2.0 else int(dmg * 0.5)
                        c['health'] = min(c['max_health'], c['health'] + heal)
                        log.append(f"🌙 *{spell['name']}* вытянул {dmg} жизни (+{heal} HP){crit_txt}!")
                        
                    elif spell['type'] == 'debuff_dmg':
                        dmg = int(base_mag * spell['val'] * crit_mult)
                        player_damage = dmg
                        enemy_damage_mod = 0.5 # Ослабление врага на этот ход
                        log.append(f"🌑 *{spell['name']}* нанес {dmg} урона и ослабил врага!")
                        
                    elif spell['type'] == 'stun':
                        dmg = int(base_mag * spell['val'] * crit_mult)
                        player_damage = dmg
                        if random.random() < 0.4: # 40% шанс стана
                            enemy_damage_mod = 0.0
                            log.append(f"✨ *{spell['name']}* ({dmg} ур.) оглушил врага!")
                        else:
                            log.append(f"✨ *{spell['name']}* нанес {dmg} урона.")

            else:
                log.append("💧 *НЕТ МАНЫ!*")
                player_damage = max(1, c['strength'] // 4)
                log.append(f"👊 Удар рукой на {player_damage}.")
        # Применяем урон игрока по врагу
        if player_damage > 0:
            e['health'] -= player_damage

        # --- 4. ПРОВЕРКА ПОБЕДЫ ---
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
                            # Добавляем предмет (цена 0, эффект 0 - просто материал)
                            database.buy_item(user_id, drop, 'material', item_info['name'], 0, 0)
                            dropped_items.append(item_info['name'])

            # === [НОВОЕ] ОБНОВЛЕНИЕ КВЕСТА ГИЛЬДИИ ===
            # Получаем ID врага из сессии
            enemy_key = s.get('enemy_key') 
            
            # Проверяем, есть ли квест типа "Убить" и совпадает ли цель
            if c.get('quest_type') == 'kill' and c.get('quest_target') == enemy_key:
                # Если квест еще не выполнен полностью
                if c.get('quest_progress') < c.get('quest_goal'):
                    database.update_quest_progress(user_id, 1)
                    # Можно добавить уведомление в лог победы, но это не обязательно

            # Сохранение прогресса
            database.add_experience(user_id, xp_win)
            database.add_gold(user_id, gold_win)
            database.update_character_stats(user_id, health=c['health'], mana=c['mana'], battle_wins=c.get('battle_wins',0)+1)
            
            if e.get('is_boss'): database.increment_boss_kills(user_id, False)
            if e.get('is_mini_boss'): database.increment_boss_kills(user_id, True)
            
            del battle_sessions[user_id]
            
            loot_text = f"\n🎒 Лут: {', '.join(dropped_items)}" if dropped_items else ""
            win_msg = (f"🏆 *ПОБЕДА!*\n\n☠️ {e['name']} повержен.\n💰 +{gold_win}g | 📚 +{xp_win}xp{loot_text}\n"
                       f"⚠️ Здоровье не восстановлено! Посетите магазин.")
            await safe_edit(query, text=win_msg, media=InputMediaPhoto(IMAGE_URLS['village'], caption=win_msg, parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
            return MAIN_MENU

        # --- 5. ХОД ВРАГА (ЕСЛИ ОН ЖИВ) ---
        
        # Если враг не в стане (модификатор 0.0 ставится способностью оглушения)
        if enemy_damage_mod == 0.0:
             log.append("💫 Враг оглушен и пропускает ход!")
        else:
            # Спец атаки врага
            spec_dmg, spec_desc, spec_status = process_enemy_special_attack(e, c, log)
            
            if spec_dmg > 0:
                # Урон от спец атаки (с учетом блока/щита)
                final_dmg = int(spec_dmg * enemy_damage_mod)
                c['health'] -= final_dmg
                if enemy_damage_mod < 1.0:
                    log.append(f"🛡 Щит поглотил часть урона! ({final_dmg})")
            else:
                # Обычная атака врага
                base_dmg, is_dodged = calculate_enemy_damage(e, c)
                if is_dodged:
                    log.append(f"💨 *УВОРОТ!* {e['name']} промазал!")
                else:
                    final_dmg = int(base_dmg * enemy_damage_mod)
                    
                    if enemy_damage_mod < 1.0:
                         log.append(f"🛡 Блок/Щит! Урон снижен до *{final_dmg}*")
                    else:
                         log.append(f"💔 {e['name']} нанес *{final_dmg}* урона!")
                    
                    c['health'] -= final_dmg

        # --- 6. ПРОВЕРКА ПОРАЖЕНИЯ ---
        if c['health'] <= 0:
            database.update_character_stats(user_id, health=0, battle_losses=c.get('battle_losses',0)+1)
            if user_id in battle_sessions:
                del battle_sessions[user_id]
            
            death_msg = "💀 *ВЫ ПОГИБЛИ...*\n\nТемные жрецы нашли ваше тело и воскресили в деревне, но часть души была утеряна в Бездне."
            
            # Совет для новичков
            if c['level'] < 10 and (e.get('is_boss') or e.get('is_mini_boss')):
                death_msg += "\n\n💡 *Урок:* Вы слишком слабы для Боссов. Прокачайтесь до 10 уровня, чтобы открыть Магию!"
            
            death_image = IMAGE_URLS.get('dungeon', 'https://i.pinimg.com/736x/93/84/9f/93849fa5c577756a346cd6c4172b384d.jpg')
            
            await safe_edit(query, text=death_msg, media=InputMediaPhoto(death_image, caption=death_msg, parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
            return MAIN_MENU
        
        # Переход к следующему ходу
        s['turn'] += 1
        await render_battle(query, user_id)
        
    finally:
        # Снимаем блокировку обработки, чтобы кнопки снова работали
        if user_id in battle_sessions:
            battle_sessions[user_id]['processing'] = False
            
    return IN_BATTLE

# --- ГЕНЕРАТОР ЗАДАНИЙ ---
def generate_daily_quests(rank):
    """Генерирует 3 случайных квеста для ранга игрока"""
    quests = []
    
    # Определяем доступных врагов для ранга
    available_enemies = []
    available_drops = []
    
    # Собираем врагов, подходящих по рангу (или чуть слабее)
    ranks_order = ['E', 'D', 'C', 'B', 'A', 'S']
    current_rank_idx = ranks_order.index(rank)
    
    for key, data in BASE_ENEMIES.items():
        enemy_rank_idx = ranks_order.index(data.get('rank', 'E'))
        if enemy_rank_idx <= current_rank_idx:
            available_enemies.append(key)
            if data.get('drops'):
                for drop in data['drops']:
                    available_drops.append(drop)
    
    if not available_enemies: available_enemies = ['wolf'] # Заглушка
    
    # Генерируем 3 варианта
    for _ in range(3):
        q_type = random.choice(['kill', 'kill', 'collect']) # Убийство падает чаще
        
        if q_type == 'kill':
            target = random.choice(available_enemies)
            enemy_name = BASE_ENEMIES[target]['name']
            # Кол-во зависит от ранга (E: 3-5, S: 10-15)
            count = random.randint(3, 5) + (current_rank_idx * 2)
            gold = count * BASE_ENEMIES[target].get('base_gold', 5) * 1.5
            exp = count * BASE_ENEMIES[target].get('base_exp', 5) * 1.5
            quests.append({
                'type': 'kill', 'target': target, 'goal': count, 
                'gold': int(gold), 'exp': int(exp), 
                'desc': f"Убить: {enemy_name} ({count} шт.)"
            })
            
        elif q_type == 'collect':
            if not available_drops: 
                continue 
            target = random.choice(available_drops)
            item_name = ITEMS_DB.get(target, {'name': target})['name']
            count = random.randint(2, 4) + current_rank_idx
            gold = count * ITEMS_DB.get(target, {}).get('price', 5) * 2.0
            exp = gold * 0.8
            quests.append({
                'type': 'collect', 'target': target, 'goal': count, 
                'gold': int(gold), 'exp': int(exp), 
                'desc': f"Принести: {item_name} ({count} шт.)"
            })
            
    return quests

# --- ХЕНДЛЕР ГИЛЬДИИ ---
async def guild_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    char = database.get_character(user_id)
    
    # --- 1. КНОПКА НАЗАД ---
    if query.data == 'back_to_main':
        await safe_edit(query, text="В деревне", media=InputMediaPhoto(IMAGE_URLS['village'], caption="В деревне", parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
        return MAIN_MENU

    # --- 2. ПЛАТНОЕ ОБНОВЛЕНИЕ (REROLL) ---
    if query.data == 'reroll_quests':
        reroll_price = 50
        if char['gold'] >= reroll_price:
            # Списываем золото
            database.add_gold(user_id, -reroll_price)
            # Генерируем новые
            new_quests = generate_daily_quests(char['rank'])
            database.save_daily_quests(user_id, new_quests)
            
            await query.answer(f"🔄 Список обновлен! (-{reroll_price}g)", show_alert=True)
            # Перезагружаем меню (оно само подтянет новые квесты из базы)
            await guild_menu_handler(update, context)
            return GUILD_MENU
        else:
            await query.answer(f"💸 Не хватает золота! Нужно {reroll_price}g", show_alert=True)
            return GUILD_MENU

    # --- 3. ВЗЯТИЕ КВЕСТА ---
    if query.data.startswith('take_quest_'):
        parts = query.data.split('_')
        try:
            q_exp = int(parts[-1])
            q_gold = int(parts[-2])
            q_goal = int(parts[-3])
            q_type = parts[2]
            q_target = "_".join(parts[3:-3])
            
            database.take_quest(user_id, q_type, q_target, q_goal, q_gold, q_exp)
            await query.answer("✅ Контракт подписан!", show_alert=True)
            await guild_menu_handler(update, context)
            return GUILD_MENU
        except Exception as e:
            print(f"Quest error: {e}")
            await query.answer("Ошибка контракта.", show_alert=True)
            return GUILD_MENU

    # --- 4. ЗАВЕРШЕНИЕ КВЕСТА ---
    if query.data == 'complete_quest':
        success, msg = database.complete_quest(user_id)
        if success:
            database.add_experience(user_id, 0)
            await query.answer("🏆 Награда получена!", show_alert=True)
            await safe_edit(query, text=msg, media=InputMediaPhoto(IMAGE_URLS['guild'], caption=msg, parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
            return MAIN_MENU
        else:
            await query.answer(f"❌ {msg}", show_alert=True)
            return GUILD_MENU

    # --- 5. ОТОБРАЖЕНИЕ МЕНЮ ---
    
    # А) Если квест уже взят - показываем прогресс
    if char.get('quest_target'):
        target_name = ""
        progress_txt = ""
        
        if char['quest_type'] == 'kill':
            mob_info = BASE_ENEMIES.get(char['quest_target'])
            target_name = mob_info['name'] if mob_info else char['quest_target']
            progress_txt = f"☠️ Убито: {char['quest_progress']}/{char['quest_goal']}"
        else:
            item_info = ITEMS_DB.get(char['quest_target'])
            target_name = item_info['name'] if item_info else char['quest_target']
            items = database.get_inventory(user_id)
            inv_qty = 0
            for i in items:
                if i['item_key'] == char['quest_target']:
                    inv_qty = i['quantity']
            progress_txt = f"🎒 Собрано: {inv_qty}/{char['quest_goal']}"
        
        txt = (f"📜 *ТЕКУЩИЙ КОНТРАКТ*\n\n"
               f"Цель: {target_name}\n"
               f"{progress_txt}\n\n"
               f"💰 Награда: {char['quest_reward_gold']}g | 📚 {char['quest_reward_exp']}xp")
        
        kb = [[InlineKeyboardButton("✅ Завершить и получить награду", callback_data='complete_quest')],
              [InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]]
        await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['guild'], caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))
        return GUILD_MENU

    # Б) Проверка: делал ли уже квест сегодня (завершенный)
    today = datetime.now().date()
    last_quest_done = char.get('last_quest_date')
    if isinstance(last_quest_done, str):
        last_quest_done = datetime.strptime(last_quest_done, '%Y-%m-%d').date()
        
    if last_quest_done == today:
        txt = "📜 *Доска пуста*\n\nМастер гильдии говорит: \"На сегодня работы нет. Приходи завтра!\""
        await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['guild'], caption=txt, parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
        return MAIN_MENU

    # В) ПОЛУЧЕНИЕ СПИСКА ЗАДАНИЙ (Сохраненные или Новые)
    stored_quests, last_refresh = database.get_stored_quests(user_id)
    
    # Исправление даты из БД
    if isinstance(last_refresh, str):
        last_refresh = datetime.strptime(last_refresh, '%Y-%m-%d').date()

    quests_to_show = []
    
    # Логика: Если есть сохраненные И они сегодняшние -> показываем их.
    # Иначе -> генерируем новые и сохраняем.
    if stored_quests and last_refresh == today:
        quests_to_show = stored_quests
    else:
        quests_to_show = generate_daily_quests(char['rank'])
        database.save_daily_quests(user_id, quests_to_show)

    # Г) Отображение списка
    txt = "📜 *ДОСКА ОБЪЯВЛЕНИЙ*\nВыберите задание на сегодня.\n_(Список обновляется раз в сутки)_"
    kb = []
    
    for q in quests_to_show:
        cb_data = f"take_quest_{q['type']}_{q['target']}_{q['goal']}_{q['gold']}_{q['exp']}"
        btn_txt = f"{q['desc']} (💰{q['gold']} 📚{q['exp']})"
        kb.append([InlineKeyboardButton(btn_txt, callback_data=cb_data)])
    
    # Кнопка платного обновления
    kb.append([InlineKeyboardButton("🔄 Новые задания (50g)", callback_data='reroll_quests')])
    kb.append([InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')])
    
    await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['guild'], caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))
    return GUILD_MENU

async def elf_magic_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    # 1. ОБРАБОТКА КНОПКИ "НАЗАД В ГЛАВНОЕ"
    if query.data == 'back_to_main':
        await query.answer()
        await safe_edit(query, text="В деревне", media=InputMediaPhoto(IMAGE_URLS['village'], caption="В деревне", parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
        return MAIN_MENU

    # 2. ОБРАБОТКА ВЫБОРА ШКОЛЫ (Например, нажали "Солнце")
    if query.data.startswith('school_'):
        school_key = query.data.split('_')[1] # sun, moon, star
        char = database.get_character(user_id)
        
        school_data = ELF_SPELLS[school_key]
        active_spell = char.get('elf_active_spell')
        
        txt = f"📖 *{school_data['name']}*\nВыберите заклинание, которое будете использовать в бою:\n\n"
        kb = []
        
        for key, spell in school_data['spells'].items():
            # Проверяем уровень
            status = "🔒 (Нужен ур. " + str(spell['lvl']) + ")"
            if char['level'] >= spell['lvl']:
                if active_spell == key:
                    status = "✅ АКТИВНО"
                else:
                    status = "Выбрать"
                    
            btn_text = f"{spell['name']} ({spell['mana']} MP) - {status}"
            
            # Если уровень позволяет, даем выбрать
            if char['level'] >= spell['lvl']:
                kb.append([InlineKeyboardButton(btn_text, callback_data=f"set_spell_{key}")])
            else:
                kb.append([InlineKeyboardButton(f"🔒 {spell['name']} (Ур. {spell['lvl']})", callback_data="ignore")])
                
        kb.append([InlineKeyboardButton("🔙 К списку школ", callback_data='elf_magic_menu')])
        
        await safe_edit(query, text=txt, keyboard=InlineKeyboardMarkup(kb))
        return MAIN_MENU # Остаемся в этом же состоянии

    # 3. ОБРАБОТКА ВЫБОРА ЗАКЛИНАНИЯ
    if query.data.startswith('set_spell_'):
        spell_key = query.data.split('_', 2)[2]
        database.set_elf_spell(user_id, spell_key)
        await query.answer("Заклинание подготовлено!", show_alert=True)
        # Возвращаемся в меню школ
        await elf_magic_menu_handler(update, context) 
        return MAIN_MENU

    # 4. ГЛАВНОЕ МЕНЮ МАГИИ (СПИСОК ШКОЛ)
    # Сюда попадаем по кнопке из главного меню или по "Назад к списку школ"
    char = database.get_character(user_id)
    
    # Определяем текущее активное заклинание для красоты
    curr_spell_key = char.get('elf_active_spell')
    curr_spell_name = "Не выбрано (Будет обычная магия)"
    
    # Ищем название активного спелла
    for school in ELF_SPELLS.values():
        if curr_spell_key in school['spells']:
            curr_spell_name = school['spells'][curr_spell_key]['name']
            break

    txt = (f"🧝‍♀️ *Магический Гримуар*\n\n"
           f"Здесь вы выбираете, какую магию использовать кнопкой «🔮 Магия» в бою.\n"
           f"⚡ Активное заклинание: *{curr_spell_name}*\n\n"
           f"Выберите школу:")
    
    kb = [
        [InlineKeyboardButton("☀️ Солнце (Урон)", callback_data='school_sun')],
        [InlineKeyboardButton("🌙 Луна (Вампиризм)", callback_data='school_moon')],
        [InlineKeyboardButton("✨ Звезды (Контроль)", callback_data='school_star')],
        [InlineKeyboardButton("🔙 Назад в меню", callback_data='back_to_main')]
    ]
    
    # Картинка мага
    img = IMAGE_URLS.get('mage', 'https://i.pinimg.com/736x/9f/8e/25/9f8e2507aceaa217060d249c308e2a13.jpg')
    
    await safe_edit(query, text=txt, media=InputMediaPhoto(img, caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))
    return MAIN_MENU
    
async def shop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    char = database.get_character(user_id)
    
    if data == 'back_to_main':
        await query.answer()
        await safe_edit(query, text="В деревне", media=InputMediaPhoto(IMAGE_URLS['village'], caption="В деревне", parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
        return MAIN_MENU
    
    elif data == 'shop': # Возврат к категориям
        txt = f"🏪 *Мрачная лавка*\nЗолото: {char['gold']}💰\nЧего желаете?"
        await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['shop'], caption=txt, parse_mode='Markdown'), keyboard=get_shop_categories_keyboard())
        return SHOP_MENU
    
    elif data.startswith('shop_cat_'):
        cat = data.split('_')[2] # food, weapon, armor, mat, acc
        
        # Заголовки для категорий
        cat_names = {
            'food': '🍖 Еда и Зелья', 
            'mat': '🧱 Ресурсы', 
            'weapon': '⚔️ Оружие', 
            'armor': '🛡️ Броня', 
            'acc': '💍 Аксессуары'
        }
        
        # Формируем текст описания
        txt = f"🛒 *{cat_names.get(cat, 'Товары')}*\n_Нажми на кнопку ниже, чтобы купить:_\n\n"
        
        items_found = False
        for key, item in ITEMS_DB.items():
            if item.get('cat') == cat:
                items_found = True
                
                # Формируем строку эффекта
                effect_str = ""
                if item['type'] == 'food': 
                    effect_str = f" (+{item['effect']} ❤️)"
                elif item['type'] == 'potion': 
                    if 'mp' in key or 'mana' in key: effect_str = f" (+{item['effect']} 🌀)"
                    else: effect_str = f" (+{item['effect']} ❤️)"
                elif item['type'] == 'weapon': 
                    effect_str = f" (+{item['effect']} ⚔️)"
                elif item['type'] == 'armor': 
                    effect_str = f" (+{item['effect']} 🛡)"
                elif item['type'] == 'artifact': 
                    effect_str = f" (+{item['effect']} 🧠)"
                
                # Добавляем в общий текст
                txt += f"▪️ *{item['name']}* — {item['price']}g\n"
                txt += f"   _{item['desc']}_{effect_str}\n\n"

        if not items_found:
            txt += "В этой категории пока пусто..."

        # Обрезаем, если текст слишком длинный (лимит телеграма 1024)
        if len(txt) > 1000: txt = txt[:1000] + "..."

        # ВАЖНО: Передаем InputMediaPhoto снова, чтобы обновился и текст, и картинка
        # Используем ту же картинку магазина
        media = InputMediaPhoto(IMAGE_URLS['shop'], caption=txt, parse_mode='Markdown')
        
        await safe_edit(query, text=txt, media=media, keyboard=get_shop_items_keyboard(cat, char['gold']))
        return SHOP_MENU
    
    elif data.startswith('buy_'):
        item_key = data.split('_', 1)[1]
        item = ITEMS_DB.get(item_key)
        
        if not item: return SHOP_MENU

        # Проверка ранга
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
            res, msg = database.buy_item(user_id, item_key, item['type'], item['name'], item['price'], item.get('effect', 0))
            await query.answer(msg, show_alert=True)
            
            # Обновляем клавиатуру и баланс (рекурсивно вызываем показ категории)
            # Чтобы обновить баланс золота в тексте, нам нужно заново сгенерировать меню этой категории
            # Проще всего имитировать нажатие на категорию снова:
            new_data = f"shop_cat_{item['cat']}"
            
            # Небольшой хак: меняем data в объекте query и вызываем shop_handler снова
            query.data = new_data
            await shop_handler(update, context)
            return SHOP_MENU
        else:
            await query.answer("💸 Не хватает золота!", show_alert=True)
            
    return SHOP_MENU
async def show_craft_menu(query, user_id):
    items = database.get_inventory(user_id)
    inv_dict = {i['item_key']: i['quantity'] for i in items}
    
    txt = "🛠 *Кузница*\nДревний мастер смотрит на твои трофеи. Для создания предметов нужны ресурсы и золото.\n━━━━━━━━━━━━━━━━\n"
    
    for key, recipe in CRAFT_RECIPES.items():
        result_item = ITEMS_DB.get(recipe['result'])
        if not result_item: continue
        
        # Заголовок рецепта
        txt += f"🔸 *{result_item['name']}* (Цена: {recipe['cost']}g)\n"
        
        # Список материалов
        mats_list = []
        can_craft = True
        
        for mat_key, required_amount in recipe['mats'].items():
            mat_info = ITEMS_DB.get(mat_key)
            mat_name = mat_info['name'] if mat_info else mat_key
            user_amount = inv_dict.get(mat_key, 0)
            
            # Ставим галочку или крестик
            if user_amount >= required_amount:
                mark = "✅"
            else:
                mark = "❌"
                can_craft = False
                
            mats_list.append(f"{mark} {mat_name}: {user_amount}/{required_amount}")
        
        txt += "\n".join(mats_list) + "\n\n"

    # Если текст слишком длинный для подписи к фото, отправляем просто текст
    # Но так как у нас safe_edit умеет менять медиа, попробуем обновить описание
    try:
        await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['craft'], caption=txt[:1024], parse_mode='Markdown'), keyboard=get_craft_keyboard(inv_dict))
    except Exception:
        # Если описание не влезает в caption (лимит 1024), шлем без картинки или сокращаем
        await safe_edit(query, text=txt, keyboard=get_craft_keyboard(inv_dict))

async def craft_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    
    # 1. Обработка кнопки "Назад"
    if data == 'back_to_main':
        await safe_edit(query, text="В деревне", media=InputMediaPhoto(IMAGE_URLS['village'], caption="В деревне", parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
        return MAIN_MENU
    
    # 2. Обработка крафта
    elif data.startswith('craft_'):
        # --- ИСПРАВЛЕНИЕ ТУТ ---
        # Было: recipe_key = data.split('_')[1] (теряло часть названия, если в нем были подчеркивания)
        # Стало: data.split('_', 1)[1] (отрезает только первое слово "craft", остальное оставляет целиком)
        recipe_key = data.split('_', 1)[1] 
        
        recipe = CRAFT_RECIPES.get(recipe_key)
        
        # Если рецепт не найден (например, старая кнопка), обновляем меню
        if not recipe: 
            await query.answer("Рецепт устарел или не найден.", show_alert=True)
            await show_craft_menu(query, user_id)
            return CRAFT_MENU
        
        # 3. Проверка золота
        char = database.get_character(user_id)
        if char['gold'] < recipe['cost']:
            await query.answer(f"⚠️ Не хватает золота! Нужно {recipe['cost']}g", show_alert=True)
            return CRAFT_MENU
            
        # 4. Проверка материалов
        items = database.get_inventory(user_id)
        inv_dict = {i['item_key']: i['quantity'] for i in items}
        
        # Сначала проверяем ВСЕ материалы
        for mat, amt in recipe['mats'].items():
            if inv_dict.get(mat, 0) < amt:
                # Получаем красивое имя материала
                mat_name = ITEMS_DB.get(mat, {'name': mat})['name']
                await query.answer(f"⚠️ Не хватает: {mat_name}", show_alert=True)
                return CRAFT_MENU
        
        # 5. Списываем материалы
        # Используем новую функцию remove_item, которую вы добавили в database.py
        for mat, amt in recipe['mats'].items():
            success = database.remove_item(user_id, mat, amt)
            if not success:
                await query.answer("❌ Ошибка при списании материалов!", show_alert=True)
                return CRAFT_MENU

        # 6. Создаем предмет
        result_item = ITEMS_DB[recipe['result']]
        
        res, msg = database.buy_item(
            user_id, 
            recipe['result'], 
            result_item['type'], 
            result_item['name'], 
            recipe['cost'], 
            result_item.get('effect', 0)
        )
        
        if res:
            await query.answer(f"✅ Успех! Создано: {result_item['name']}", show_alert=True)
            # Обновляем меню, чтобы показать новые остатки ресурсов
            await show_craft_menu(query, user_id)
        else:
            await query.answer(f"❌ Ошибка крафта: {msg}", show_alert=True)
            
    return CRAFT_MENU

async def inventory_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    # Не делаем query.answer() тут, чтобы не сбивать уведомления от use_item
    data = query.data
    user_id = query.from_user.id
    
    if data == 'back_to_main':
        await query.answer()
        await safe_edit(query, text="Главное меню", media=InputMediaPhoto(IMAGE_URLS['village'], caption="Главное меню", parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
        return MAIN_MENU
    
    elif data.startswith('use_'):
        key = data.split('_', 1)[1]
        item = ITEMS_DB.get(key)
        effect = item['effect'] if item else 0
        
        # Используем предмет
        res, msg = database.use_item(user_id, key, item['type'], item['name'], effect)
        await query.answer(msg, show_alert=True) # Показываем всплывающее окно
        
        # Сразу обновляем меню, чтобы показать новые HP и количество предметов
        items = database.get_inventory(user_id)
        char = database.get_character(user_id) # Загружаем обновленного героя
        
        # Показываем HP прямо в заголовке инвентаря
        txt = f"🎒 *Инвентарь*\n❤️ Здоровье: {char['health']}/{char['max_health']}\n🌀 Мана: {char['mana']}/{char['max_mana']}\n\nНажми на предмет, чтобы использовать:"
        
        kb = get_inventory_keyboard(items, 0) if items else get_main_menu_keyboard(user_id)
        
        # Обновляем текст сообщения
        try:
             await query.edit_message_caption(caption=txt, parse_mode='Markdown', reply_markup=kb)
        except BadRequest:
             # Если текст не изменился (например, HP полное), игнорируем ошибку
             pass
        
        if not items:
            await safe_edit(query, text="Ваш мешок пуст.", media=InputMediaPhoto(IMAGE_URLS['village'], caption="Ваш мешок пуст.", parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
            return MAIN_MENU
            
    elif data == 'ignore':
        await query.answer("Это экипировка. Она работает пассивно (дает статы сразу при покупке).", show_alert=True)

    return INVENTORY_MENU

async def show_inventory_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query if update.callback_query else update
    user_id = query.from_user.id
    items = database.get_inventory(user_id)
    txt = "Инвентарь:" if items else "Ваш мешок пуст."
    kb = get_inventory_keyboard(items, 0) if items else get_main_menu_keyboard(user_id)
    await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['inventory'], caption=txt, parse_mode='Markdown'), keyboard=kb)
    return INVENTORY_MENU

async def show_top_players(query, user_id):
    top_players = database.get_top_players(10)
    top_text = "🏆 *ЛЕГЕНДЫ ЭТОГО МИРА*\n━━━━━━━━━━━━━━━━\n"
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
    text = (
        "🆘 *Книга Знаний*\n\n"
        "• 📜 **Герой** — Ваши характеристики.\n"
        "• ⚔️ **Битва** — Сражения за золото и опыт.\n"
        "• 🛍 **Лавка** — Покупка снаряжения.\n"
        "• 🛠 **Кузница** — Крафт редких вещей.\n\n"
        "✨ **СИЛА РАСЫ:**\n"
        "На *10, 25 и 40 уровне* открываются уникальные способности (кнопка появится в бою). \n"
        "⚠️ *Совет:* Не пытайтесь убить Боссов без способностей — это верная смерть!\n\n"
        "❤️ **Важно:** Здоровье не восстанавливается само (только 5% в минуту). Пейте зелья!"
    )
    if update.callback_query:
         await safe_edit(update.callback_query, text=text, media=InputMediaPhoto(IMAGE_URLS['village'], caption=text, parse_mode='Markdown'), keyboard=get_main_menu_keyboard(update.effective_user.id))
    else:
         await update.message.reply_text(text, parse_mode='Markdown')
async def daily_reminder(context: ContextTypes.DEFAULT_TYPE):
    users = database.get_all_users()
    for uid in users:
        try: await context.bot.send_message(chat_id=uid, text="🌅 Солнце встает над руинами мира.\nТвой меч заржавел? Пора в бой! Нажми /start")
        except: pass

async def unknown_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перенаправляет любые текстовые сообщения на старт"""
    await update.message.reply_text("Твой голос тонет в пустоте... \nНапиши /start, чтобы пробудиться.")

async def unknown_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text("Это видение уже рассеялось. Напиши /start.")
    except: pass

def main():
    # 1. Инициализируем базу данных
    database.init_db()
    
    # 2. Создаем приложение БЕЗ JobQueue
    # Это уберет ошибку "No JobQueue set up"
    app = Application.builder().token(TOKEN).build()
    
    # 3. Настраиваем диалоги
    # Мы УБРАЛИ per_message=True, так как это ломает кнопку /start
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSE_RACE: [CallbackQueryHandler(choose_race, pattern='^race_')],
            ENTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_name)],
            MAIN_MENU: [CallbackQueryHandler(main_menu_handler)],
            BATTLE_MENU: [CallbackQueryHandler(battle_menu_handler)],
            IN_BATTLE: [CallbackQueryHandler(battle_action_handler)],
            GUILD_MENU: [CallbackQueryHandler(guild_menu_handler)],
            SHOP_MENU: [CallbackQueryHandler(shop_handler)],
            CRAFT_MENU: [CallbackQueryHandler(craft_handler)],
            LEVEL_UP: [CallbackQueryHandler(level_up_handler)],
            INVENTORY_MENU: [CallbackQueryHandler(inventory_menu_handler)]
        },
        fallbacks=[CommandHandler('start', start)]
    )
    
    app.add_handler(conv)
    app.add_handler(CommandHandler('help', help_command))
    
    # Хендлер для неизвестного текста
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_text))
    
    # Хендлер для старых кнопок
    app.add_handler(CallbackQueryHandler(unknown_callback))
    
    print("⚔️ Бот Темного Фентези перезапущен! Нажмите /start")
    
    # Запуск (блокирующий процесс)
    # Запуск
    app.run_polling()
if __name__ == '__main__':
    main()
