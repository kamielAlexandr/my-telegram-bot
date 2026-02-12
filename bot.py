import os
import logging
import random
import html
from datetime import datetime, time
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    ContextTypes, ConversationHandler, MessageHandler, filters
)
import database

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния
CHOOSE_RACE, ENTER_NAME, MAIN_MENU, BATTLE_MENU, IN_BATTLE, SHOP_MENU, LEVEL_UP, INVENTORY_MENU = range(8)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
battle_sessions = {}

# --- КОНТЕНТ (ИЗОБРАЖЕНИЯ ОСТАЛИСЬ ПРЕЖНИМИ) ---
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

# ОБНОВЛЕННЫЕ ОПИСАНИЯ ПРЕДМЕТОВ (ЛОР)
SHOP_ITEMS = {
    'small_health_potion': {'name': '💊 Малое зелье здоровья', 'description': 'Мутная красная жидкость с металлическим привкусом. Затягивает легкие раны (+20 HP).', 'price': 40, 'type': 'potion', 'effect': 20, 'available': True, 'required_rank': 'E'},
    'large_health_potion': {'name': '💊 Большое зелье здоровья', 'description': 'Густой эликсир в склянке из темного стекла. Спасает от смертельных ран (+40 HP).', 'price': 75, 'type': 'potion', 'effect': 40, 'available': True, 'required_rank': 'D'},
    'small_mana_potion': {'name': '🔮 Малое зелье маны', 'description': 'Слабо светящаяся голубая эссенция. Восстанавливает крупицы магической силы (+15 MP).', 'price': 35, 'type': 'potion', 'effect': 15, 'available': True, 'required_rank': 'E'},
    'large_mana_potion': {'name': '🔮 Большое зелье маны', 'description': 'Концентрированная магическая энергия. Позволяет творить сильные заклинания (+30 MP).', 'price': 65, 'type': 'potion', 'effect': 30, 'available': True, 'required_rank': 'D'},
    'rank_d_weapon': {'name': '⚔️ Меч наемника (D)', 'description': 'Тяжелый меч с зазубринами от прошлых битв. Надежнее ржавой железки (+3 Силы).', 'price': 300, 'type': 'weapon', 'effect': 3, 'available': True, 'required_rank': 'D'},
    'rank_c_armor': {'name': '🛡️ Кольчуга стража (C)', 'description': 'Помятая кольчуга, снятая с мертвого стражника. Все еще держит удар (+5 Живучести).', 'price': 400, 'type': 'armor', 'effect': 5, 'available': True, 'required_rank': 'C'},
    'rank_b_artifact': {'name': '💎 Око Бездны (B)', 'description': 'Древний амулет, пульсирующий темной энергией. Шепчет забытые тайны (+8 Интеллекта).', 'price': 600, 'type': 'artifact', 'effect': 8, 'available': True, 'required_rank': 'B'},
    'ring_of_agility': {'name': '💍 Кольцо Тени (C)', 'description': 'Позволяет владельцу двигаться быстрее ветра, ускользая от ударов (+5 Ловкости).', 'price': 450, 'type': 'artifact', 'effect': 5, 'available': True, 'required_rank': 'C'}
}

