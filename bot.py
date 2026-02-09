import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta

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
            # Применяем регенерацию здоровья и маны
            character = apply_regeneration(character)
            
            # Обновляем время последней активности
            cursor.execute("""
                UPDATE player_characters 
                SET last_active = CURRENT_TIMESTAMP 
                WHERE user_id = %s
            """, (user_id,))
            
            # Если ранг не установлен, рассчитываем его
            if not character.get('rank'):
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

def apply_regeneration(character):
    """Применение регенерации здоровья и маны"""
    conn = None
    cursor = None
    try:
        if not character:
            return character
        
        conn = get_connection()
        if not conn:
            return character
        
        cursor = conn.cursor()
        
        # Проверяем, прошло ли достаточно времени с последней регенерации
        last_regeneration = character.get('last_regeneration')
        current_time = datetime.now()
        
        if last_regeneration:
            # Преобразуем строку в datetime, если нужно
            if isinstance(last_regeneration, str):
                try:
                    last_regeneration = datetime.fromisoformat(last_regeneration.replace('Z', '+00:00'))
                except:
                    try:
                        last_regeneration = datetime.strptime(last_regeneration, '%Y-%m-%d %H:%M:%S.%f')
                    except:
                        last_regeneration = None
            
            if last_regeneration:
                time_diff = current_time - last_regeneration
                
                # Регенерация каждые 10 минут (600 секунд)
                if time_diff.total_seconds() >= 600:
                    # Рассчитываем сколько интервалов прошло
                    intervals_passed = int(time_diff.total_seconds() // 600)
                    
                    # Регенерация за каждый интервал
                    health_per_interval = character['max_health'] * 0.03  # 3% от макс. здоровья
                    mana_per_interval = character['max_mana'] * 0.05  # 5% от макс. маны
                    
                    total_health_regen = int(health_per_interval * intervals_passed)
                    total_mana_regen = int(mana_per_interval * intervals_passed)
                    
                    new_health = min(character['max_health'], character['health'] + total_health_regen)
                    new_mana = min(character['max_mana'], character['mana'] + total_mana_regen)
                    
                    # Обновляем в базе данных
                    cursor.execute("""
                        UPDATE player_characters 
                        SET health = %s, mana = %s, last_regeneration = CURRENT_TIMESTAMP
                        WHERE user_id = %s
                        RETURNING health, mana
                    """, (new_health, new_mana, character['user_id']))
                    
                    result = cursor.fetchone()
                    conn.commit()
                    
                    if result:
                        character['health'] = result[0]
                        character['mana'] = result[1]
                        character['last_regeneration'] = current_time
        
        return character
        
    except Exception as e:
        print(f"❌ Ошибка при регенерации: {e}")
        return character
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