# ОБНОВЛЕННЫЕ ОПИСАНИЯ ВРАГОВ (ЛОР)
BASE_ENEMIES = {
    'wolf': {'name': '🐺 Бешеный Волк', 'base_health': 35, 'base_min_physical_damage': 5, 'base_max_physical_damage': 8, 'base_min_magic_damage': 0, 'base_max_magic_damage': 0, 'base_exp': 12, 'base_gold': 8, 'rank': 'E', 'description': 'Облезлый зверь с горящими безумием глазами, вечно голодный порождение пустошей.', 'image': IMAGE_URLS['wolf'], 'difficulty': 'easy', 'abilities': ['basic_attack'], 'damage_type': 'physical', 'dodge_chance': 0.08, 'physical_resistance': 0.15, 'magic_resistance': 0.0, 'special_chance': 0.15, 'attack_range': 'melee'},
    'goblin': {'name': '👹 Гоблин-мародер', 'base_health': 40, 'base_min_physical_damage': 6, 'base_max_physical_damage': 10, 'base_min_magic_damage': 0, 'base_max_magic_damage': 0, 'base_exp': 16, 'base_gold': 12, 'rank': 'E', 'description': 'Подлое и трусливое создание, сбившееся в стаю ради выживания. Не знает жалости.', 'image': IMAGE_URLS['goblin'], 'difficulty': 'easy', 'abilities': ['basic_attack', 'dirty_trick'], 'damage_type': 'physical', 'dodge_chance': 0.12, 'physical_resistance': 0.05, 'magic_resistance': 0.0, 'special_chance': 0.20, 'attack_range': 'melee'},
    'slime': {'name': '🟢 Ядовитая Слизь', 'base_health': 45, 'base_min_physical_damage': 3, 'base_max_physical_damage': 8, 'base_min_magic_damage': 2, 'base_max_magic_damage': 5, 'base_exp': 10, 'base_gold': 7, 'rank': 'E', 'description': 'Аморфная масса, разъедающая плоть. Результат магических экспериментов прошлого.', 'image': IMAGE_URLS['slime'], 'difficulty': 'easy', 'abilities': ['basic_attack', 'poison_spit'], 'damage_type': 'mixed', 'dodge_chance': 0.03, 'physical_resistance': 0.35, 'magic_resistance': 0.15, 'special_chance': 0.25, 'poison_chance': 0.35, 'attack_range': 'ranged'},
    'goblin_elite': {'name': '👹 Гоблин-вожак', 'base_health': 75, 'base_min_physical_damage': 10, 'base_max_physical_damage': 18, 'base_min_magic_damage': 0, 'base_max_magic_damage': 0, 'base_exp': 28, 'base_gold': 20, 'rank': 'E', 'description': 'Крупнее и злее своих сородичей. Носит броню, снятую с убитых охотников.', 'image': IMAGE_URLS['hot_goblin'], 'difficulty': 'mini_boss', 'abilities': ['basic_attack', 'power_strike', 'goblin_shout'], 'damage_type': 'physical', 'dodge_chance': 0.15, 'physical_resistance': 0.20, 'magic_resistance': 0.08, 'special_chance': 0.30, 'mini_boss_bonus': 1.8, 'attack_range': 'melee'},
    'training_master': {'name': '⚔️ Забытый Ветеран', 'base_health': 100, 'base_min_physical_damage': 10, 'base_max_physical_damage': 20, 'base_min_magic_damage': 0, 'base_max_magic_damage': 0, 'base_exp': 40, 'base_gold': 32, 'rank': 'E', 'description': 'Старый воин, чье тело покрыто шрамами. Он учит новичков выживать в этом проклятом мире.', 'image': IMAGE_URLS['knight'], 'difficulty': 'boss', 'abilities': ['basic_attack', 'training_strike', 'defensive_stance', 'encouraging_shout'], 'damage_type': 'physical', 'dodge_chance': 0.20, 'physical_resistance': 0.25, 'magic_resistance': 0.15, 'special_chance': 0.35, 'boss_bonus': 2.5, 'attack_range': 'melee'},
    'forest_spider': {'name': '🕷️ Ткач Теней', 'base_health': 65, 'base_min_physical_damage': 8, 'base_max_physical_damage': 16, 'base_min_magic_damage': 0, 'base_max_magic_damage': 0, 'base_exp': 25, 'base_gold': 16, 'rank': 'D', 'description': 'Огромный паук, чья паутина прочнее стали. Пьет кровь тех, кто заблудился во тьме.', 'image': 'https://img.freepik.com/free-photo/giant-spider_23-2150911307.jpg', 'difficulty': 'medium', 'abilities': ['basic_attack', 'web_shot', 'poison_bite'], 'damage_type': 'physical', 'dodge_chance': 0.15, 'physical_resistance': 0.15, 'magic_resistance': 0.05, 'special_chance': 0.25, 'web_chance': 0.30, 'attack_range': 'melee'},
    'ghost': {'name': '👻 Неупокоенный Дух', 'base_health': 55, 'base_min_physical_damage': 7, 'base_max_physical_damage': 14, 'base_min_magic_damage': 4, 'base_max_magic_damage': 9, 'base_exp': 28, 'base_gold': 20, 'rank': 'D', 'description': 'Призрак жертвы древнего проклятия. Его прикосновение леденит душу.', 'image': 'https://img.freepik.com/free-photo/ghost_23-2150762306.jpg', 'difficulty': 'medium', 'abilities': ['basic_attack', 'fear', 'phase_through'], 'damage_type': 'magic', 'dodge_chance': 0.25, 'physical_resistance': 0.60, 'magic_resistance': 0.25, 'special_chance': 0.30, 'attack_range': 'ranged'},
    'wild_boar': {'name': '🐗 Кабан-людоед', 'base_health': 85, 'base_min_physical_damage': 10, 'base_max_physical_damage': 20, 'base_min_magic_damage': 0, 'base_max_magic_damage': 0, 'base_exp': 32, 'base_gold': 24, 'rank': 'D', 'description': 'Массивная тварь, вкусившая человеческой плоти. Его клыки способны пробить доспех.', 'image': 'https://img.freepik.com/free-photo/wild-boar_23-2150911295.jpg', 'difficulty': 'medium', 'abilities': ['basic_attack', 'charge', 'tusks'], 'damage_type': 'physical', 'dodge_chance': 0.08, 'physical_resistance': 0.30, 'magic_resistance': 0.05, 'special_chance': 0.25, 'charge_chance': 0.35, 'attack_range': 'melee'},
    'forest_troll': {'name': '🌳 Болотный Тролль', 'base_health': 110, 'base_min_physical_damage': 15, 'base_max_physical_damage': 23, 'base_min_magic_damage': 0, 'base_max_magic_damage': 0, 'base_exp': 48, 'base_gold': 36, 'rank': 'D', 'description': 'Тупое, но невероятно сильное существо. Его раны затягиваются прямо на глазах.', 'image': 'https://img.freepik.com/free-photo/troll_23-2150911292.jpg', 'difficulty': 'mini_boss', 'abilities': ['basic_attack', 'regeneration', 'club_smash'], 'damage_type': 'physical', 'dodge_chance': 0.12, 'physical_resistance': 0.35, 'magic_resistance': 0.15, 'special_chance': 0.35, 'mini_boss_bonus': 1.9, 'attack_range': 'melee'},
    'forest_guardian': {'name': '🌳 Проклятый Энт', 'base_health': 150, 'base_min_physical_damage': 13, 'base_max_physical_damage': 25, 'base_min_magic_damage': 7, 'base_max_magic_damage': 13, 'base_exp': 80, 'base_gold': 64, 'rank': 'D', 'description': 'Древний страж леса, искаженный темной магией. Теперь он убивает все живое.', 'image': 'https://img.freepik.com/free-photo/treant_23-2150911290.jpg', 'difficulty': 'boss', 'abilities': ['basic_attack', 'root_grab', 'healing_leaves', 'forest_rage'], 'damage_type': 'mixed', 'dodge_chance': 0.08, 'physical_resistance': 0.45, 'magic_resistance': 0.35, 'special_chance': 0.40, 'boss_bonus': 2.7, 'heal_chance': 0.25, 'attack_range': 'mixed'},
    'skeleton_warrior': {'name': '💀 Костяной страж', 'base_health': 100, 'base_min_physical_damage': 13, 'base_max_physical_damage': 23, 'base_min_magic_damage': 0, 'base_max_magic_damage': 0, 'base_exp': 48, 'base_gold': 32, 'rank': 'C', 'description': 'Останки воина древней империи, поднятые некромантом. Не знает усталости и страха.', 'image': IMAGE_URLS['skeleton'], 'difficulty': 'hard', 'abilities': ['basic_attack', 'shield_bash', 'bone_armor'], 'damage_type': 'physical', 'dodge_chance': 0.12, 'physical_resistance': 0.35, 'magic_resistance': 0.15, 'special_chance': 0.30, 'block_chance': 0.35, 'attack_range': 'melee'},
    'ghoul': {'name': '🧟 Могильный Гуль', 'base_health': 115, 'base_min_physical_damage': 12, 'base_max_physical_damage': 22, 'base_min_magic_damage': 0, 'base_max_magic_damage': 0, 'base_exp': 52, 'base_gold': 36, 'rank': 'C', 'description': 'Отвратительное создание, пожирающее трупы в катакомбах. Его когти заразны.', 'image': IMAGE_URLS['zombie'], 'difficulty': 'hard', 'abilities': ['basic_attack', 'life_drain', 'frenzy'], 'damage_type': 'physical', 'dodge_chance': 0.10, 'physical_resistance': 0.25, 'magic_resistance': 0.05, 'special_chance': 0.35, 'drain_chance': 0.30, 'attack_range': 'melee'},
    'dark_priest': {'name': '🕯️ Еретик-культист', 'base_health': 90, 'base_min_physical_damage': 7, 'base_max_physical_damage': 13, 'base_min_magic_damage': 15, 'base_max_magic_damage': 28, 'base_exp': 60, 'base_gold': 44, 'rank': 'C', 'description': 'Безумец, поклоняющийся темным богам. Владеет запретной магией крови и проклятий.', 'image': IMAGE_URLS['mage'], 'difficulty': 'hard', 'abilities': ['basic_attack', 'dark_bolt', 'curse', 'sacrifice'], 'damage_type': 'magic', 'dodge_chance': 0.15, 'physical_resistance': 0.15, 'magic_resistance': 0.30, 'special_chance': 0.40, 'spell_chance': 0.45, 'attack_range': 'ranged'},
    'crypt_keeper': {'name': '💀 Некромант-ученик', 'base_health': 140, 'base_min_physical_damage': 15, 'base_max_physical_damage': 25, 'base_min_magic_damage': 10, 'base_max_magic_damage': 19, 'base_exp': 72, 'base_gold': 56, 'rank': 'C', 'description': 'Стремится познать тайны смерти, поднимая мертвецов для защиты своих владений.', 'image': 'https://img.freepik.com/free-photo/necromancer_23-2150911284.jpg', 'difficulty': 'mini_boss', 'abilities': ['basic_attack', 'raise_dead', 'death_bolt', 'bone_shield'], 'damage_type': 'mixed', 'dodge_chance': 0.18, 'physical_resistance': 0.25, 'magic_resistance': 0.40, 'special_chance': 0.40, 'mini_boss_bonus': 2.0, 'attack_range': 'ranged'},
    'catacomb_lord': {'name': '👑 Король-Лич Катакомб', 'base_health': 225, 'base_min_physical_damage': 19, 'base_max_physical_damage': 32, 'base_min_magic_damage': 13, 'base_max_magic_damage': 23, 'base_exp': 160, 'base_gold': 120, 'rank': 'C', 'description': 'Древний правитель, отвергший смерть. Он вечно правит своим подземным царством мертвых.', 'image': 'https://img.freepik.com/free-photo/skeleton-king_23-2150911291.jpg', 'difficulty': 'boss', 'abilities': ['basic_attack', 'royal_decree', 'summon_skeletons', 'kings_wrath'], 'damage_type': 'mixed', 'dodge_chance': 0.15, 'physical_resistance': 0.40, 'magic_resistance': 0.30, 'special_chance': 0.45, 'boss_bonus': 3.0, 'summon_chance': 0.35, 'attack_range': 'mixed'},
    'knight': {'name': '⚔️ Падший Рыцарь', 'base_health': 150, 'base_min_physical_damage': 19, 'base_max_physical_damage': 32, 'base_min_magic_damage': 0, 'base_max_magic_damage': 0, 'base_exp': 80, 'base_gold': 64, 'rank': 'B', 'description': 'Его доспехи черны как ночь, а меч жаждет крови. Он предал свои клятвы ради силы.', 'image': IMAGE_URLS['knight'], 'difficulty': 'very_hard', 'abilities': ['basic_attack', 'shield_wall', 'vengeful_strike', 'dark_aura'], 'damage_type': 'physical', 'dodge_chance': 0.20, 'physical_resistance': 0.45, 'magic_resistance': 0.25, 'special_chance': 0.35, 'defense_bonus': 0.45, 'attack_range': 'melee'},
    'vampire': {'name': '🦇 Вампир-аристократ', 'base_health': 125, 'base_min_physical_damage': 23, 'base_max_physical_damage': 35, 'base_min_magic_damage': 0, 'base_max_magic_damage': 0, 'base_exp': 96, 'base_gold': 80, 'rank': 'B', 'description': 'Древний хищник, скрывающийся в руинах замка. Он видит в тебе лишь очередной сосуд с кровью.', 'image': IMAGE_URLS['vampire'], 'difficulty': 'very_hard', 'abilities': ['basic_attack', 'blood_drain', 'bat_swarm', 'hypnosis'], 'damage_type': 'physical', 'dodge_chance': 0.25, 'physical_resistance': 0.30, 'magic_resistance': 0.20, 'special_chance': 0.40, 'heal_from_damage': 0.35, 'attack_range': 'melee'},
    'warlock': {'name': '🔮 Мастер Проклятий', 'base_health': 115, 'base_min_physical_damage': 7, 'base_max_physical_damage': 13, 'base_min_magic_damage': 25, 'base_max_magic_damage': 40, 'base_exp': 104, 'base_gold': 88, 'rank': 'B', 'description': 'Заключил пакт с демонами, обменяв свою душу на разрушительную силу.', 'image': IMAGE_URLS['mage'], 'difficulty': 'very_hard', 'abilities': ['basic_attack', 'shadow_bolt', 'demon_summon', 'soul_burn'], 'damage_type': 'magic', 'dodge_chance': 0.18, 'physical_resistance': 0.15, 'magic_resistance': 0.45, 'special_chance': 0.45, 'summon_chance': 0.30, 'attack_range': 'ranged'},
    'death_knight': {'name': '💀 Рыцарь Смерти', 'base_health': 190, 'base_min_physical_damage': 25, 'base_max_physical_damage': 38, 'base_min_magic_damage': 13, 'base_max_magic_damage': 23, 'base_exp': 144, 'base_gold': 112, 'rank': 'B', 'description': 'Воплощение войны и мора. Он ведет за собой армию нежити, уничтожая все на своем пути.', 'image': 'https://img.freepik.com/free-photo/death-knight_23-2150911264.jpg', 'difficulty': 'mini_boss', 'abilities': ['basic_attack', 'death_coil', 'anti_magic_shell', 'army_of_the_dead'], 'damage_type': 'mixed', 'dodge_chance': 0.23, 'physical_resistance': 0.50, 'magic_resistance': 0.40, 'special_chance': 0.45, 'mini_boss_bonus': 2.1, 'attack_range': 'melee'},
    'castle_overlord': {'name': '🏰 Безумный Король', 'base_health': 315, 'base_min_physical_damage': 25, 'base_max_physical_damage': 44, 'base_min_magic_damage': 19, 'base_max_magic_damage': 32, 'base_exp': 280, 'base_gold': 200, 'rank': 'B', 'description': 'Владыка проклятого замка. Его разум давно поглотила тьма, превратив его в тирана.', 'image': 'https://img.freepik.com/free-photo/dark-king_23-2150911261.jpg', 'difficulty': 'boss', 'abilities': ['basic_attack', 'royal_command', 'castle_defense', 'tyrants_wrath'], 'damage_type': 'mixed', 'dodge_chance': 0.20, 'physical_resistance': 0.55, 'magic_resistance': 0.35, 'special_chance': 0.50, 'boss_bonus': 3.3, 'defense_bonus': 0.55, 'attack_range': 'mixed'},
    'demon': {'name': '😈 Демон-разрушитель', 'base_health': 190, 'base_min_physical_damage': 32, 'base_max_physical_damage': 50, 'base_min_magic_damage': 13, 'base_max_magic_damage': 25, 'base_exp': 160, 'base_gold': 120, 'rank': 'A', 'description': 'Существо из чистой злобы, прорвавшееся в этот мир через врата ада. Жаждет лишь хаоса.', 'image': IMAGE_URLS['demon'], 'difficulty': 'extreme', 'abilities': ['basic_attack', 'hellfire', 'demonic_claws', 'fear_aura'], 'damage_type': 'mixed', 'dodge_chance': 0.25, 'physical_resistance': 0.35, 'magic_resistance': 0.45, 'special_chance': 0.40, 'fire_chance': 0.35, 'attack_range': 'mixed'},
    'hellhound': {'name': '🔥 Цербер Преисподней', 'base_health': 225, 'base_min_physical_damage': 28, 'base_max_physical_damage': 48, 'base_min_magic_damage': 7, 'base_max_magic_damage': 13, 'base_exp': 144, 'base_gold': 112, 'rank': 'A', 'description': 'Трехголовый пес, страж врат ада. Его дыхание — само пламя, а шкура тверже камня.', 'image': 'https://img.freepik.com/free-photo/hellhound_23-2150911276.jpg', 'difficulty': 'extreme', 'abilities': ['basic_attack', 'fire_breath', 'pack_hunt', 'hellish_howl'], 'damage_type': 'mixed', 'dodge_chance': 0.30, 'physical_resistance': 0.30, 'magic_resistance': 0.40, 'special_chance': 0.35, 'burn_chance': 0.30, 'attack_range': 'melee'},
    'infernal_mage': {'name': '🔥 Архидемон Пламени', 'base_health': 165, 'base_min_physical_damage': 13, 'base_max_physical_damage': 23, 'base_min_magic_damage': 35, 'base_max_magic_damage': 56, 'base_exp': 176, 'base_gold': 136, 'rank': 'A', 'description': 'Повелитель адского огня. Он способен превратить все вокруг в пепел одним щелчком пальцев.', 'image': 'https://img.freepik.com/free-photo/fire-mage_23-2150911269.jpg', 'difficulty': 'extreme', 'abilities': ['basic_attack', 'meteor_shower', 'demonic_gate', 'inferno'], 'damage_type': 'magic', 'dodge_chance': 0.20, 'physical_resistance': 0.20, 'magic_resistance': 0.55, 'special_chance': 0.45, 'aoe_chance': 0.40, 'attack_range': 'ranged'},
    'pit_fiend': {'name': '😈 Владыка Бездны', 'base_health': 275, 'base_min_physical_damage': 35, 'base_max_physical_damage': 53, 'base_min_magic_damage': 25, 'base_max_magic_damage': 40, 'base_exp': 240, 'base_gold': 176, 'rank': 'A', 'description': 'Высший демон, командующий легионами. Его сила превосходит понимание смертных.', 'image': 'https://img.freepik.com/free-photo/pit-fiend_23-2150911286.jpg', 'difficulty': 'mini_boss', 'abilities': ['basic_attack', 'summon_demons', 'infernal_rage', 'dimensional_rip'], 'damage_type': 'mixed', 'dodge_chance': 0.28, 'physical_resistance': 0.45, 'magic_resistance': 0.50, 'special_chance': 0.50, 'mini_boss_bonus': 2.2, 'attack_range': 'mixed'},
    'demon_general': {'name': '😈 Генерал Армии Ада', 'base_health': 440, 'base_min_physical_damage': 38, 'base_max_physical_damage': 63, 'base_min_magic_damage': 32, 'base_max_magic_damage': 50, 'base_exp': 400, 'base_gold': 280, 'rank': 'A', 'description': 'Правая рука самого Дьявола. Его появление на поле боя знаменует конец света.', 'image': 'https://img.freepik.com/free-photo/demon-general_23-2150911263.jpg', 'difficulty': 'boss', 'abilities': ['basic_attack', 'army_command', 'apocalypse', 'final_judgment'], 'damage_type': 'mixed', 'dodge_chance': 0.25, 'physical_resistance': 0.50, 'magic_resistance': 0.45, 'special_chance': 0.55, 'boss_bonus': 3.5, 'army_bonus': 1.6, 'attack_range': 'mixed'},
    'dragon_ancient': {'name': '🐉 Древний Дракон Хаоса', 'base_health': 500, 'base_min_physical_damage': 44, 'base_max_physical_damage': 69, 'base_min_magic_damage': 32, 'base_max_magic_damage': 50, 'base_exp': 480, 'base_gold': 320, 'rank': 'S', 'description': 'Существо, рожденное на заре времен. Его чешуя непробиваема, а пламя сжигает душу.', 'image': IMAGE_URLS['dragon_ancient'], 'difficulty': 'legendary', 'abilities': ['basic_attack', 'dragon_breath', 'wing_gust', 'ancient_roar'], 'damage_type': 'mixed', 'dodge_chance': 0.30, 'physical_resistance': 0.55, 'magic_resistance': 0.55, 'special_chance': 0.45, 'breath_chance': 0.40, 'attack_range': 'mixed'},
    'titan': {'name': '🏔️ Титан Катаклизма', 'base_health': 625, 'base_min_physical_damage': 50, 'base_max_physical_damage': 75, 'base_min_magic_damage': 19, 'base_max_magic_damage': 32, 'base_exp': 560, 'base_gold': 360, 'rank': 'S', 'description': 'Ходячая гора, воплощение землетрясений и разрушений. Он может расколоть мир пополам.', 'image': IMAGE_URLS['titan'], 'difficulty': 'legendary', 'abilities': ['basic_attack', 'earthquake', 'mountain_slam', 'titanic_rage'], 'damage_type': 'physical', 'dodge_chance': 0.15, 'physical_resistance': 0.65, 'magic_resistance': 0.35, 'special_chance': 0.40, 'stun_chance': 0.35, 'attack_range': 'melee'},
    'fallen_angel': {'name': '😇 Падший Серафим', 'base_health': 565, 'base_min_physical_damage': 48, 'base_max_physical_damage': 73, 'base_min_magic_damage': 38, 'base_max_magic_damage': 56, 'base_exp': 520, 'base_gold': 336, 'rank': 'S', 'description': 'Некогда сияющий ангел, изгнанный с небес за гордыню. Теперь его крылья черны, а меч несет гибель.', 'image': 'https://img.freepik.com/free-photo/fallen-angel_23-2150911260.jpg', 'difficulty': 'legendary', 'abilities': ['basic_attack', 'heavenly_light', 'fallen_wings', 'judgment_sword'], 'damage_type': 'mixed', 'dodge_chance': 0.35, 'physical_resistance': 0.45, 'magic_resistance': 0.65, 'special_chance': 0.50, 'heal_chance': 0.30, 'attack_range': 'mixed'},
    'archangel': {'name': '😇 Архангел Возмездия', 'base_health': 475, 'base_min_physical_damage': 40, 'base_max_physical_damage': 60, 'base_min_magic_damage': 44, 'base_max_magic_damage': 65, 'base_exp': 440, 'base_gold': 304, 'rank': 'S', 'description': 'Верховный страж небес, спустившийся покарать грешников. Его свет ослепляет недостойных.', 'image': 'https://img.freepik.com/free-photo/archangel_23-2150911259.jpg', 'difficulty': 'mini_boss', 'abilities': ['basic_attack', 'divine_smite', 'angelic_shield', 'holy_aura'], 'damage_type': 'mixed', 'dodge_chance': 0.40, 'physical_resistance': 0.40, 'magic_resistance': 0.60, 'special_chance': 0.55, 'mini_boss_bonus': 2.3, 'attack_range': 'mixed'},
    'final_god': {'name': '⚡ Падший Бог-Творец', 'base_health': 1250, 'base_min_physical_damage': 63, 'base_max_physical_damage': 100, 'base_min_magic_damage': 50, 'base_max_magic_damage': 88, 'base_exp': 1200, 'base_gold': 800, 'rank': 'S', 'description': 'Создатель этого мира, сошедший с ума и решивший уничтожить свое творение. Победи его и стань новой легендой, или умри как все остальные.', 'image': IMAGE_URLS['fallen_god'], 'difficulty': 'boss', 'abilities': ['basic_attack', 'divine_judgment', 'creation', 'annihilation', 'omnipotence'], 'damage_type': 'mixed', 'dodge_chance': 0.45, 'physical_resistance': 0.65, 'magic_resistance': 0.65, 'special_chance': 0.65, 'boss_bonus': 4.5, 'god_powers': True, 'attack_range': 'mixed'}
}

# ОБНОВЛЕННЫЕ ОПИСАНИЯ ЛОКАЦИЙ (ЛОР)
LOCATIONS = {
    'E': {'name': '🎪 Лагерь Наемников', 'description': 'Последний оплот относительной безопасности на краю цивилизации. Здесь новички тренируются на слабых монстрах, прежде чем шагнуть в настоящую тьму.', 'enemies': ['wolf', 'goblin', 'slime', 'goblin_elite', 'training_master'], 'mini_boss': 'goblin_elite', 'boss': 'training_master', 'image': IMAGE_URLS['training_camp'], 'min_level': 1, 'max_level': 15, 'difficulty': 'easy'},
    'D': {'name': '🌲 Проклятый Лес', 'description': 'Древний лес, где деревья шепчут имена погибших путников. Солнечный свет здесь редкий гость, а тени кишат голодными тварями.', 'enemies': ['forest_spider', 'ghost', 'wild_boar', 'forest_troll', 'forest_guardian'], 'mini_boss': 'forest_troll', 'boss': 'forest_guardian', 'image': IMAGE_URLS['forest'], 'min_level': 10, 'max_level': 25, 'difficulty': 'medium'},
    'C': {'name': '🪦 Город Мертвых', 'description': 'Руины некогда великой столицы, теперь населенные нежитью и темными культистами. Подземелья хранят древние тайны и смертельные опасности.', 'enemies': ['skeleton_warrior', 'ghoul', 'dark_priest', 'crypt_keeper', 'catacomb_lord'], 'mini_boss': 'crypt_keeper', 'boss': 'catacomb_lord', 'image': IMAGE_URLS['dungeon'], 'min_level': 20, 'max_level': 35, 'difficulty': 'hard'},
    'B': {'name': '🏰 Цитадель Тьмы', 'description': 'Замок безумного короля, продавшего душу ради власти. Его стены пропитаны злом, а стражи — могущественные вампиры и рыцари смерти.', 'enemies': ['knight', 'vampire', 'warlock', 'death_knight', 'castle_overlord'], 'mini_boss': 'death_knight', 'boss': 'castle_overlord', 'image': IMAGE_URLS['castle'], 'min_level': 30, 'max_level': 45, 'difficulty': 'very_hard'},
    'A': {'name': '🌋 Врата Преисподней', 'description': 'Разлом в ткани реальности, откуда в мир проникают легионы ада. Воздух здесь раскален, а земля горит под ногами. Путь только для сильнейших.', 'enemies': ['demon', 'hellhound', 'infernal_mage', 'pit_fiend', 'demon_general'], 'mini_boss': 'pit_fiend', 'boss': 'demon_general', 'image': IMAGE_URLS['hell_gate'], 'min_level': 40, 'max_level': 55, 'difficulty': 'extreme'},
    'S': {'name': '⚡ Трон Падшего Бога', 'description': 'Вершина мироздания, где решается судьба всего сущего. Здесь обитают легендарные существа, а в конце пути ждет сам безумный Творец. Лишь истинная легенда сможет бросить ему вызов.', 'enemies': ['dragon_ancient', 'titan', 'fallen_angel', 'archangel', 'final_god'], 'mini_boss': 'archangel', 'boss': 'final_god', 'image': IMAGE_URLS['throne_god'], 'min_level': 50, 'max_level': 70, 'difficulty': 'legendary'}
}

# --- ФУНКЦИИ БОТА (БЕЗ ИЗМЕНЕНИЙ ЛОГИКИ, ТОЛЬКО БАЛАНС В create_enemy и calculate_damage) ---

async def safe_edit(query, text=None, keyboard=None, media=None):
    try:
        if media:
            await query.edit_message_media(media=media, reply_markup=keyboard)
        elif text:
            try:
                await query.edit_message_caption(caption=text, parse_mode='Markdown', reply_markup=keyboard)
            except:
                await query.edit_message_text(text=text, parse_mode='Markdown', reply_markup=keyboard)
        elif keyboard:
             await query.edit_message_reply_markup(reply_markup=keyboard)
    except Exception as e:
        try: await query.delete_message()
        except: pass
        if media:
             await query.message.reply_photo(photo=media.media, caption=media.caption, parse_mode='Markdown', reply_markup=keyboard)
        elif text:
             await query.message.reply_text(text, parse_mode='Markdown', reply_markup=keyboard)

def create_enemy(enemy_key, player_level):
    if enemy_key not in BASE_ENEMIES: 
        if 'wolf' in BASE_ENEMIES: return create_enemy('wolf', player_level)
        return None
    
    base = BASE_ENEMIES[enemy_key].copy()
    
    # БАЛАНС: Снижаем скорость роста врагов (было 15%, стало 10%)
    level_multiplier = 1.0 + (player_level - 1) * 0.10
    
    bonus = 1.0
    if base.get('difficulty') == 'mini_boss': bonus = 1.8
    elif base.get('difficulty') == 'boss': bonus = 2.5
    
    final_multiplier = level_multiplier * bonus
    
    enemy = base.copy()
    # БАЛАНС: Ослабляем здоровье на 10%
    enemy['health'] = int(base['base_health'] * final_multiplier * 0.9)
    enemy['max_health'] = enemy['health']
    
    # БАЛАНС: Ослабляем урон на 15%
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

def get_rank_icon(rank):
    return {'E': '🆕', 'D': '🟢', 'C': '🔵', 'B': '🟣', 'A': '🟠', 'S': '⚡'}.get(rank, '🆕')

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

def calculate_player_dodge_chance(agility):
    return min(0.03 + (agility * 0.003), 0.25)

def calculate_damage(character, enemy, damage_type='physical'):
    # БАЛАНС: Урон героя теперь Сила / 2 (было /3), т.е. +50% урона
    base_damage = max(1, character['strength' if damage_type == 'physical' else 'intelligence'] // 2)
    res = enemy.get('physical_resistance' if damage_type == 'physical' else 'magic_resistance', 0.0)
    
    damage = random.randint(int(base_damage*0.8), int(base_damage*1.2))
    damage = max(1, int(damage * (1 - res)))
    
    # Шанс крита от ловкости
    is_crit = random.random() < min(0.15, character.get('agility', 8) * 0.005)
    if is_crit: damage = int(damage * 1.5)
    
    return damage, is_crit

def calculate_enemy_damage(enemy, character):
    if enemy['damage_type'] == 'physical':
        min_d, max_d = enemy['min_physical_damage'], enemy['max_physical_damage']
        res = character.get('physical_resistance', 0.0)
    elif enemy['damage_type'] == 'magic':
        min_d, max_d = enemy['min_magic_damage'], enemy['max_magic_damage']
        res = character.get('magic_resistance', 0.0)
    else:
        if random.random() < 0.5:
            min_d, max_d = enemy['min_physical_damage'], enemy['max_physical_damage']
            res = character.get('physical_resistance', 0.0)
        else:
            min_d, max_d = enemy['min_magic_damage'], enemy['max_magic_damage']
            res = character.get('magic_resistance', 0.0)
            
    damage = random.randint(min_d, max_d)
    # БАЛАНС: Снижаем входящий урон на 15%
    damage = int(damage * (1 - float(res)) * 0.85)
    
    is_dodged = random.random() < calculate_player_dodge_chance(character.get('agility', 8))
    return max(1, damage), is_dodged

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
        [InlineKeyboardButton("🛍 Торговец", callback_data='shop'), InlineKeyboardButton("🏆 Топ игроков", callback_data='top_players')],
        [InlineKeyboardButton("📜 Помощь", callback_data='help'), InlineKeyboardButton("🔄 Обновить", callback_data='refresh')]
    ]
    if char and char['stat_points'] > 0:
        kb.insert(2, [InlineKeyboardButton(f"🌟 ПРОКАЧАТЬ ({char['stat_points']})", callback_data='level_up_menu')])
    return InlineKeyboardMarkup(kb)

def get_shop_keyboard(char):
    kb = []
    for k, v in SHOP_ITEMS.items():
        kb.append([InlineKeyboardButton(f"{v['name']} - {v['price']}💰", callback_data=f"buy_{k}")])
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
    for i in items:
        kb.append([InlineKeyboardButton(f"Использовать {i['item_name']} (x{i['quantity']})", callback_data=f"use_{i['item_key']}")])
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
        # ЛОР: Приветствие для существующего героя
        msg = f"С возвращением в этот проклятый мир, {char['character_name']}. Тьма сгущается, и лишь сильнейшие выживут."
        await update.message.reply_photo(IMAGE_URLS['village'], caption=msg, reply_markup=get_main_menu_keyboard(user.id))
        return MAIN_MENU
    else:
        await update.message.reply_text("Мир на грани гибели. Выбери, кем ты рожден в этой эпохе тьмы:", reply_markup=get_race_selection_keyboard())
        return CHOOSE_RACE

async def choose_race(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['race'] = query.data.split('_')[1]
    await query.message.reply_text("Как нарекут героя, что бросит вызов судьбе?")
    return ENTER_NAME

async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    user = update.effective_user
    database.create_character(user.id, user.username, name, context.user_data['race'])
    # ЛОР: Сообщение о создании героя
    msg = "Герой создан. Твой путь начинается в лагере наемников. Тренируйся, сражайся и, возможно, ты станешь той легендой, что сокрушит Падшего Бога."
    await update.message.reply_photo(IMAGE_URLS['village'], caption=msg, reply_markup=get_main_menu_keyboard(user.id))
    return MAIN_MENU

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    
    if data == 'profile':
        char = database.get_character(user_id) 
        # Доп. статистика для стратегии
        phys = max(1, char['strength'] // 2)
        mag = max(1, char['intelligence'] // 2)
        dodge = int(calculate_player_dodge_chance(char['agility']) * 100)
        
        # ЛОР: Заголовок профиля
        txt = (f"📜 *Хроники выжившего {char['character_name']}*\n"
               f"Раса: {database.RACES[char['race']]['name']} | Ранг: {char['rank']}\n\n"
               f"HP: {get_health_bar(char['health'], char['max_health'])} | MP: {get_mana_bar(char['mana'], char['max_mana'])}\n"
               f"💰 Золото: {char['gold']} | ✨ Опыт: {get_xp_bar(char['level'], char['experience'])}\n\n"
               f"⚔️ Урон: {phys} (Физ) / {mag} (Маг)\n"
               f"💨 Уклонение: {dodge}%\n"
               f"❤️ Регенерация: 5% в минуту (вне боя)")
               
        await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['village'], caption=txt, parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
    elif data == 'inventory':
        await show_inventory_menu(update, context)
        return INVENTORY_MENU
    elif data == 'battle_menu':
        char = database.get_character(user_id)
        await safe_edit(query, text="Куда ты отправишься на поиски смерти и славы?", media=InputMediaPhoto(IMAGE_URLS['forest'], caption="Куда ты отправишься на поиски смерти и славы?", parse_mode='Markdown'), keyboard=get_battle_menu_keyboard(char))
        return BATTLE_MENU
    elif data == 'shop':
        char = database.get_character(user_id)
        # ЛОР: Описание магазина
        txt = f"Торговец: 'Эй, путник! У меня есть чем залатать раны и чем их нанести. Золото вперед.'\n\nВаше золото: {char['gold']}💰"
        await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['shop'], caption=txt, parse_mode='Markdown'), keyboard=get_shop_keyboard(char))
        return SHOP_MENU
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
        await query.edit_message_caption("Твоя сила растет. Что ты улучшишь, чтобы выжить?", reply_markup=get_level_up_keyboard(char, char['stat_points']))
        return LEVEL_UP
    elif data == 'rank_info':
        # ЛОР: Описание рангов
        rank_info = """
🏆 *ПУТЬ ОХОТНИКА*
В этом мире сила определяет все. Чем выше твой ранг, тем опаснее твари, с которыми ты столкнешься, и тем ближе ты к трону Падшего Бога.

🆕 E: Пушечное мясо (1-14 ур)
🟢 D: Опытный выживший (15-24 ур)
🔵 C: Истребитель нежити (25-34 ур)
🟣 B: Убийца демонов (35-44 ур)
🟠 A: Легендарный воин (45-54 ур)
⚡ S: Богоубийца (55+ ур)
        """
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
        loc = LOCATIONS[rank]
        txt = f"Локация: {loc['name']}.\n{loc['description']}\n\nВыберите свою жертву:"
        await safe_edit(query, text=txt, media=InputMediaPhoto(loc['image'], caption=txt, parse_mode='Markdown'), keyboard=get_location_enemies_keyboard(rank, char['level']))
    elif data.startswith('battle_'):
        enemy_key = data.split('_')[1]
        char = database.get_character(user_id)
        if char['health'] < 10:
            await query.answer("Ты слишком слаб для боя. Залечи раны!", show_alert=True)
            return BATTLE_MENU
            
        enemy = create_enemy(enemy_key, char['level'])
        battle_sessions[user_id] = {
            'char': char, 'enemy': enemy, 'log': [f"⚔️ Вы бросили вызов: {enemy['name']}!"], 'turn': 1
        }
        await render_battle(query, user_id)
        return IN_BATTLE
    elif data == 'back_to_battle_menu':
        char = database.get_character(user_id)
        await safe_edit(query, text="Куда ты отправишься?", media=InputMediaPhoto(IMAGE_URLS['forest'], caption="Куда ты отправишься?", parse_mode='Markdown'), keyboard=get_battle_menu_keyboard(char))
        
    return BATTLE_MENU

async def render_battle(query, user_id):
    s = battle_sessions[user_id]
    c, e = s['char'], s['enemy']
    log = "\n".join(s['log'][-3:])
    txt = (f"🆚 *СМЕРТЕЛЬНАЯ БИТВА*\n👤 {c['character_name']}: {get_health_bar(c['health'], c['max_health'])}\n"
           f"👺 {e['name']}: {get_health_bar(e['health'], e['max_health'])}\n\n{log}")
    await safe_edit(query, text=txt, media=InputMediaPhoto(e['image'], caption=txt, parse_mode='Markdown'), keyboard=get_battle_action_keyboard())

async def battle_action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    action = query.data
    s = battle_sessions.get(user_id)
    if not s: return MAIN_MENU
    
    c, e, log = s['char'], s['enemy'], s['log']
    
    # Ход игрока
    if action == 'flee':
        if random.random() < 0.5:
            # СОХРАНЯЕМ ТЕКУЩЕЕ ЗДОРОВЬЕ ПРИ ПОБЕГЕ
            database.update_character_stats(user_id, health=c['health'], mana=c['mana'])
            del battle_sessions[user_id]
            # ЛОР: Сообщение о побеге
            msg = "🏃 Ты позорно бежал с поля боя, спасая свою шкуру. Раны остались при тебе."
            await safe_edit(query, text=msg, media=InputMediaPhoto(IMAGE_URLS['village'], caption=msg, parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
            return MAIN_MENU
        log.append("🚫 Враг не дает тебе сбежать!")
    elif 'attack' in action:
        dmg, crit = calculate_damage(c, e, 'magic' if 'magic' in action else 'physical')
        status = " (КРИТ!)" if crit else ""
        if 'magic' in action:
             if c['mana'] >= 10:
                 c['mana'] -= 10
                 e['health'] -= dmg
                 log.append(f"🔮 Твое заклинание нанесло {dmg}{status} урона!")
             else:
                 log.append("❌ Недостаточно маны для магии!")
        else:
            e['health'] -= dmg
            log.append(f"⚔️ Твой удар нанес {dmg}{status} урона!")

    # Победа
    if e['health'] <= 0:
        database.add_experience(user_id, e['exp'])
        database.add_gold(user_id, e['gold'])
        database.update_character_stats(user_id, health=c['health'], mana=c['mana'], battle_wins=c.get('battle_wins',0)+1)
        if e.get('is_boss'): database.increment_boss_kills(user_id, False)
        if e.get('is_mini_boss'): database.increment_boss_kills(user_id, True)
        del battle_sessions[user_id]
        # ЛОР: Сообщение о победе
        txt = f"🏆 Враг повержен! Ты обыскал труп и нашел: {e['gold']} золота. Получено {e['exp']} опыта."
        await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['village'], caption=txt, parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
        return MAIN_MENU

    # Ход врага
    if action != 'flee':
        dmg, dodge = calculate_enemy_damage(e, c)
        if not dodge:
            if action == 'defend': dmg //= 2
            c['health'] -= dmg
            log.append(f"💔 {e['name']} наносит тебе {dmg} урона!")
        else:
            log.append("💨 Ты ловко уклонился от атаки врага!")

    # Поражение
    if c['health'] <= 0:
        database.update_character_stats(user_id, health=0, battle_losses=c.get('battle_losses',0)+1)
        del battle_sessions[user_id]
        # ЛОР: Сообщение о смерти
        msg = "💀 Твоя история закончилась здесь. Твое тело останется гнить на поле боя, пока кто-нибудь не подберет твое снаряжение..."
        await safe_edit(query, text=msg, media=InputMediaPhoto(IMAGE_URLS['village'], caption=msg, parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
        return MAIN_MENU
        
    await render_battle(query, user_id)
    return IN_BATTLE

async def shop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    
    if data == 'back_to_main':
        await query.answer()
        await safe_edit(query, text="В деревне", media=InputMediaPhoto(IMAGE_URLS['village'], caption="В деревне", parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
        return MAIN_MENU
    elif data.startswith('buy_'):
        item_key = data.split('_', 1)[1]
        item = SHOP_ITEMS.get(item_key)
        
        # ПРОВЕРКИ МАГАЗИНА
        char = database.get_character(user_id)
        if item.get('required_rank'):
            ranks = ['E', 'D', 'C', 'B', 'A', 'S']
            if ranks.index(char['rank']) < ranks.index(item['required_rank']):
                await query.answer(f"🔒 Торговец: 'Этот товар только для охотников ранга {item['required_rank']}. Проваливай.'", show_alert=True)
                return SHOP_MENU
        
        if item and char['gold'] >= item['price']:
            res, msg = database.buy_item(user_id, item_key, item['type'], item['name'], item['price'], item['effect'])
            await query.answer(f"Торговец: 'Хороший выбор. {msg}'", show_alert=True)
            char = database.get_character(user_id)
            txt = f"Торговец: 'Еще что-нибудь?'\n\nВаше золото: {char['gold']}💰"
            await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['shop'], caption=txt, parse_mode='Markdown'), keyboard=get_shop_keyboard(char))
        else:
            await query.answer("💸 Торговец: 'Нет золота — нет товара. Я не занимаюсь благотворительностью.'", show_alert=True)
            
    return SHOP_MENU

async def level_up_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    
    if data == 'back_to_main':
        await safe_edit(query, text="Главное меню", media=InputMediaPhoto(IMAGE_URLS['village'], caption="Главное меню", parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
        return MAIN_MENU
    elif data.startswith('levelup_'):
        stat = data.split('_')[1]
        res, msg = database.add_stat_point(user_id, stat)
        await query.answer(msg)
        char = database.get_character(user_id)
        if char['stat_points'] > 0:
             await query.edit_message_reply_markup(reply_markup=get_level_up_keyboard(char, char['stat_points']))
        else:
             await safe_edit(query, text="Все очки распределены. Ты стал сильнее.", media=InputMediaPhoto(IMAGE_URLS['village'], caption="Все очки распределены. Ты стал сильнее.", parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
             return MAIN_MENU
    return LEVEL_UP

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
        res, msg = database.use_item(user_id, key, 'potion', 'Potion', 0) 
        await query.answer(msg, show_alert=True)
        items = database.get_inventory(user_id)
        if items:
            await query.edit_message_reply_markup(reply_markup=get_inventory_keyboard(items, 0))
        else:
            await safe_edit(query, text="Инвентарь пуст.", media=InputMediaPhoto(IMAGE_URLS['village'], caption="Инвентарь пуст.", parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
            return MAIN_MENU
    return INVENTORY_MENU

async def show_inventory_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query if update.callback_query else update
    user_id = query.from_user.id
    items = database.get_inventory(user_id)
    
    txt = "🎒 Твой походный мешок:" if items else "В твоем мешке пусто."
    kb = get_inventory_keyboard(items, 0) if items else get_main_menu_keyboard(user_id)
    await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['inventory'], caption=txt, parse_mode='Markdown'), keyboard=kb)
    return INVENTORY_MENU

async def show_top_players(query, user_id):
    top_players = database.get_top_players(10)
    # ЛОР: Заголовок топа
    top_text = "🏆 *ЛЕГЕНДЫ УМИРАЮЩЕГО МИРА*\nТе, кто выжил там, где погибли остальные:\n━━━━━━━━━━━━━━━━\n"

    for i, player in enumerate(top_players, 1):
        name = html.escape(player['character_name'])
        lvl = player['level']
        race_key = player['race']
        race_name = database.RACES.get(race_key, {}).get('name', 'Неизвестно')
        bosses = player.get('boss_kills', 0)

        medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
        top_text += f"{medal} <b>{name}</b>\n"
        top_text += f"   └ 🎭 {race_name} | ⭐ {lvl} ур.\n"
        top_text += f"   └ ☠️ Повержено боссов: {bosses}\n\n"
    
    await safe_edit(query, text=top_text, media=InputMediaPhoto(IMAGE_URLS['village'], caption=top_text, parse_mode='HTML'), keyboard=get_main_menu_keyboard(user_id))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ЛОР: Текст помощи
    text = """
🆘 *РУКОВОДСТВО ПО ВЫЖИВАНИЮ*

Мир лежит в руинах. Твоя цель — стать сильнее, пробиться через орды монстров и бросить вызов Падшему Богу.

• 📜 **Герой** - Твое состояние. Следи за здоровьем и снаряжением.
• ⚔️ **Битва** - Единственный способ получить силу (опыт) и средства (золото).
• 🛍 **Торговец** - Жадный старик, продающий спасительные зелья и экипировку.
• 🎒 **Инвентарь** - Используй зелья в бою или перед ним, чтобы выжить.

❤️ **Регенерация:** Твои раны затягиваются со временем (5% в минуту), но только когда ты в безопасности (вне боя).
    """
    if update.callback_query:
         await safe_edit(update.callback_query, text=text, media=InputMediaPhoto(IMAGE_URLS['village'], caption=text, parse_mode='Markdown'), keyboard=get_main_menu_keyboard(update.effective_user.id))
    else:
         await update.message.reply_text(text, parse_mode='Markdown')

async def daily_reminder(context: ContextTypes.DEFAULT_TYPE):
    """Ежедневное уведомление всем игрокам"""
    users = database.get_all_users()
    for uid in users:
        # ЛОР: Ежедневное напоминание
        try: await context.bot.send_message(chat_id=uid, text="🌅 Новый день в мире тьмы. Твои раны затянулись. Пора снова отправиться в путь, пока смерть не настигла тебя в постели. (/start)")
        except: pass

def main():
    database.init_db()
    app = Application.builder().token(TOKEN).build()
    
    # Ежедневное напоминание в 12:00 UTC
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
            LEVEL_UP: [CallbackQueryHandler(level_up_handler)],
            INVENTORY_MENU: [CallbackQueryHandler(inventory_menu_handler)]
        },
        fallbacks=[CommandHandler('start', start)]
    )
    
    app.add_handler(conv)
    app.add_handler(CommandHandler('help', help_command))
    print("Бот запущен!")
    app.run_polling()

if __name__ == '__main__':
    main()
