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
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, LabeledPrice
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    ContextTypes, ConversationHandler, MessageHandler, filters, PreCheckoutQueryHandler
)
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, LabeledPrice, BotCommand, ReplyKeyboardMarkup
import database

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


# Состояния
# Состояния
# Состояния
CHOOSE_RACE, ENTER_NAME, MAIN_MENU, BATTLE_MENU, IN_BATTLE, SHOP_MENU, LEVEL_UP, INVENTORY_MENU, CRAFT_MENU, GUILD_MENU, CLAN_MENU, CLAN_CREATE_NAME, CLAN_CREATE_ICON, CLAN_GIFT_GOLD_ENTER, CLAN_GIFT_ITEM_ENTER, SHOP_BUY_QUANTITY, SLUMS_BET_ENTER = range(17)
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
battle_sessions = {}

# --- ВИЗУАЛ (DARK FANTASY) ---
IMAGE_URLS = {
    #E
    'human': 'https://i.pinimg.com/736x/9b/f6/20/9bf6203bb54a7b095840f55fa780a365.jpg',
    'elf': 'https://i.pinimg.com/736x/c5/b1/e6/c5b1e645ceadf9c42e8ab51393981bb9.jpg',
    'dwarf': 'https://i.pinimg.com/736x/ef/b2/a2/efb2a24d7f7897ba9841764d8fb88c69.jpg',
    'orc': 'https://i.pinimg.com/736x/9d/03/22/9d0322080cea97cfd1e4667f835592dd.jpg',
    # НОВАЯ КАРТИНКА ДЛЯ ГЕРОЯ-ВАМПИРА:
    'vampire_hero': 'https://i.pinimg.com/736x/f7/cc/5d/f7cc5d151ba496829019f5d0c473fe4f.jpg',
    'lizardman': 'https://i.pinimg.com/736x/71/78/8e/71788e6d14f77626848d21b322800be0.jpg',
    'frogman': 'https://i.pinimg.com/736x/c3/d7/f6/c3d7f623bca415d0e111c867f3cb4cac.jpg',
    # НОВЫЕ РАСЫ:
    'leprechaun': 'https://i.pinimg.com/736x/18/60/2b/18602bb207c8e57cadf56a676c98e657.jpg',
    'undead': 'https://i.pinimg.com/736x/1f/c3/40/1fc34080cade4fe342cf4417d843cd61.jpg',


    
    
    'wolf': 'https://i.pinimg.com/736x/9f/8e/25/9f8e2507aceaa217060d249c308e2a13.jpg',
    'goblin': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRv_JCAj5bxf0VGHSS_-brpxVZfOz-T-CUR7w&s',
    'slime': 'https://papik.pro/uploads/posts/2023-02/1676176492_papik-pro-p-risunok-sliz-1.jpg',
    'goblin_shaman': 'https://i.pinimg.com/736x/00/75/fd/0075fdfce906f756ef6174aa8afc5401.jpg' ,
    'hot_goblin': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSXgGesfRif8L7MrmHFJruGNuxRWf3G_SFgTw&s', 
    
    'zombie': 'https://i.pinimg.com/736x/66/f1/95/66f195505cd3d16fea66f320d458c512.jpg',
    'skeleton': 'https://i.pinimg.com/736x/59/d2/a5/59d2a5aa6d18099ca70d3cdec70cdb7c.jpg',
    'mage': 'https://i.pinimg.com/736x/60/f9/99/60f999c66fbda5676aa72cb36476c3cf.jpg',
    'vampire': 'https://i.pinimg.com/736x/c7/44/ce/c744ce8f09f8ab438c465b71df581a43.jpg',
    'knight': 'https://i.pinimg.com/736x/93/84/9f/93849fa5c577756a346cd6c4172b384d.jpg',
    'pit_fiend':'https://i.pinimg.com/736x/ba/da/ea/badaeac665b0da85c91f0a77735ed696.jpg',
    'demon': 'https://i.pinimg.com/736x/72/33/df/7233df1487c23073f5e9c58131adb12a.jpg',
    'succubus': 'https://i.pinimg.com/736x/fa/42/88/fa4288f0a7cafc214457c85e72690663.jpg',
    'demon_general':'https://i.pinimg.com/1200x/b8/76/2c/b8762c3a52d031fa4dcebc8e44eacfb1.jpg',
    'lich': 'https://i.pinimg.com/736x/78/95/a5/7895a5a57b658cc1db2950484511a93d.jpg',
    'catacomb_lord':'https://i.pinimg.com/736x/fe/3f/f3/fe3ff3a147e5eb02148c1a4dfda7eba5.jpg',
    'dark_knight':'https://i.pinimg.com/1200x/0b/99/0e/0b990e5d9114228138810bb57d723685.jpg',
    'gargoyle':'https://i.pinimg.com/736x/a1/74/6c/a1746c29e6d52dcb6bb2e7ff8f96f04c.jpg',
    'death_knight':'https://i.pinimg.com/1200x/44/10/95/441095468e8537407825c3ae9c58040e.jpg',
    'castle_overlord':'https://i.pinimg.com/736x/57/7e/05/577e05fa5cf07bec6ecc5dd15eed2281.jpg',
    'imp':'https://i.pinimg.com/1200x/6d/39/e0/6d39e0250a65f8e586cd7aae8b8c3538.jpg',
    
    'dragon': 'https://abrakadabra.fun/uploads/posts/2022-03/1646721873_1-abrakadabra-fun-p-pauk-fantezi-art-1.jpg',
    'dragon_ancient': 'https://i.pinimg.com/736x/87/53/0b/87530bc6086bd4760304d56c1bd452ca.jpg',
    'titan': 'https://img.freepik.com/free-photo/titan_23-2150911270.jpg',
    'fallen_god': 'https://i.pinimg.com/1200x/ae/f3/f8/aef3f8083a8c3b85526131e8991fe460.jpg',
    'forest_spider':'https://i.pinimg.com/1200x/6b/17/a8/6b17a8e5f64f24e2eae2ae468840de76.jpg',
    'wild_boar':'https://i.pinimg.com/736x/cf/8f/57/cf8f57e07d4a1b2a468fa90f8ca0e083.jpg',
    'forest_troll':'https://i.pinimg.com/736x/ae/80/26/ae8026a1ec5a321226c0d2edea140840.jpg',
    'frost_spider': 'https://i.pinimg.com/1200x/f4/7e/d5/f47ed5b2672fc9b63acab360f3464c6d.jpg',
    'forest_guardian':'https://i.pinimg.com/1200x/50/dd/fa/50ddfa68afdc12925fbd2fb3140fe8f7.jpg',
    'village': 'https://i.pinimg.com/736x/50/b6/36/50b636f399c41e8697972676ebe85dff.jpg',
    'void_walker':'https://i.pinimg.com/736x/d7/20/ae/d720aea9c8efa589e991ab14143a7c5e.jpg',
    #рыбалка
    'pier': 'https://i.pinimg.com/1200x/e9/cb/d8/e9cbd8f837b30bf1d0385e0e32aa790e.jpg',
    'drowned': 'https://i.pinimg.com/1200x/b8/9f/c4/b89fc4239c083a908c972633d6d2668f.jpg',
    'kraken': 'https://i.pinimg.com/736x/de/0f/92/de0f92f2fa2ef3ea4acf028d7c5270ee.jpg',
    #локации
    'forest': 'https://img.freepik.com/premium-photo/ancient-forest-ai-generated_1127-13930.jpg',
    'castle': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTrAoGzKjgZxurLbxZ_Dyhtkm1gBqMUMtA87w&s',
    'dungeon': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSTZd9YHDcPOGmD8ezmHB0xD-HfA9O7OpgVyA&s',
    'training_camp': 'https://img1.liveinternet.ru/images/attach/b/2/1/726/1726838_full0011.jpg',
    'hell_gate': 'https://i.pinimg.com/736x/6e/d8/bb/6ed8bb536412c192f334b700988fa4d6.jpg',
    'throne_god': 'https://i.pinimg.com/1200x/f0/cb/f0/f0cbf0c6209a3f38e1545dc66a867ece.jpg',
    'shop': 'https://cubiq.ru/wp-content/uploads/2021/07/picture-1-15.jpeg',
    'inventory': 'https://freepngimg.com/thumb/backpack/22202-6-backpack-painting.png',
    'craft': 'https://abrakadabra.fun/uploads/posts/2022-01/1643486640_1-abrakadabra-fun-p-kuznitsa-art-1.jpg',
    'guild': 'https://www.worldanvil.com/uploads/images/9a7f5886e9dde2f96801a33e70e75345.jpg',
    'bank': 'https://i.pinimg.com/736x/4e/3e/c9/4e3ec9a87a689b1acd1f5da91d6d1fc2.jpg',
    # Трущобы
    'slums': 'https://i.pinimg.com/736x/c5/4f/44/c54f44d381b5a6d5e61b6f2152c3b4a2.jpg',
    #Клан босс
    'raid_boss':'https://i.pinimg.com/736x/75/c8/05/75c805793008563d6b8f6ebff52adacc.jpg'

    
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
        10: {'key': 'e1', 'name': '🏹 Точный выстрел', 'mana': 15, 'cd': 2, 'type': 'dmg_agi', 'val': 2.2, 'desc': 'Быстрый выстрел (зависит от Ловкости).'},
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
    },
    'vampire': {
        10: {'key': 'v1', 'name': '🦇 Укус', 'mana': 20, 'cd': 3, 'type': 'lifesteal', 'val': 1.8, 'desc': 'Урон (180%) и лечение от крови врага.'},
        25: {'key': 'v2', 'name': '🌫 Теневой шаг', 'mana': 35, 'cd': 4, 'type': 'buff_def', 'val': 0.1, 'desc': 'Превращение в туман. Избегание 90% урона (1 ход).'},
        40: {'key': 'v3', 'name': '🩸 Кровавая жатва', 'mana': 60, 'cd': 5, 'type': 'dmg_agi', 'val': 4.0, 'desc': 'Смертоносный удар от Ловкости (400%).'}
    },
    'lizardman': {
        10: {'key': 'lz1', 'name': '🦎 Удар хвостом', 'mana': 15, 'cd': 3, 'type': 'stun_dmg', 'val': 1.5, 'desc': 'Урон (150%) + шанс оглушить.'},
        25: {'key': 'lz2', 'name': '🛡 Толстая чешуя', 'mana': 30, 'cd': 4, 'type': 'buff_def', 'val': 0.5, 'desc': 'Снижает урон врага на 50% (1 ход).'},
        40: {'key': 'lz3', 'name': '🩸 Первобытная ярость', 'mana': 50, 'cd': 5, 'type': 'lifesteal', 'val': 3.0, 'desc': 'Разрывает врага (300%) и лечит.'}
    },
    'frogman': {
        10: {'key': 'fr1', 'name': '👅 Хлыст-язык', 'mana': 15, 'cd': 2, 'type': 'dmg_agi', 'val': 2.0, 'desc': 'Быстрый удар (зависит от Ловкости).'},
        25: {'key': 'fr2', 'name': '🤢 Токсичная слизь', 'mana': 35, 'cd': 4, 'type': 'magic_nuke', 'val': 2.5, 'desc': 'Магический ядовитый взрыв (250%).'},
        40: {'key': 'fr3', 'name': '🌊 Целебная трясина', 'mana': 50, 'cd': 5, 'type': 'heal', 'val': 0.8, 'desc': 'Восстанавливает 80% здоровья.'}
    },
    'leprechaun': {
        10: {'key': 'lep1', 'name': '🍀 Иллюзия', 'mana': 15, 'cd': 3, 'type': 'buff_def', 'val': 0.8, 'desc': 'Ложный силуэт. Снижает урон.'},
        25: {'key': 'lep2', 'name': '🪙 Монетный шквал', 'mana': 35, 'cd': 3, 'type': 'dmg_agi', 'val': 2.2, 'desc': 'Бьет врага магией от Ловкости.'},
        40: {'key': 'lep3', 'name': '🌈 Золотая лихорадка', 'mana': 60, 'cd': 5, 'type': 'heal_mana', 'val': 0.7, 'desc': 'Восстанавливает 70% ХП и лечит яды.'}
    },
    'undead': {
        10: {'key': 'und1', 'name': '🦴 Костяной панцирь', 'mana': 20, 'cd': 4, 'type': 'buff_def', 'val': 1.0, 'desc': 'Игнорирует 1 атаку (Блок).'},
        25: {'key': 'und2', 'name': '☠️ Могильный холод', 'mana': 35, 'cd': 3, 'type': 'stun_dmg', 'val': 1.8, 'desc': 'Урон (180%) + шанс заморозить (оглушить).'},
        40: {'key': 'und3', 'name': '🧟‍♂️ Восстание из мертвых', 'mana': 50, 'cd': 5, 'type': 'lifesteal', 'val': 3.5, 'desc': 'Разрывает плоть врага (350%) и восстанавливает себе ХП.'}
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
# --- БАЗА ПРЕДМЕТОВ ---
# --- БАЗА ПРЕДМЕТОВ ---
ITEMS_DB = {
    # --- ЕДА И ЗЕЛЬЯ ---
    'bread': {'name': '🍞 Заплесневелый хлеб', 'desc': 'На вкус как пыль.', 'price': 15, 'type': 'food', 'effect': 10, 'cat': 'food', 'rank': 'E'},
    'apple': {'name': '🍎 Дикое яблоко', 'desc': 'Кислое, но съедобное.', 'price': 20, 'type': 'food', 'effect': 15, 'cat': 'food', 'rank': 'E'},
    'meat_stew': {'name': '🍲 Похлебка бедняка', 'desc': 'Варево из неизвестного мяса.', 'price': 45, 'type': 'food', 'effect': 35, 'cat': 'food', 'rank': 'D'},
    'roast_boar': {'name': '🍖 Окорок вепря', 'desc': 'Жирное мясо, дающее силы.', 'price': 80, 'type': 'food', 'effect': 60, 'cat': 'food', 'rank': 'C'},
    'elven_wine': {'name': '🍷 Кровь Лозы', 'desc': 'Вино, настоянное на лунном свете.', 'price': 150, 'type': 'food', 'effect': 100, 'cat': 'food', 'rank': 'B'},
    'ambrosia': {'name': '🏺 Амброзия', 'desc': 'Пища богов.', 'price': 500, 'type': 'food', 'effect': 300, 'cat': 'food', 'rank': 'A'},
    'honey_hp': {'name': '🍯 Дикий мёд', 'desc': 'Сладкое золото. +50 HP', 'price': 60, 'type': 'potion', 'effect': 50, 'cat': 'food', 'rank': 'D'},
    'small_hp': {'name': '🧪 Слабый отвар', 'desc': 'Пахнет тиной.', 'price': 50, 'type': 'potion', 'effect': 30, 'cat': 'food', 'rank': 'E'},
    'medium_hp': {'name': '🧪 Зелье Крови', 'desc': 'Бурлящая алая жидкость.', 'price': 100, 'type': 'potion', 'effect': 70, 'cat': 'food', 'rank': 'D'},
    'large_hp': {'name': '🧪 Эссенция Жизни', 'desc': 'Чистая жизненная сила.', 'price': 250, 'type': 'potion', 'effect': 150, 'cat': 'food', 'rank': 'B'},
    'full_hp': {'name': '🧪 Слеза Феникса', 'desc': 'Восстанавливает тело из пепла.', 'price': 600, 'type': 'potion', 'effect': 500, 'cat': 'food', 'rank': 'S'},
    
    'small_mp': {'name': '🔮 Отвар ясности', 'desc': 'Просветляет разум.', 'price': 40, 'type': 'potion', 'effect': 20, 'cat': 'food', 'rank': 'E'},
    'large_mp': {'name': '🔮 Эликсир Бездны', 'desc': 'Наполняет вены магией.', 'price': 200, 'type': 'potion', 'effect': 100, 'cat': 'food', 'rank': 'B'},

    # --- ОРУЖИЕ (ФИЗИЧЕСКОЕ) ---
    'rusty_sword': {'name': '⚔️ Ржавый клинок', 'desc': 'Оружие мертвеца.', 'price': 150, 'type': 'weapon', 'effect': 5, 'cat': 'weapon', 'rank': 'E'},
    'iron_axe': {'name': '🪓 Топор палача', 'desc': 'Тяжелый, в крови.', 'price': 400, 'type': 'weapon', 'effect': 10, 'cat': 'weapon', 'rank': 'D'},
    'steel_saber': {'name': '⚔️ Гвардейская сабля', 'desc': 'Оружие рыцаря.', 'price': 900, 'type': 'weapon', 'effect': 15, 'cat': 'weapon', 'rank': 'C'},
    'dark_blade': {'name': '🗡️ Клинок Скорби', 'desc': 'Шепчет проклятия.', 'price': 2500, 'type': 'weapon', 'effect': 20, 'cat': 'weapon', 'rank': 'B'},
    'demon_slayer': {'name': '🔥 Убийца Демонов', 'desc': 'Пылает яростью.', 'price': 6000, 'type': 'weapon', 'effect': 30, 'cat': 'weapon', 'rank': 'A'},
    'god_killer': {'name': '⚡ Гнев Титана', 'desc': 'Раскалывает небо.', 'price': 15000, 'type': 'weapon', 'effect': 50, 'cat': 'weapon', 'rank': 'S'},

    # --- МАГИЧЕСКОЕ ОРУЖИЕ (ПОСОХИ) ---
    'wooden_staff': {'name': '🔮 Посох ученика', 'desc': 'Деревянная палка.', 'price': 150, 'type': 'magic_weapon', 'effect': 5, 'cat': 'weapon', 'rank': 'E'},
    'acolyte_wand': {'name': '🔮 Жезл Аколита', 'desc': 'Искрится магией.', 'price': 400, 'type': 'magic_weapon', 'effect': 10, 'cat': 'weapon', 'rank': 'D'},
    'crystal_staff': {'name': '💠 Кристальный посох', 'desc': 'Фокусирует энергию.', 'price': 900, 'type': 'magic_weapon', 'effect': 15, 'cat': 'weapon', 'rank': 'C'},
    'void_scepter': {'name': '🌑 Скипетр Пустоты', 'desc': 'Излучает тьму.', 'price': 2500, 'type': 'magic_weapon', 'effect': 20, 'cat': 'weapon', 'rank': 'B'},
    'archmage_staff': {'name': '🔥 Посох Архимага', 'desc': 'Пылает вечным огнем.', 'price': 6000, 'type': 'magic_weapon', 'effect': 30, 'cat': 'weapon', 'rank': 'A'},
    'world_tree_branch': {'name': '🌿 Ветвь Древа', 'desc': 'Сила самой природы.', 'price': 15000, 'type': 'magic_weapon', 'effect': 50, 'cat': 'weapon', 'rank': 'S'},
    # ==========================================
    # === НОВОЕ ОРУЖИЕ НА ЛОВКОСТЬ (agi_weapon) ===
    # ==========================================
    # Ранг E
    'dagger_rusty': {'name': '🗡️ Ржавый кинжал', 'desc': 'Оружие вора.', 'price': 180, 'type': 'agi_weapon', 'effect': 6, 'cat': 'weapon', 'rank': 'E'},
    'bone_shiv': {'name': '🗡️ Костяная заточка', 'desc': 'Сделана из ребра.', 'price': 250, 'type': 'agi_weapon', 'effect': 8, 'cat': 'weapon', 'rank': 'E'},
    # Ранг D
    'hunter_knife': {'name': '🗡️ Охотничий нож', 'desc': 'Хорош для снятия шкур.', 'price': 500, 'type': 'agi_weapon', 'effect': 14, 'cat': 'weapon', 'rank': 'D'},
    'short_bow': {'name': '🏹 Короткий лук', 'desc': 'Бьет издалека.', 'price': 700, 'type': 'agi_weapon', 'effect': 18, 'cat': 'weapon', 'rank': 'D'},
    # Ранг C
    'poison_stiletto': {'name': '🗡️ Отравленный стилет', 'desc': 'Лезвие в зеленой слизи.', 'price': 1500, 'type': 'agi_weapon', 'effect': 28, 'cat': 'weapon', 'rank': 'C'},
    'curved_saber': {'name': '⚔️ Изогнутая сабля', 'desc': 'Оружие пустынных наемников.', 'price': 1900, 'type': 'agi_weapon', 'effect': 32, 'cat': 'weapon', 'rank': 'C'},
    # Ранг B
    'assassin_dagger': {'name': '🗡️ Кинжал Убийцы', 'desc': 'Не издает звука при ударе.', 'price': 4000, 'type': 'agi_weapon', 'effect': 50, 'cat': 'weapon', 'rank': 'B'},
    'elven_bow': {'name': '🏹 Эльфийский длинный лук', 'desc': 'Стрелы летят быстрее ветра.', 'price': 5500, 'type': 'agi_weapon', 'effect': 65, 'cat': 'weapon', 'rank': 'B'},
    # Ранг A
    'shadow_blades': {'name': '⚔️ Парные Клинки Тени', 'desc': 'Рассекают саму тьму.', 'price': 10000, 'type': 'agi_weapon', 'effect': 90, 'cat': 'weapon', 'rank': 'A'},
    'wyvern_fang': {'name': '🐍 Клык Виверны', 'desc': 'Яд разъедает доспехи.', 'price': 13000, 'type': 'agi_weapon', 'effect': 110, 'cat': 'weapon', 'rank': 'A'},
    # Ранг S
    'meteor_shard': {'name': '🗡️ Осколок Метеорита', 'desc': 'Кинжал из упавшей звезды.', 'price': 22000, 'type': 'agi_weapon', 'effect': 160, 'cat': 'weapon', 'rank': 'S'},
    'eclipse_bow': {'name': '🏹 Лук Затмения', 'desc': 'Стреляет чистой пустотой.', 'price': 28000, 'type': 'agi_weapon', 'effect': 200, 'cat': 'weapon', 'rank': 'S'},

    # ==========================================
    # === НОВАЯ БРОНЯ (ПО 5 ШТУК НА РАНГ) ===
    # ==========================================
    # Ранг E
    'e_heavy_1': {'name': '🛡️ Деревянный щит и цепь', 'desc': 'Собрано на свалке.', 'price': 180, 'type': 'heavy_armor', 'effect': 8, 'cat': 'armor', 'rank': 'E'},
    'e_heavy_2': {'name': '🛡️ Медный нагрудник', 'desc': 'Тяжелый и погнутый.', 'price': 300, 'type': 'heavy_armor', 'effect': 14, 'cat': 'armor', 'rank': 'E'},
    'e_light_1': {'name': '💨 Обноски бродяги', 'desc': 'Совсем не стесняют.', 'price': 150, 'type': 'light_armor', 'effect': 8, 'cat': 'armor', 'rank': 'E'},
    'e_light_2': {'name': '💨 Шкура кабана', 'desc': 'Грубая, но прочная.', 'price': 280, 'type': 'light_armor', 'effect': 14, 'cat': 'armor', 'rank': 'E'},
    'e_magic_1': {'name': '🔮 Рваная ряса', 'desc': 'Хранит остатки магии.', 'price': 250, 'type': 'magic_armor', 'effect': 12, 'cat': 'armor', 'rank': 'E'},

    # Ранг D
    'd_heavy_1': {'name': '🛡️ Бронзовая кираса', 'desc': 'Сверкает на солнце.', 'price': 500, 'type': 'heavy_armor', 'effect': 20, 'cat': 'armor', 'rank': 'D'},
    'd_heavy_2': {'name': '🛡️ Доспех стражника', 'desc': 'Снят с мертвого патрульного.', 'price': 850, 'type': 'heavy_armor', 'effect': 28, 'cat': 'armor', 'rank': 'D'},
    'd_light_1': {'name': '💨 Усиленная кожанка', 'desc': 'С заклепками.', 'price': 450, 'type': 'light_armor', 'effect': 18, 'cat': 'armor', 'rank': 'D'},
    'd_light_2': {'name': '💨 Охотничий камзол', 'desc': 'Сливается с листвой.', 'price': 800, 'type': 'light_armor', 'effect': 26, 'cat': 'armor', 'rank': 'D'},
    'd_magic_1': {'name': '🔮 Накидка аколита', 'desc': 'Защищает от сглаза.', 'price': 700, 'type': 'magic_armor', 'effect': 22, 'cat': 'armor', 'rank': 'D'},

    # Ранг C
    'c_heavy_1': {'name': '🛡️ Костяной доспех', 'desc': 'Собран из ребер гулей.', 'price': 1200, 'type': 'heavy_armor', 'effect': 38, 'cat': 'armor', 'rank': 'C'},
    'c_heavy_2': {'name': '🛡️ Латы Крестоносца', 'desc': 'Святая сталь.', 'price': 1800, 'type': 'heavy_armor', 'effect': 50, 'cat': 'armor', 'rank': 'C'},
    'c_light_1': {'name': '💨 Плащ Тени', 'desc': 'Делает шаги бесшумными.', 'price': 1100, 'type': 'light_armor', 'effect': 35, 'cat': 'armor', 'rank': 'C'},
    'c_light_2': {'name': '💨 Змеиная чешуя', 'desc': 'Скользкая броня.', 'price': 1700, 'type': 'light_armor', 'effect': 48, 'cat': 'armor', 'rank': 'C'},
    'c_magic_1': {'name': '🔮 Мантия Иллюзиониста', 'desc': 'Искажает силуэт.', 'price': 1500, 'type': 'magic_armor', 'effect': 42, 'cat': 'armor', 'rank': 'C'},

    # Ранг B
    'b_heavy_1': {'name': '🛡️ Руническая кираса', 'desc': 'Гномья ковка.', 'price': 4000, 'type': 'heavy_armor', 'effect': 75, 'cat': 'armor', 'rank': 'B'},
    'b_heavy_2': {'name': '🛡️ Доспех Кровавого Барона', 'desc': 'Впитывает кровь.', 'price': 6500, 'type': 'heavy_armor', 'effect': 95, 'cat': 'armor', 'rank': 'B'},
    'b_light_1': {'name': '💨 Накидка Ассасина', 'desc': 'Вплетены нити тени.', 'price': 3800, 'type': 'light_armor', 'effect': 70, 'cat': 'armor', 'rank': 'B'},
    'b_light_2': {'name': '💨 Эльфийский доспех', 'desc': 'Легче пуха.', 'price': 6000, 'type': 'light_armor', 'effect': 90, 'cat': 'armor', 'rank': 'B'},
    'b_magic_1': {'name': '🔮 Мантия Крови', 'desc': 'Усиливает заклинания.', 'price': 5500, 'type': 'magic_armor', 'effect': 85, 'cat': 'armor', 'rank': 'B'},

    # Ранг A
    'a_heavy_1': {'name': '🛡️ Демонический панцирь', 'desc': 'Обжигает при касании.', 'price': 12000, 'type': 'heavy_armor', 'effect': 140, 'cat': 'armor', 'rank': 'A'},
    'a_heavy_2': {'name': '🛡️ Обсидиановые латы', 'desc': 'Тверже алмаза.', 'price': 18000, 'type': 'heavy_armor', 'effect': 180, 'cat': 'armor', 'rank': 'A'},
    'a_light_1': {'name': '💨 Броня Владыки Ветров', 'desc': 'Дарует сверхскорость.', 'price': 11500, 'type': 'light_armor', 'effect': 130, 'cat': 'armor', 'rank': 'A'},
    'a_light_2': {'name': '💨 Одеяние Призрака', 'desc': 'Оружие проходит насквозь.', 'price': 17000, 'type': 'light_armor', 'effect': 170, 'cat': 'armor', 'rank': 'A'},
    'a_magic_1': {'name': '🔮 Регалии Архимага', 'desc': 'Соткано из маны.', 'price': 15000, 'type': 'magic_armor', 'effect': 160, 'cat': 'armor', 'rank': 'A'},

    # Ранг S
    's_heavy_1': {'name': '🛡️ Доспех Падшего Бога', 'desc': 'Абсолютная защита.', 'price': 30000, 'type': 'heavy_armor', 'effect': 260, 'cat': 'armor', 'rank': 'S'},
    's_heavy_2': {'name': '🛡️ Титановый Монолит', 'desc': 'Вы — ходячая крепость.', 'price': 45000, 'type': 'heavy_armor', 'effect': 320, 'cat': 'armor', 'rank': 'S'},
    's_light_1': {'name': '💨 Эфирный Плащ', 'desc': 'Вы существуете между мирами.', 'price': 28000, 'type': 'light_armor', 'effect': 240, 'cat': 'armor', 'rank': 'S'},
    's_light_2': {'name': '💨 Доспех Искажения', 'desc': 'Манипулирует пространством.', 'price': 42000, 'type': 'light_armor', 'effect': 300, 'cat': 'armor', 'rank': 'S'},
    's_magic_1': {'name': '🔮 Покров Хаоса', 'desc': 'Бесконечная магическая мощь.', 'price': 38000, 'type': 'magic_armor', 'effect': 280, 'cat': 'armor', 'rank': 'S'},
    # --- ТЯЖЕЛАЯ БРОНЯ (Воин/Дварф) ---
    'rusty_chainmail': {'name': '🛡️ Ржавая кольчуга', 'desc': 'Тяжелая и дырявая.', 'price': 250, 'type': 'heavy_armor', 'effect': 10, 'cat': 'armor', 'rank': 'E'}, 
    'chainmail': {'name': '🛡️ Кольчуга стража', 'desc': 'Надежная сталь.', 'price': 350, 'type': 'heavy_armor', 'effect': 15, 'cat': 'armor', 'rank': 'D'},
    'plate_armor': {'name': '🛡️ Латы Рыцаря', 'desc': 'Стальная стена.', 'price': 800, 'type': 'heavy_armor', 'effect': 25, 'cat': 'armor', 'rank': 'C'},
    'dragon_scale': {'name': '🛡️ Драконьи латы', 'desc': 'Непробиваемая чешуя.', 'price': 3000, 'type': 'heavy_armor', 'effect': 60, 'cat': 'armor', 'rank': 'B'},
    'dragon_mail': {'name': '🐉 Доспех Дракона', 'desc': 'Легендарная защита.', 'price': 5500, 'type': 'heavy_armor', 'effect': 70, 'cat': 'armor', 'rank': 'A'},

    # --- ЛЕГКАЯ БРОНЯ (Эльф/Вор) ---
    'leather_vest': {'name': '💨 Кожанка вора', 'desc': 'Не сковывает движения.', 'price': 200, 'type': 'light_armor', 'effect': 10, 'cat': 'armor', 'rank': 'E'},
    'hunter_gear': {'name': '🌿 Плащ следопыта', 'desc': 'Сливается с лесом.', 'price': 750, 'type': 'light_armor', 'effect': 24, 'cat': 'armor', 'rank': 'D'},
    'shadow_cloak': {'name': '🌑 Плащ Теней', 'desc': 'Вы становитесь призраком.', 'price': 2800, 'type': 'light_armor', 'effect': 50, 'cat': 'armor', 'rank': 'B'},
# НОВОЕ: Добавлена роба для B ранга
    'shadow_robe': {'name': '🌑 Мантия Теней', 'desc': 'Соткана из ночного тумана.', 'price': 3200, 'type': 'magic_armor', 'effect': 55, 'cat': 'armor', 'rank': 'B'},
    # --- МАГИЧЕСКИЕ РОБЫ (Маг/Эльф) ---
    'apprentice_robe': {'name': '🔮 Роба ученика', 'desc': 'Пахнет старыми книгами.', 'price': 200, 'type': 'magic_armor', 'effect': 10, 'cat': 'armor', 'rank': 'E'},
    'archmage_robe': {'name': '🌟 Звездная мантия', 'desc': 'Сияет магией.', 'price': 800, 'type': 'magic_armor', 'effect': 25, 'cat': 'armor', 'rank': 'D'},
    # ИСПРАВЛЕНО: Мифрил теперь C ранг (цена снижена, чтобы соответствовать этапу Катакомб)
    'mithril_armor': {'name': '💠 Мифриловая роба', 'desc': 'Легкая как перо.', 'price': 1500, 'type': 'magic_armor', 'effect': 40, 'cat': 'armor', 'rank': 'C'},
    'void_robe': {'name': '🌌 Покров Пустоты', 'desc': 'Поглощает заклинания.', 'price': 6000, 'type': 'magic_armor', 'effect': 75, 'cat': 'armor', 'rank': 'A'},
    'void_plate': {'name': '🌌 Доспех Пустоты (Маг)', 'desc': 'Абсолютная защита.', 'price': 12000, 'type': 'magic_armor', 'effect': 100, 'cat': 'armor', 'rank': 'S'},

    # --- АКСЕССУАРЫ ---
    'wooden_ring': {'name': '💍 Кольцо из корня', 'desc': 'Слабый оберег.', 'price': 200, 'type': 'artifact', 'effect': 2, 'cat': 'acc', 'rank': 'E'},
    'silver_amulet': {'name': '🧿 Глаз Ведьмы', 'desc': 'Смотрит в душу.', 'price': 500, 'type': 'artifact', 'effect': 5, 'cat': 'acc', 'rank': 'D'},
    'gold_ring': {'name': '💍 Перстень Барона', 'desc': 'Украден с трупа.', 'price': 1200, 'type': 'artifact', 'effect': 10, 'cat': 'acc', 'rank': 'C'},
    'skull_necklace': {'name': '💀 Лик Смерти', 'desc': 'Усиливает магию.', 'price': 3000, 'type': 'artifact', 'effect': 20, 'cat': 'acc', 'rank': 'B'},
    'demon_eye': {'name': '👁️ Око Бездны', 'desc': 'Запретные знания.', 'price': 7000, 'type': 'artifact', 'effect': 35, 'cat': 'acc', 'rank': 'A'},

    # --- МАТЕРИАЛЫ ---
    'wolf_pelt': {'name': '🐺 Волчья шкура', 'desc': 'Жесткая шерсть.', 'price': 5, 'type': 'material', 'cat': 'mat', 'rank': 'E'},
    'goblin_ear': {'name': '👂 Ухо гоблина', 'desc': 'Трофей.', 'price': 8, 'type': 'material', 'cat': 'mat', 'rank': 'E'},
    'slime_goo': {'name': '🟢 Едкая слизь', 'desc': 'Прожигает ткань.', 'price': 6, 'type': 'material', 'cat': 'mat', 'rank': 'E'},
    'iron_ore': {'name': '🪨 Железная руда', 'desc': 'Тяжелый кусок.', 'price': 15, 'type': 'material', 'cat': 'mat', 'rank': 'D'},
    'spider_silk': {'name': '🕸️ Живая паутина', 'desc': 'Прочная.', 'price': 20, 'type': 'material', 'cat': 'mat', 'rank': 'D'},
    'bone_dust': {'name': '💀 Прах мертвеца', 'desc': 'Холодный.', 'price': 25, 'type': 'material', 'cat': 'mat', 'rank': 'C'},
    'vampire_fang': {'name': '🧛 Клык вампира', 'desc': 'Острый.', 'price': 60, 'type': 'material', 'cat': 'mat', 'rank': 'B'},
    'demon_horn': {'name': '😈 Рог демона', 'desc': 'Излучает жар.', 'price': 100, 'type': 'material', 'cat': 'mat', 'rank': 'A'},
    'void_crystal': {'name': '🌌 Осколок Пустоты', 'desc': 'Из другого мира.', 'price': 300, 'type': 'material', 'cat': 'mat', 'rank': 'S'},
# --- ДОБАВИТЬ В ITEMS_DB ---
    # === РЫБАЛКА ===
    'bait_worm': {'name': '🪱 Жирный червь', 'desc': 'Наживка для рыбы.', 'price': 10, 'type': 'material', 'cat': 'mat', 'rank': 'E'},
    'fish_blind': {'name': '🐟 Слепая рыба', 'desc': 'Бледная рыбешка.', 'price': 25, 'type': 'material', 'cat': 'mat', 'rank': 'E'},
    'fish_golden': {'name': '🐡 Золотой карп', 'desc': 'Светится в темноте!', 'price': 150, 'type': 'material', 'cat': 'mat', 'rank': 'C'},
    'trash_boot': {'name': '👢 Дырявый сапог', 'desc': 'Пахнет болотом.', 'price': 2, 'type': 'material', 'cat': 'mat', 'rank': 'E'},
    
    'fish_soup': {'name': '🍲 Наваристая уха', 'desc': '+200 HP, +50 MP', 'price': 150, 'type': 'food', 'effect': 200, 'cat': 'food', 'rank': 'D'},
# ==========================
    # 🌿 РЕСУРСЫ (ТРАВНИК)
    # ==========================
    
    # E Ранг (Руины)
    'moss_lichen': {'name': '🌿 Мшистый лишайник', 'price': 2, 'type': 'material', 'rank': 'E'},
    'ruin_wormwood': {'name': '🌿 Руинная полынь', 'price': 3, 'type': 'material', 'rank': 'E'},
    'stone_beetle': {'name': '🐞 Каменный жук', 'price': 4, 'type': 'material', 'rank': 'E'},
    'firefly_shard': {'name': '🐞 Светлячок-обломок', 'price': 4, 'type': 'material', 'rank': 'E'},
    'ancient_shard': {'name': '🪨 Осколок камня', 'price': 5, 'type': 'material', 'rank': 'E'},
    'dust_ages': {'name': '🪨 Пыль веков', 'price': 2, 'type': 'material', 'rank': 'E'},
    'stone_berry': {'name': '🍓 Каменная ягода', 'price': 3, 'type': 'material', 'rank': 'E'},
    'ruin_rose': {'name': '🌸 Руинная роза', 'price': 10, 'type': 'material', 'rank': 'E'},

    # D Ранг (Лес)
    'forest_fern': {'name': '🌿 Лесной папоротник', 'price': 5, 'type': 'material', 'rank': 'D'},
    'life_root': {'name': '🌿 Корень жизни', 'price': 8, 'type': 'material', 'rank': 'D'},
    'hypericum': {'name': '🌿 Зверобой', 'price': 6, 'type': 'material', 'rank': 'D'},
    'forest_raspberry': {'name': '🍓 Лесная малина', 'price': 5, 'type': 'material', 'rank': 'D'},
    'blueberry': {'name': '🍓 Черника', 'price': 5, 'type': 'material', 'rank': 'D'},
    'wolf_berry': {'name': '🍓 Волчья ягода', 'price': 4, 'type': 'material', 'rank': 'D'},
    'leaf_beetle': {'name': '🐞 Жук-листоед', 'price': 6, 'type': 'material', 'rank': 'D'},
    'woodlice': {'name': '🐞 Мокрица', 'price': 3, 'type': 'material', 'rank': 'D'},
    'river_pebble': {'name': '🪨 Речная галька', 'price': 4, 'type': 'material', 'rank': 'D'},
    'flint': {'name': '🪨 Кремень', 'price': 7, 'type': 'material', 'rank': 'D'},
    'violet': {'name': '🌸 Фиалка', 'price': 8, 'type': 'material', 'rank': 'D'},
    'lily_valley': {'name': '🌸 Ландыш', 'price': 9, 'type': 'material', 'rank': 'D'},

    # C Ранг (Катакомбы)
    'mycelium': {'name': '🌿 Грибница', 'price': 10, 'type': 'material', 'rank': 'C'},
    'grave_moss': {'name': '🌿 Могильный мох', 'price': 12, 'type': 'material', 'rank': 'C'},
    'corpse_root': {'name': '🌿 Трупный корень', 'price': 15, 'type': 'material', 'rank': 'C'},
    'cave_cricket': {'name': '🐞 Пещерный сверчок', 'price': 12, 'type': 'material', 'rank': 'C'},
    'bone_beetle': {'name': '🐞 Костяной жук', 'price': 14, 'type': 'material', 'rank': 'C'},
    'glowing_larva': {'name': '🐞 Светящаяся личинка', 'price': 16, 'type': 'material', 'rank': 'C'},
    'bone_crumbs': {'name': '🪨 Костяная крошка', 'price': 10, 'type': 'material', 'rank': 'C'},
    'limestone': {'name': '🪨 Известняк', 'price': 11, 'type': 'material', 'rank': 'C'},
    'sarcophagus_shard': {'name': '🪨 Осколок саркофага', 'price': 20, 'type': 'material', 'rank': 'C'},
    'ghost_orchid': {'name': '🌸 Призрачная орхидея', 'price': 25, 'type': 'material', 'rank': 'C'},
    'bone_berry': {'name': '🍓 Костяника', 'price': 15, 'type': 'material', 'rank': 'C'},

    # B Ранг (Замок)
    'royal_thyme': {'name': '🌿 Королевский тимьян', 'price': 25, 'type': 'material', 'rank': 'B'},
    'castle_ivy': {'name': '🌿 Замковый плющ', 'price': 20, 'type': 'material', 'rank': 'B'},
    'knight_cherry': {'name': '🍓 Рыцарская вишня', 'price': 30, 'type': 'material', 'rank': 'B'},
    'baron_currant': {'name': '🍓 Барская смородина', 'price': 28, 'type': 'material', 'rank': 'B'},
    'velvet_beetle': {'name': '🐞 Бархатный жук', 'price': 35, 'type': 'material', 'rank': 'B'},
    'moth': {'name': '🐞 Моль-чешуйница', 'price': 30, 'type': 'material', 'rank': 'B'},
    'duke_lily': {'name': '🌸 Лилия герцога', 'price': 50, 'type': 'material', 'rank': 'B'},
    'rosehip': {'name': '🌸 Шиповник', 'price': 20, 'type': 'material', 'rank': 'B'},
    'marble_chips': {'name': '🪨 Мраморная крошка', 'price': 25, 'type': 'material', 'rank': 'B'},
    'rusty_iron': {'name': '🪨 Ржавое железо', 'price': 15, 'type': 'material', 'rank': 'B'},
    'precious_shard': {'name': '🪨 Драгоценный осколок', 'price': 60, 'type': 'material', 'rank': 'B'},

    # A Ранг (Пекло)
    'hell_nettle': {'name': '🌿 Адская крапива', 'price': 60, 'type': 'material', 'rank': 'A'},
    'devil_claw': {'name': '🌿 Дьявольский коготь', 'price': 70, 'type': 'material', 'rank': 'A'},
    'flame_berry': {'name': '🍓 Пламенная ягода', 'price': 65, 'type': 'material', 'rank': 'A'},
    'blood_berry': {'name': '🍓 Кровавая ягода', 'price': 75, 'type': 'material', 'rank': 'A'},
    'fire_fly': {'name': '🐞 Огненная муха', 'price': 80, 'type': 'material', 'rank': 'A'},
    'demon_roach': {'name': '🐞 Демон-таракан', 'price': 70, 'type': 'material', 'rank': 'A'},
    'lava_stone': {'name': '🪨 Лавовый камень', 'price': 90, 'type': 'material', 'rank': 'A'},
    'sinner_ash': {'name': '🪨 Пепел грешников', 'price': 50, 'type': 'material', 'rank': 'A'},
    'obsidian': {'name': '🪨 Обсидиан', 'price': 100, 'type': 'material', 'rank': 'A'},
    'fire_rose': {'name': '🌸 Огненная роза', 'price': 120, 'type': 'material', 'rank': 'A'},
    'hell_lily': {'name': '🌸 Адская лилия', 'price': 130, 'type': 'material', 'rank': 'A'},

    # S Ранг (Хаос)
    'chaos_grass': {'name': '🌿 Трава хаоса', 'price': 200, 'type': 'material', 'rank': 'S'},
    'star_moss': {'name': '🌿 Звёздный мох', 'price': 250, 'type': 'material', 'rank': 'S'},
    'cosmic_berry': {'name': '🍓 Космическая ягода', 'price': 300, 'type': 'material', 'rank': 'S'},
    'void_berry': {'name': '🍓 Ягода пустоты', 'price': 350, 'type': 'material', 'rank': 'S'},
    'crystal_dragonfly': {'name': '🐞 Кристальная стрекоза', 'price': 400, 'type': 'material', 'rank': 'S'},
    'phantom_beetle': {'name': '🐞 Фантомный жук', 'price': 380, 'type': 'material', 'rank': 'S'},
    'chaos_shard': {'name': '🪨 Осколок хаоса', 'price': 500, 'type': 'material', 'rank': 'S'},
    'aether_crystal': {'name': '🪨 Эфирный кристалл', 'price': 600, 'type': 'material', 'rank': 'S'},
    'primordial_matter': {'name': '🪨 Праматерия', 'price': 1000, 'type': 'material', 'rank': 'S'},
    'void_flower': {'name': '🌸 Цветок бездны', 'price': 700, 'type': 'material', 'rank': 'S'},
    'chaos_nectarine': {'name': '🌸 Нектарин хаоса', 'price': 800, 'type': 'material', 'rank': 'S'},


    # ==========================
    # 🧪 ЗЕЛЬЯ (ГОТОВЫЕ)
    # ==========================
    # E Ранг
    'pot_small_hp': {'name': '🧪 Малое лечебное', 'desc': '+30 HP', 'price': 30, 'type': 'potion', 'effect': 30, 'cat': 'food', 'rank': 'E'},
    'pot_small_mp': {'name': '🔮 Малое магическое', 'desc': '+20 MP', 'price': 30, 'type': 'potion', 'effect': 20, 'cat': 'food', 'rank': 'E'},
    'pot_small_str': {'name': '🧪 Малая мощь', 'desc': '+5 Физ.урона (2 хода)', 'price': 50, 'type': 'buff_potion', 'buff_type': 'strength', 'effect': 5, 'duration': 2, 'rank': 'E'},
    'pot_stone_skin': {'name': '🧪 Каменная кожа', 'desc': '+10 Брони (2 хода)', 'price': 50, 'type': 'buff_potion', 'buff_type': 'armor', 'effect': 10, 'duration': 2, 'rank': 'E'},
    'pot_agility': {'name': '🧪 Проворство', 'desc': '+2 Ловкости (2 хода)', 'price': 50, 'type': 'buff_potion', 'buff_type': 'agility', 'effect': 2, 'duration': 2, 'rank': 'E'},
    'pot_poison_touch': {'name': '☠️ Ядовитое касание', 'desc': 'Оружие отравляет (10 ур/ход)', 'price': 60, 'type': 'buff_potion', 'buff_type': 'poison_weapon', 'effect': 10, 'duration': 3, 'rank': 'E'},
    'pot_wind_speed': {'name': '🧪 Скорость ветра', 'desc': '+10% Уворота (2 хода)', 'price': 60, 'type': 'buff_potion', 'buff_type': 'agility', 'effect': 10, 'duration': 2, 'rank': 'E'},

    # D Ранг
    'pot_medium_hp': {'name': '🧪 Лечебное зелье', 'desc': '+60 HP', 'price': 60, 'type': 'potion', 'effect': 60, 'cat': 'food', 'rank': 'D'},
    'pot_mana_rec': {'name': '🔮 Восстановление маны', 'desc': '+40 MP', 'price': 60, 'type': 'potion', 'effect': 40, 'cat': 'food', 'rank': 'D'},
    'pot_forest_rage': {'name': '🧪 Ярость леса', 'desc': '+10 Физ.урона (3 хода)', 'price': 100, 'type': 'buff_potion', 'buff_type': 'strength', 'effect': 10, 'duration': 3, 'rank': 'D'},
    'pot_flower_magic': {'name': '🧪 Магия цветов', 'desc': '+5 Маг.урона (3 хода)', 'price': 100, 'type': 'buff_potion', 'buff_type': 'intelligence', 'effect': 5, 'duration': 3, 'rank': 'D'},
    'pot_oak_skin': {'name': '🧪 Дубовая броня', 'desc': '+20 Брони (3 хода)', 'price': 120, 'type': 'buff_potion', 'buff_type': 'armor', 'effect': 20, 'duration': 3, 'rank': 'D'},
    'pot_evasion': {'name': '🧪 Уклонение', 'desc': '+4 Ловкости (3 хода)', 'price': 120, 'type': 'buff_potion', 'buff_type': 'agility', 'effect': 4, 'duration': 3, 'rank': 'D'},
    'pot_fire_cloak': {'name': '🔥 Огненный плащ', 'desc': 'Жжет врага при атаке (10 ур).', 'price': 150, 'type': 'buff_potion', 'buff_type': 'fire_shield', 'effect': 10, 'duration': 2, 'rank': 'D'},

    # C Ранг
    'pot_elixir_life': {'name': '🧪 Эликсир жизни', 'desc': '+100 HP', 'price': 150, 'type': 'potion', 'effect': 100, 'cat': 'food', 'rank': 'C'},
    'pot_necro': {'name': '🔮 Некромантия', 'desc': '+70 MP', 'price': 150, 'type': 'potion', 'effect': 70, 'cat': 'food', 'rank': 'C'},
    'pot_bone_str': {'name': '🧪 Костяная сила', 'desc': '+15 Физ.урона (4 хода)', 'price': 200, 'type': 'buff_potion', 'buff_type': 'strength', 'effect': 15, 'duration': 4, 'rank': 'C'},
    'pot_ghost_pow': {'name': '🧪 Призрачная мощь', 'desc': '+10 Маг.урона (4 хода)', 'price': 200, 'type': 'buff_potion', 'buff_type': 'intelligence', 'effect': 10, 'duration': 4, 'rank': 'C'},
    'pot_dead_armor': {'name': '🧪 Броня мертвеца', 'desc': '+30 Брони (4 хода)', 'price': 220, 'type': 'buff_potion', 'buff_type': 'armor', 'effect': 30, 'duration': 4, 'rank': 'C'},
    'pot_corpse_agi': {'name': '🧪 Трупная ловкость', 'desc': '+6 Ловкости (4 хода)', 'price': 220, 'type': 'buff_potion', 'buff_type': 'agility', 'effect': 6, 'duration': 4, 'rank': 'C'},
    'item_ice_spike': {'name': '❄️ Свиток Ледяного Шипа', 'desc': 'Наносит 40 урона (Однораз.)', 'price': 250, 'type': 'combat_item', 'effect': 40, 'rank': 'C'},

    # B Ранг
    'pot_knight_hp': {'name': '🧪 Рыцарское здоровье', 'desc': '+150 HP', 'price': 300, 'type': 'potion', 'effect': 150, 'cat': 'food', 'rank': 'B'},
    'pot_lord_mp': {'name': '🔮 Мана лорда', 'desc': '+100 MP', 'price': 300, 'type': 'potion', 'effect': 100, 'cat': 'food', 'rank': 'B'},
    'pot_steel_pow': {'name': '🧪 Мощь стали', 'desc': '+20 Физ.урона (5 ходов)', 'price': 400, 'type': 'buff_potion', 'buff_type': 'strength', 'effect': 20, 'duration': 5, 'rank': 'B'},
    'pot_duke_mag': {'name': '🧪 Герцогская магия', 'desc': '+15 Маг.урона (5 ходов)', 'price': 400, 'type': 'buff_potion', 'buff_type': 'intelligence', 'effect': 15, 'duration': 5, 'rank': 'B'},
    'pot_bastion': {'name': '🧪 Бастион', 'desc': '+40 Брони (5 ходов)', 'price': 450, 'type': 'buff_potion', 'buff_type': 'armor', 'effect': 40, 'duration': 5, 'rank': 'B'},
    'pot_ghost_evasion': {'name': '🧪 Призрачный уворот', 'desc': '+8 Ловкости (5 ходов)', 'price': 450, 'type': 'buff_potion', 'buff_type': 'agility', 'effect': 8, 'duration': 5, 'rank': 'B'},
    'pot_crit': {'name': '🧪 Критический удар', 'desc': 'Шанс крита +10% (5 ходов)', 'price': 500, 'type': 'buff_potion', 'buff_type': 'crit_chance', 'effect': 10, 'duration': 5, 'rank': 'B'},

    # A Ранг
    'pot_demon_blood': {'name': '🧪 Кровь демона', 'desc': '+250 HP', 'price': 600, 'type': 'potion', 'effect': 250, 'cat': 'food', 'rank': 'A'},
    'pot_void_nrg': {'name': '🔮 Энергия бездны', 'desc': '+150 MP', 'price': 600, 'type': 'potion', 'effect': 150, 'cat': 'food', 'rank': 'A'},
    'pot_hell_fury': {'name': '🧪 Ярость ада', 'desc': '+30 Физ.урона (6 ходов)', 'price': 800, 'type': 'buff_potion', 'buff_type': 'strength', 'effect': 30, 'duration': 6, 'rank': 'A'},
    'pot_mind_flame': {'name': '🧪 Пламя разума', 'desc': '+25 Маг.урона (6 ходов)', 'price': 800, 'type': 'buff_potion', 'buff_type': 'intelligence', 'effect': 25, 'duration': 6, 'rank': 'A'},
    'pot_lava_armor': {'name': '🧪 Лавовая броня', 'desc': '+60 Брони (6 ходов)', 'price': 900, 'type': 'buff_potion', 'buff_type': 'armor', 'effect': 60, 'duration': 6, 'rank': 'A'},
    'pot_devil_agi': {'name': '🧪 Дьявольская ловкость', 'desc': '+10 Ловкости (6 ходов)', 'price': 900, 'type': 'buff_potion', 'buff_type': 'agility', 'effect': 10, 'duration': 6, 'rank': 'A'},
    'pot_fire_aura': {'name': '🔥 Огненная аура', 'desc': '50 урона врагу каждый ход (3 хода)', 'price': 1000, 'type': 'buff_potion', 'buff_type': 'dot_aura', 'effect': 50, 'duration': 3, 'rank': 'A'},

    # S Ранг
    'pot_god_heal': {'name': '🧪 Божественное исцеление', 'desc': '+500 HP + Реген', 'price': 2000, 'type': 'potion', 'effect': 500, 'cat': 'food', 'rank': 'S'},
    'pot_inf_mana': {'name': '🔮 Бесконечная мана', 'desc': '+300 MP + Реген', 'price': 2000, 'type': 'potion', 'effect': 300, 'cat': 'food', 'rank': 'S'},
    'pot_chaos_pow': {'name': '🧪 Сила хаоса', 'desc': '+50 Физ.урона (8 ходов)', 'price': 2500, 'type': 'buff_potion', 'buff_type': 'strength', 'effect': 50, 'duration': 8, 'rank': 'S'},
    'pot_void_mag': {'name': '🧪 Магия пустоты', 'desc': '+40 Маг.урона (8 ходов)', 'price': 2500, 'type': 'buff_potion', 'buff_type': 'intelligence', 'effect': 40, 'duration': 8, 'rank': 'S'},
    'pot_chaos_def': {'name': '🧪 Твердыня хаоса', 'desc': '+100 Брони (8 ходов)', 'price': 3000, 'type': 'buff_potion', 'buff_type': 'armor', 'effect': 100, 'duration': 8, 'rank': 'S'},
    'pot_inv_step': {'name': '🧪 Незримая поступь', 'desc': '+15 Ловкости (8 ходов)', 'price': 3000, 'type': 'buff_potion', 'buff_type': 'agility', 'effect': 15, 'duration': 8, 'rank': 'S'},
    'pot_deadly_psn': {'name': '☠️ Смертельный яд', 'desc': '200 яда/ход', 'price': 3500, 'type': 'buff_potion', 'buff_type': 'poison_weapon', 'effect': 200, 'duration': 3, 'rank': 'S'},
    # === ФЕРМА И КУХНЯ ===
    'wheat': {'name': '🌾 Пшеница', 'price': 5, 'type': 'material', 'cat': 'mat', 'rank': 'E'},
    'carrot': {'name': '🥕 Сладкая морковь', 'price': 8, 'type': 'material', 'cat': 'mat', 'rank': 'D'},
    'potato': {'name': '🥔 Картофель', 'price': 10, 'type': 'material', 'cat': 'mat', 'rank': 'C'},
    'magic_bean': {'name': '🫘 Магический боб', 'price': 50, 'type': 'material', 'cat': 'mat', 'rank': 'A'},
    
    'bread_fresh': {'name': '🍞 Горячий хлеб', 'desc': '+80 HP', 'price': 50, 'type': 'food', 'effect': 80, 'cat': 'food', 'rank': 'E'},
    'carrot_soup': {'name': '🥣 Морковный суп', 'desc': '+120 HP', 'price': 100, 'type': 'food', 'effect': 120, 'cat': 'food', 'rank': 'D'},
    'meat_pie': {'name': '🥧 Мясной пирог', 'desc': '+250 HP', 'price': 200, 'type': 'food', 'effect': 250, 'cat': 'food', 'rank': 'C'},
    'magic_stew': {'name': '🍲 Похлебка Героя', 'desc': '+600 HP, +200 MP', 'price': 800, 'type': 'food', 'effect': 600, 'cat': 'food', 'rank': 'A'},

 
}

DONATE_PACKAGES = {
    'pack_mini': {'name': '🪙 Горсть монет (500g)', 'gold': 500, 'price': 10},     # Базовый курс
    'pack1': {'name': '💰 Кошель золота (2,500g)', 'gold':2500, 'price': 50},        # Выгода +10%
    'pack2': {'name': '📦 Тяжелый сундук (10,000g)', 'gold': 10000, 'price': 150},    # Выгода +20%
    'pack3': {'name': '👑 Имперская казна (25,000g)', 'gold': 25000, 'price': 350}    # Выгода +40%
}

# --- РЕЦЕПТЫ АЛХИМИИ ---
ALCHEMY_RECIPES = {
    # === E RANG ===
    'pot_small_hp': {'result': 'pot_small_hp', 'cost': 10, 'mats': {'moss_lichen': 2, 'ruin_wormwood': 1}},
    'pot_small_mp': {'result': 'pot_small_mp', 'cost': 10, 'mats': {'firefly_shard': 3, 'dust_ages': 1}},
    'pot_small_str': {'result': 'pot_small_str', 'cost': 15, 'mats': {'stone_beetle': 2, 'ancient_shard': 1}},
    'pot_stone_skin': {'result': 'pot_stone_skin', 'cost': 15, 'mats': {'ancient_shard': 2, 'moss_lichen': 1}},
    'pot_agility': {'result': 'pot_agility', 'cost': 20, 'mats': {'stone_beetle': 1, 'dust_ages': 2}},
    'pot_poison_touch': {'result': 'pot_poison_touch', 'cost': 25, 'mats': {'stone_berry': 2, 'dust_ages': 1}},
    'pot_wind_speed': {'result': 'pot_wind_speed', 'cost': 20, 'mats': {'ruin_wormwood': 2, 'stone_beetle': 1}},

    # === D RANG ===
    'pot_medium_hp': {'result': 'pot_medium_hp', 'cost': 30, 'mats': {'life_root': 2, 'forest_fern': 1}},
    'pot_mana_rec': {'result': 'pot_mana_rec', 'cost': 30, 'mats': {'firefly_shard': 3, 'blueberry': 2}}, # firefly from E rank works too or define generic firefly
    'pot_forest_rage': {'result': 'pot_forest_rage', 'cost': 40, 'mats': {'leaf_beetle': 3, 'flint': 1}},
    'pot_flower_magic': {'result': 'pot_flower_magic', 'cost': 40, 'mats': {'violet': 2, 'firefly_shard': 2}},
    'pot_oak_skin': {'result': 'pot_oak_skin', 'cost': 45, 'mats': {'river_pebble': 3, 'life_root': 1}},
    'pot_evasion': {'result': 'pot_evasion', 'cost': 45, 'mats': {'woodlice': 3, 'forest_fern': 2}},
    'pot_fire_cloak': {'result': 'pot_fire_cloak', 'cost': 50, 'mats': {'flint': 2, 'forest_raspberry': 3}},

    # === C RANG ===
    'pot_elixir_life': {'result': 'pot_elixir_life', 'cost': 60, 'mats': {'mycelium': 3, 'grave_moss': 2}},
    'pot_necro': {'result': 'pot_necro', 'cost': 60, 'mats': {'glowing_larva': 3, 'bone_crumbs': 2}},
    'pot_bone_str': {'result': 'pot_bone_str', 'cost': 70, 'mats': {'bone_beetle': 3, 'sarcophagus_shard': 2}},
    'pot_ghost_pow': {'result': 'pot_ghost_pow', 'cost': 70, 'mats': {'ghost_orchid': 1, 'glowing_larva': 3}},
    'pot_dead_armor': {'result': 'pot_dead_armor', 'cost': 80, 'mats': {'limestone': 3, 'bone_crumbs': 2}},
    'pot_corpse_agi': {'result': 'pot_corpse_agi', 'cost': 80, 'mats': {'cave_cricket': 3, 'corpse_root': 2}},
    'item_ice_spike': {'result': 'item_ice_spike', 'cost': 90, 'mats': {'limestone': 3, 'ghost_orchid': 1}},

    # === B RANG ===
    'pot_knight_hp': {'result': 'pot_knight_hp', 'cost': 100, 'mats': {'royal_thyme': 3, 'castle_ivy': 2, 'knight_cherry': 1}},
    'pot_lord_mp': {'result': 'pot_lord_mp', 'cost': 100, 'mats': {'velvet_beetle': 3, 'precious_shard': 2}},
    'pot_steel_pow': {'result': 'pot_steel_pow', 'cost': 120, 'mats': {'rusty_iron': 3, 'velvet_beetle': 2}},
    'pot_duke_mag': {'result': 'pot_duke_mag', 'cost': 120, 'mats': {'duke_lily': 2, 'precious_shard': 2}},
    'pot_bastion': {'result': 'pot_bastion', 'cost': 130, 'mats': {'marble_chips': 3, 'rusty_iron': 2}},
    'pot_ghost_evasion': {'result': 'pot_ghost_evasion', 'cost': 130, 'mats': {'moth': 3, 'rosehip': 2}},
    'pot_crit': {'result': 'pot_crit', 'cost': 150, 'mats': {'precious_shard': 3, 'duke_lily': 1}},

    # === A RANG ===
    'pot_demon_blood': {'result': 'pot_demon_blood', 'cost': 200, 'mats': {'hell_nettle': 3, 'devil_claw': 2, 'blood_berry': 1}},
    'pot_void_nrg': {'result': 'pot_void_nrg', 'cost': 200, 'mats': {'fire_fly': 3, 'sinner_ash': 2}},
    'pot_hell_fury': {'result': 'pot_hell_fury', 'cost': 250, 'mats': {'obsidian': 3, 'demon_roach': 2}},
    'pot_mind_flame': {'result': 'pot_mind_flame', 'cost': 250, 'mats': {'hell_lily': 2, 'fire_fly': 3}},
    'pot_lava_armor': {'result': 'pot_lava_armor', 'cost': 280, 'mats': {'lava_stone': 3, 'obsidian': 2}},
    'pot_devil_agi': {'result': 'pot_devil_agi', 'cost': 280, 'mats': {'demon_roach': 3, 'hell_nettle': 2}},
    'pot_fire_aura': {'result': 'pot_fire_aura', 'cost': 300, 'mats': {'lava_stone': 3, 'fire_rose': 2}},

    # === S RANG ===
    'pot_god_heal': {'result': 'pot_god_heal', 'cost': 500, 'mats': {'chaos_grass': 3, 'star_moss': 2, 'cosmic_berry': 1}},
    'pot_inf_mana': {'result': 'pot_inf_mana', 'cost': 500, 'mats': {'crystal_dragonfly': 3, 'aether_crystal': 2}},
    'pot_chaos_pow': {'result': 'pot_chaos_pow', 'cost': 600, 'mats': {'chaos_shard': 3, 'phantom_beetle': 2}},
    'pot_void_mag': {'result': 'pot_void_mag', 'cost': 600, 'mats': {'void_flower': 2, 'crystal_dragonfly': 3}},
    'pot_chaos_def': {'result': 'pot_chaos_def', 'cost': 700, 'mats': {'primordial_matter': 3, 'chaos_shard': 2}},
    'pot_inv_step': {'result': 'pot_inv_step', 'cost': 700, 'mats': {'phantom_beetle': 3, 'chaos_grass': 2}},
    'pot_deadly_psn': {'result': 'pot_deadly_psn', 'cost': 800, 'mats': {'void_berry': 3, 'star_moss': 2}},
}
# --- РЕЦЕПТЫ КРАФТА ---
CRAFT_RECIPES = {
    # --- РАСХОДНИКИ ---
    'small_hp': {'result': 'small_hp', 'cost': 10, 'mats': {'slime_goo': 2, 'wolf_pelt': 1}},
    'medium_hp': {'result': 'medium_hp', 'cost': 30, 'mats': {'small_hp': 2, 'spider_silk': 1}},
    
    # --- ОРУЖИЕ (МЕЧИ И ТОПОРЫ) ---
    'rusty_sword': {'result': 'rusty_sword', 'cost': 60, 'mats': {'goblin_ear': 5, 'wolf_pelt': 2}},
    'iron_axe': {'result': 'iron_axe', 'cost': 150, 'mats': {'iron_ore': 5, 'wolf_pelt': 3}},
    'dark_blade': {'result': 'dark_blade', 'cost': 1000, 'mats': {'demon_horn': 1, 'bone_dust': 10, 'iron_ore': 20}},
    'god_killer': {'result': 'god_killer', 'cost': 5000, 'mats': {'void_crystal': 5, 'demon_horn': 20, 'dragon_mail': 1}},

    # --- МАГИЧЕСКОЕ ОРУЖИЕ (ПОСОХИ - ДОБАВЛЕНО) ---
    'wooden_staff': {'result': 'wooden_staff', 'cost': 60, 'mats': {'wolf_pelt': 3, 'slime_goo': 2}},
    'acolyte_wand': {'result': 'acolyte_wand', 'cost': 200, 'mats': {'spider_silk': 5, 'small_mp': 2}},
    'crystal_staff': {'result': 'crystal_staff', 'cost': 500, 'mats': {'iron_ore': 10, 'spider_silk': 10}},
    'void_scepter': {'result': 'void_scepter', 'cost': 1500, 'mats': {'demon_horn': 2, 'bone_dust': 10}},
    'archmage_staff': {'result': 'archmage_staff', 'cost': 4000, 'mats': {'demon_horn': 10, 'void_crystal': 1}},

    # --- ЛЕГКАЯ БРОНЯ (ЛОВКОСТЬ) ---
    'leather_vest': {'result': 'leather_vest', 'cost': 50, 'mats': {'wolf_pelt': 5}},
    'hunter_gear': {'result': 'hunter_gear', 'cost': 300, 'mats': {'wolf_pelt': 10, 'spider_silk': 5, 'goblin_ear': 5}},
    'shadow_cloak': {'result': 'shadow_cloak', 'cost': 1500, 'mats': {'spider_silk': 20, 'vampire_fang': 2, 'bone_dust': 10}},
    'shadow_robe': {'result': 'shadow_robe', 'cost': 1200, 'mats': {'spider_silk': 20, 'vampire_fang': 5, 'bone_dust': 15}},
    # --- ТЯЖЕЛАЯ БРОНЯ (ЗАЩИТА) ---
    'chainmail': {'result': 'chainmail', 'cost': 120, 'mats': {'iron_ore': 8, 'spider_silk': 4}},
    'plate_armor': {'result': 'plate_armor', 'cost': 400, 'mats': {'iron_ore': 20, 'bone_dust': 5}},
    'dragon_mail': {'result': 'dragon_mail', 'cost': 3000, 'mats': {'demon_horn': 5, 'iron_ore': 50, 'plate_armor': 1}},
    'void_robe': {'result': 'void_robe', 'cost': 2500, 'mats': {'void_crystal': 1, 'demon_horn': 5, 'shadow_robe': 1}},
    # --- МАГИЧЕСКАЯ БРОНЯ (МАНА) ---
    'apprentice_robe': {'result': 'apprentice_robe', 'cost': 80, 'mats': {'spider_silk': 5, 'slime_goo': 5}},
    'archmage_robe': {'result': 'archmage_robe', 'cost': 300, 'mats': {'spider_silk': 15, 'small_mp': 5}},
    'mithril_armor': {'result': 'mithril_armor', 'cost': 600, 'mats': {'iron_ore': 20, 'bone_dust': 20, 'spider_silk': 10}},
    'void_plate': {'result': 'void_plate', 'cost': 8000, 'mats': {'void_crystal': 3, 'demon_horn': 10, 'void_robe': 1}}
}
# --- НАСТРОЙКИ ФЕРМЫ ---
FARM_CONFIG = {
    'wheat': {'name': '🌾 Пшеница', 'time_minutes': 10, 'yield_min': 3, 'yield_max': 6, 'req_rank': 'E'},
    'carrot': {'name': '🥕 Морковь', 'time_minutes': 20, 'yield_min': 2, 'yield_max': 5, 'req_rank': 'D'},
    'potato': {'name': '🥔 Картофель', 'time_minutes': 40, 'yield_min': 2, 'yield_max': 4, 'req_rank': 'C'},
    'magic_bean': {'name': '🫘 Магические бобы', 'time_minutes': 120, 'yield_min': 1, 'yield_max': 3, 'req_rank': 'A'},
}

# --- РЕЦЕПТЫ КУХНИ (ПОВАР) ---
COOKING_RECIPES = {
    # Вставьте это к остальным рецептам кухни
    'fish_soup': {'result': 'fish_soup', 'cost': 30, 'mats': {'fish_blind': 2, 'potato': 1}},
    'bread_fresh': {'result': 'bread_fresh', 'cost': 15, 'mats': {'wheat': 3}},
    'carrot_soup': {'result': 'carrot_soup', 'cost': 30, 'mats': {'carrot': 2, 'wheat': 1}},
    # meat_stew - это лут с кабана (D ранг), делаем из него мощный пирог!
    'meat_pie': {'result': 'meat_pie', 'cost': 50, 'mats': {'meat_stew': 2, 'potato': 2, 'wheat': 1}},
    'magic_stew': {'result': 'magic_stew', 'cost': 150, 'mats': {'magic_bean': 2, 'meat_pie': 1, 'carrot': 3}},
}

# --- БЕСТИАРИЙ ---
BASE_ENEMIES = {
    # === РАНГ E (1-14 ур) ===
    'wolf': {
        'name': '🐺 Бешеный Волк',
        'base_health': 40, 'base_min_physical_damage': 5, 'base_max_physical_damage': 9, 
        'base_min_magic_damage': 0, 'base_max_magic_damage': 0,
        'base_exp': 25, 'base_gold': 15, 'rank': 'E',
        'description': 'Облезлый зверь с пеной у рта.', 'image': IMAGE_URLS['wolf'], 'difficulty': 'easy',
        'abilities': ['basic_attack'], 'damage_type': 'physical', 'dodge_chance': 0.08,
        'drops': ['wolf_pelt', 'apple']
    },
    'goblin': {
        'name': '👹 Гоблин-Мародер',
        'base_health': 50, 'base_min_physical_damage': 6, 'base_max_physical_damage': 11, 
        'base_min_magic_damage': 0, 'base_max_magic_damage': 0,
        'base_exp': 30, 'base_gold': 20, 'rank': 'E',
        'description': 'Мерзкое создание.', 'image': IMAGE_URLS['goblin'], 'difficulty': 'easy',
        'abilities': ['basic_attack', 'dirty_trick'], 'damage_type': 'physical', 'dodge_chance': 0.12,
        'drops': ['goblin_ear', 'bread']
    },
    'slime': {
        'name': '🟢 Ядовитая Слизь',
        'base_health': 60, 'base_min_physical_damage': 4, 'base_max_physical_damage': 8, 
        'base_min_magic_damage': 5, 'base_max_magic_damage': 10,
        'base_exp': 35, 'base_gold': 25, 'rank': 'E',
        'description': 'Бурлящая кислотная масса.', 'image': IMAGE_URLS['slime'], 'difficulty': 'medium',
        'abilities': ['basic_attack', 'toxic_growth'], 'damage_type': 'mixed', 'dodge_chance': 0.02,
        'drops': ['slime_goo', 'small_hp']
    },
    'drowned_corpse': {
        'name': '🧟‍♂️ Утопленник',
        'base_health': 70, 'base_min_physical_damage': 8, 'base_max_physical_damage': 15, 
        'base_min_magic_damage': 0, 'base_max_magic_damage': 0,
        'base_exp': 40, 'base_gold': 25, 'rank': 'E',
        'description': 'Он ждал на дне слишком долго...', 'image': IMAGE_URLS['drowned'], 'difficulty': 'medium',
        'abilities': ['basic_attack'], 'damage_type': 'physical', 'dodge_chance': 0.05,
        'drops': ['fish_blind', 'bone_dust']
    },
    'goblin_shaman': {
        'name': '🔥 Гоблин-Шаман',
        'base_health': 55, 'base_min_physical_damage': 2, 'base_max_physical_damage': 4, 
        'base_min_magic_damage': 6, 'base_max_magic_damage': 10,
        'base_exp': 22, 'base_gold': 18, 'rank': 'E',
        'description': 'Бормочет заклинания и кидает огненные шары.', 'image': IMAGE_URLS['goblin_shaman'], 'difficulty': 'medium',
        'abilities': ['basic_attack', 'ignite'], 'damage_type': 'magic', 'dodge_chance': 0.10,
        'drops': ['goblin_ear', 'small_mp']
    },
    'goblin_elite': {
        'name': '👹 Вожак Гоблинов',
        'base_health': 80, 'base_min_physical_damage': 10, 'base_max_physical_damage': 18, 
        'base_min_magic_damage': 0, 'base_max_magic_damage': 0,
        'base_exp': 35, 'base_gold': 25, 'rank': 'E',
        'description': 'Громила в украденных доспехах.', 'image': IMAGE_URLS['hot_goblin'], 'difficulty': 'mini_boss',
        'abilities': ['basic_attack', 'power_strike'], 'damage_type': 'physical', 'dodge_chance': 0.15,
        'drops': ['goblin_ear', 'iron_ore']
    },
    'training_master': {
        'name': '⚔️ Падший Рыцарь',
        'base_health': 150, 'base_min_physical_damage': 15, 'base_max_physical_damage': 25, 
        'base_min_magic_damage': 0, 'base_max_magic_damage': 0,
        'base_exp': 100, 'base_gold': 80, 'rank': 'E',
        'description': 'Безумный воин, охраняющий руины.', 'image': IMAGE_URLS['knight'], 'difficulty': 'boss',
        'abilities': ['basic_attack', 'whirlwind_strike'], 'damage_type': 'physical', 'dodge_chance': 0.20,
        'drops': ['iron_ore', 'medium_hp']
    },

    # === РАНГ D (15-24 ур) ===
    'forest_spider': {
        'name': '🕷️ Арахнид',
        'base_health': 150, 'base_min_physical_damage': 12, 'base_max_physical_damage': 20, 
        'base_min_magic_damage': 0, 'base_max_magic_damage': 0,
        'base_exp': 120, 'base_gold': 60, 'rank': 'D',
        'description': 'Восьмилапый кошмар.', 'image': IMAGE_URLS['forest_spider'], 'difficulty': 'medium',
        'abilities': ['basic_attack', 'web_shot'], 'damage_type': 'physical', 'dodge_chance': 0.15,
        'drops': ['spider_silk']
    },
    'ghost': {
        'name': '👻 Заблудшая Душа',
        'base_health': 100, 'base_min_physical_damage': 6, 'base_max_physical_damage': 12, 
        'base_min_magic_damage': 15, 'base_max_magic_damage': 25,
        'base_exp': 110, 'base_gold': 50, 'rank': 'D',
        'description': 'Призрак путника.', 'image': IMAGE_URLS['mage'], 'difficulty': 'medium',
        'abilities': ['basic_attack', 'fear'], 'damage_type': 'magic', 'dodge_chance': 0.25,
        'drops': ['small_mp']
    },
    'wild_boar': {
        'name': '🐗 Секач-Людоед',
        'base_health': 180, 'base_min_physical_damage': 18, 'base_max_physical_damage': 28, 
        'base_min_magic_damage': 0, 'base_max_magic_damage': 0,
        'base_exp': 140, 'base_gold': 70, 'rank': 'D',
        'description': 'Массивная туша.', 'image': IMAGE_URLS['wild_boar'], 'difficulty': 'medium',
        'abilities': ['basic_attack', 'charge'], 'damage_type': 'physical', 'dodge_chance': 0.08,
        'drops': ['wolf_pelt', 'meat_stew']
    },
    'frost_spider': {
        'name': '❄️ Морозный Паук',
        'base_health': 160, 'base_min_physical_damage': 5, 'base_max_physical_damage': 10, 
        'base_min_magic_damage': 15, 'base_max_magic_damage': 25,
        'base_exp': 150, 'base_gold': 80, 'rank': 'D',
        'description': 'Его паутина холоднее льда.', 'image': IMAGE_URLS['frost_spider'], 'difficulty': 'hard',
        'abilities': ['basic_attack', 'freeze_bite'], 'damage_type': 'magic', 'dodge_chance': 0.15,
        'drops': ['spider_silk', 'small_mp'],
        'physical_resistance': 0.30, 'magic_resistance': -0.10
    },
    'forest_troll': {
        'name': '🌳 Болотный Тролль',
        'base_health': 250, 'base_min_physical_damage': 20, 'base_max_physical_damage': 35, 
        'base_min_magic_damage': 0, 'base_max_magic_damage': 0,
        'base_exp': 200, 'base_gold': 100, 'rank': 'D',
        'description': 'Тупая гора мышц.', 'image': IMAGE_URLS['forest_troll'], 'difficulty': 'mini_boss',
        'abilities': ['basic_attack', 'regeneration'], 'damage_type': 'physical', 'dodge_chance': 0.12,
        'drops': ['iron_ore', 'roast_boar']
    },
    'forest_guardian': {
        'name': '🌳 Проклятый Энт',
        'base_health': 400, 'base_min_physical_damage': 25, 'base_max_physical_damage': 40, 
        'base_min_magic_damage': 10, 'base_max_magic_damage': 20,
        'base_exp': 350, 'base_gold': 180, 'rank': 'D',
        'description': 'Древний страж леса.', 'image': IMAGE_URLS['forest_guardian'], 'difficulty': 'boss',
        'abilities': ['basic_attack', 'root_grab'], 'damage_type': 'mixed', 'dodge_chance': 0.08,
        'drops': ['medium_hp', 'apple']
    },

    # === РАНГ C (25-34 ур) ===
    'swamp_kraken': {
        'name': '🦑 Глубинный Ужас',
        'base_health': 400, 'base_min_physical_damage': 35, 'base_max_physical_damage': 55, 
        'base_min_magic_damage': 20, 'base_max_magic_damage': 30,
        'base_exp': 350, 'base_gold': 180, 'rank': 'C',
        'description': 'Тварь с десятком щупалец!', 'image': IMAGE_URLS['kraken'], 'difficulty': 'mini_boss',
        'abilities': ['basic_attack'], 'damage_type': 'mixed', 'dodge_chance': 0.10,
        'drops': ['fish_golden', 'large_hp']
    },
    'skeleton_warrior': {
        'name': '💀 Костяной Легионер',
        'base_health': 300, 'base_min_physical_damage': 30, 'base_max_physical_damage': 50, 
        'base_min_magic_damage': 0, 'base_max_magic_damage': 0,
        'base_exp': 300, 'base_gold': 150, 'rank': 'C',
        'description': 'Скелет в ржавых латах.', 'image': IMAGE_URLS['skeleton'], 'difficulty': 'hard',
        'abilities': ['basic_attack', 'shield_bash'], 'damage_type': 'physical', 'dodge_chance': 0.12,
        'drops': ['bone_dust']
    },
    'ghoul': {
        'name': '🧟 Трупоед',
        'base_health': 350, 'base_min_physical_damage': 25, 'base_max_physical_damage': 45, 
        'base_min_magic_damage': 0, 'base_max_magic_damage': 0,
        'base_exp': 320, 'base_gold': 160, 'rank': 'C',
        'description': 'Сгорбленная тварь.', 'image': IMAGE_URLS['zombie'], 'difficulty': 'hard',
        'abilities': ['basic_attack', 'life_drain'], 'damage_type': 'physical', 'dodge_chance': 0.10,
        'drops': ['bone_dust', 'meat_stew']
    },
    'dark_priest': {
        'name': '🕯️ Культист Смерти',
        'base_health': 250, 'base_min_physical_damage': 10, 'base_max_physical_damage': 20, 
        'base_min_magic_damage': 40, 'base_max_magic_damage': 60,
        'base_exp': 350, 'base_gold': 180, 'rank': 'C',
        'description': 'Безумец в балахоне.', 'image': IMAGE_URLS['mage'], 'difficulty': 'hard',
        'abilities': ['basic_attack', 'dark_bolt'], 'damage_type': 'magic', 'dodge_chance': 0.15,
        'drops': ['small_mp'] 
    },
    'crypt_keeper': {
        'name': '💀 Некромант',
        'base_health': 500, 'base_min_physical_damage': 40, 'base_max_physical_damage': 60, 
        'base_min_magic_damage': 20, 'base_max_magic_damage': 40,
        'base_exp': 500, 'base_gold': 250, 'rank': 'C',
        'description': 'Хозяин склепа.', 'image': IMAGE_URLS['lich'], 'difficulty': 'mini_boss',
        'abilities': ['basic_attack', 'raise_dead'], 'damage_type': 'mixed', 'dodge_chance': 0.18,
        'drops': ['bone_dust', 'medium_hp']
    },
    'catacomb_lord': {
        'name': '👑 Король Лич',
        'base_health': 800, 'base_min_physical_damage': 50, 'base_max_physical_damage': 80, 
        'base_min_magic_damage': 30, 'base_max_magic_damage': 50,
        'base_exp': 900, 'base_gold': 450, 'rank': 'C',
        'description': 'Древний правитель.', 'image': IMAGE_URLS['catacomb_lord'], 'difficulty': 'boss',
        'abilities': ['basic_attack', 'royal_decree'], 'damage_type': 'mixed', 'dodge_chance': 0.15,
        'drops': ['large_hp', 'bone_dust']
    },

    # === РАНГ B (35-44 ур) ===
    'dark_knight': {
        'name': '⚔️ Черный Страж',
        'base_health': 700, 'base_min_physical_damage': 60, 'base_max_physical_damage': 90, 
        'base_min_magic_damage': 0, 'base_max_magic_damage': 0,
        'base_exp': 800, 'base_gold': 400, 'rank': 'B',
        'description': 'Элитный воин.', 'image': IMAGE_URLS['dark_knight'], 'difficulty': 'very_hard',
        'abilities': ['basic_attack', 'shield_wall'], 'damage_type': 'physical', 'dodge_chance': 0.20,
        'drops': ['iron_ore', 'medium_hp']
    },
    'vampire': {
        'name': '🦇 Носферату',
        'base_health': 650, 'base_min_physical_damage': 70, 'base_max_physical_damage': 100, 
        'base_min_magic_damage': 0, 'base_max_magic_damage': 0,
        'base_exp': 850, 'base_gold': 420, 'rank': 'B',
        'description': 'Аристократ ночи.', 'image': IMAGE_URLS['vampire'], 'difficulty': 'very_hard',
        'abilities': ['basic_attack', 'blood_drain'], 'damage_type': 'physical', 'dodge_chance': 0.25,
        'drops': ['elven_wine', 'vampire_fang']
    },
    'gargoyle': {
        'name': '🗿 Ожившая Горгулья',
        'base_health': 900, 'base_min_physical_damage': 50, 'base_max_physical_damage': 80, 
        'base_min_magic_damage': 0, 'base_max_magic_damage': 0,
        'base_exp': 750, 'base_gold': 380, 'rank': 'B',
        'description': 'Каменная тварь.', 'image': IMAGE_URLS['gargoyle'], 'difficulty': 'very_hard',
        'abilities': ['basic_attack', 'stone_skin'], 'damage_type': 'physical', 'dodge_chance': 0.05,
        'drops': ['iron_ore']
    },
    'death_knight': {
        'name': '💀 Генерал Тьмы',
        'base_health': 1100, 'base_min_physical_damage': 80, 'base_max_physical_damage': 120, 
        'base_min_magic_damage': 40, 'base_max_magic_damage': 70,
        'base_exp': 1300, 'base_gold': 650, 'rank': 'B',
        'description': 'Командующий проклятым легионом.', 'image': IMAGE_URLS['death_knight'], 'difficulty': 'mini_boss',
        'abilities': ['basic_attack', 'death_coil'], 'damage_type': 'mixed', 'dodge_chance': 0.23,
        'drops': ['iron_ore', 'bone_dust']
    },
    'castle_overlord': {
        'name': '🏰 Безумный Император',
        'base_health': 1800, 'base_min_physical_damage': 100, 'base_max_physical_damage': 150, 
        'base_min_magic_damage': 60, 'base_max_magic_damage': 100,
        'base_exp': 2200, 'base_gold': 1100, 'rank': 'B',
        'description': 'Тиран, продавший королевство.', 'image': IMAGE_URLS['castle_overlord'], 'difficulty': 'boss',
        'abilities': ['basic_attack', 'royal_command'], 'damage_type': 'mixed', 'dodge_chance': 0.20,
        'drops': ['vampire_fang', 'large_hp']
    },

    # === РАНГ A (45-54 ур) ===
    'imp': {
        'name': '😈 Адский бес',
        'base_health': 1200, 'base_min_physical_damage': 110, 'base_max_physical_damage': 160, 
        'base_min_magic_damage': 80, 'base_max_magic_damage': 130,
        'base_exp': 2000, 'base_gold': 1000, 'rank': 'A',
        'description': 'Мелкий демон.', 'image': IMAGE_URLS['imp'], 'difficulty': 'extreme',
        'abilities': ['basic_attack', 'fireball'], 'damage_type': 'mixed', 'dodge_chance': 0.30,
        'drops': ['demon_horn']
    },
    'succubus': {
        'name': '💋 Суккуб',
        'base_health': 1000, 'base_min_physical_damage': 80, 'base_max_physical_damage': 120, 
        'base_min_magic_damage': 150, 'base_max_magic_damage': 200,
        'base_exp': 2200, 'base_gold': 1100, 'rank': 'A',
        'description': 'Прекрасная и смертоносная.', 'image': IMAGE_URLS['succubus'], 'difficulty': 'extreme',
        'abilities': ['basic_attack', 'charm'], 'damage_type': 'magic', 'dodge_chance': 0.35,
        'drops': ['large_mp']
    },
    'demon': {
        'name': '😈 Демон Разрушения',
        'base_health': 1600, 'base_min_physical_damage': 140, 'base_max_physical_damage': 200, 
        'base_min_magic_damage': 100, 'base_max_magic_damage': 160,
        'base_exp': 2800, 'base_gold': 1400, 'rank': 'A',
        'description': 'Воплощение ненависти.', 'image': IMAGE_URLS['demon'], 'difficulty': 'extreme',
        'abilities': ['basic_attack', 'hellfire'], 'damage_type': 'mixed', 'dodge_chance': 0.25,
        'drops': ['demon_horn']
    },
    'pit_fiend': {
        'name': '😈 Архидемон',
        'base_health': 2200, 'base_min_physical_damage': 160, 'base_max_physical_damage': 240, 
        'base_min_magic_damage': 120, 'base_max_magic_damage': 180,
        'base_exp': 3500, 'base_gold': 1800, 'rank': 'A',
        'description': 'Один из лордов преисподней.', 'image': IMAGE_URLS['pit_fiend'], 'difficulty': 'mini_boss',
        'abilities': ['basic_attack', 'summon_demons'], 'damage_type': 'mixed', 'dodge_chance': 0.28,
        'drops': ['demon_horn', 'large_hp']
    },
    'demon_general': {
        'name': '😈 Принц Ада',
        'base_health': 2500, 'base_min_physical_damage': 180, 'base_max_physical_damage': 260, 
        'base_min_magic_damage': 140, 'base_max_magic_damage': 220,
        'base_exp': 4500, 'base_gold': 2200, 'rank': 'A',
        'description': 'Правая рука Дьявола.', 'image': IMAGE_URLS['demon_general'], 'difficulty': 'boss',
        'abilities': ['basic_attack', 'apocalypse'], 'damage_type': 'mixed', 'dodge_chance': 0.25,
        'drops': ['demon_horn', 'void_crystal']
    },

    # === РАНГ S (55+ ур) ===
    'void_walker': {
        'name': '🌑 Странник Пустоты',
        'base_health': 2500, 'base_min_physical_damage': 200, 'base_max_physical_damage': 300, 
        'base_min_magic_damage': 200, 'base_max_magic_damage': 300,
        'base_exp': 5000, 'base_gold': 2500, 'rank': 'S',
        'description': 'Существо из антиматерии.', 'image': IMAGE_URLS['void_walker'], 'difficulty': 'legendary',
        'abilities': ['basic_attack', 'warp'], 'damage_type': 'mixed', 'dodge_chance': 0.40,
        'drops': ['void_crystal']
    },
    'dragon_ancient': {
        'name': '🐉 Дракон Хаоса',
        'base_health': 3500, 'base_min_physical_damage': 250, 'base_max_physical_damage': 380, 
        'base_min_magic_damage': 250, 'base_max_magic_damage': 380,
        'base_exp': 7000, 'base_gold': 3500, 'rank': 'S',
        'description': 'Существо, видевшее рождение звезд.', 'image': IMAGE_URLS['dragon_ancient'], 'difficulty': 'legendary',
        'abilities': ['basic_attack', 'dragon_breath'], 'damage_type': 'mixed', 'dodge_chance': 0.30,
        'drops': ['void_crystal', 'large_hp']
    },
    'final_god': {
        'name': '⚡ Падший Творец',
        'base_health': 6000, 'base_min_physical_damage': 350, 'base_max_physical_damage': 500, 
        'base_min_magic_damage': 350, 'base_max_magic_damage': 500,
        'base_exp': 15000, 'base_gold': 8000, 'rank': 'S',
        'description': 'Бог, решивший стереть этот мир.', 'image': IMAGE_URLS['fallen_god'], 'difficulty': 'boss',
        'abilities': ['basic_attack', 'divine_judgment', 'omnipotence'], 'damage_type': 'mixed', 'dodge_chance': 0.45,
        'drops': ['void_crystal', 'ambrosia']
    }
}
# --- ЛОКАЦИИ ---
# --- ЛОКАЦИИ ---
# --- ЛОКАЦИИ ---
LOCATIONS = {
    'E': {'name': '🏚️ Руины Деревни', 'description': 'Здесь лишь пепел и безумцы.', 'image': IMAGE_URLS['village'], 'min_level': 1, 'enemies': ['wolf', 'goblin', 'slime','goblin_shaman' ,'goblin_elite','training_master']},
    'D': {'name': '🌲 Шепчущий Лес', 'description': 'Тени здесь длиннее, чем кажется.', 'image': IMAGE_URLS['forest'], 'min_level': 15, 'enemies': ['forest_spider', 'ghost', 'wild_boar', 'frost_spider','forest_troll', 'forest_guardian']},
    'C': {'name': '☠️ Катакомбы Скорби', 'description': 'Подземелья, пропахшие гнилью.', 'image': IMAGE_URLS['dungeon'], 'min_level': 25, 'enemies': ['skeleton_warrior', 'ghoul', 'dark_priest', 'crypt_keeper', 'catacomb_lord']},
    'B': {'name': '🏰 Проклятая Цитадель', 'description': 'Обитель вампиров.', 'image': IMAGE_URLS['castle'], 'min_level': 35, 'enemies': ['dark_knight', 'vampire', 'gargoyle', 'death_knight', 'castle_overlord']},
    'A': {'name': '🔥 Врата Ада', 'description': 'Земля раскалена.', 'image': IMAGE_URLS['hell_gate'], 'min_level': 60, 'enemies': ['imp', 'demon', 'succubus', 'pit_fiend', 'demon_general']},
    'S': {'name': '🌌 Трон Хаоса', 'description': 'Пустота за пределами реальности.', 'image': IMAGE_URLS['throne_god'], 'min_level': 100, 'enemies': ['void_walker', 'dragon_ancient', 'final_god']}
}
# --- НАСТРОЙКИ ЭКСПЕДИЦИЙ (ТРАВНИК) ---
EXPEDITION_CONFIG = {
    'E': {
        'name': '🌿 Забытые руины (E)', 
        'time_minutes': 15, 
        'loot': ['moss_lichen', 'ruin_wormwood', 'stone_beetle', 'firefly_shard', 'ancient_shard', 'dust_ages', 'stone_berry', 'ruin_rose']
    },
    'D': {
        'name': '🌲 Тенистый лес (D)', 
        'time_minutes': 30, 
        'loot': ['forest_fern', 'life_root', 'hypericum', 'forest_raspberry', 'blueberry', 'wolf_berry', 'leaf_beetle', 'woodlice', 'river_pebble', 'flint', 'violet']
    },
    'C': {
        'name': '☠️ Мрачные катакомбы (C)', 
        'time_minutes': 60, 
        'loot': ['mycelium', 'grave_moss', 'corpse_root', 'cave_cricket', 'bone_beetle', 'glowing_larva', 'bone_crumbs', 'limestone', 'sarcophagus_shard', 'ghost_orchid', 'bone_berry']
    },
    'B': {
        'name': '🏰 Старый замок (B)', 
        'time_minutes': 90, 
        'loot': ['royal_thyme', 'castle_ivy', 'knight_cherry', 'baron_currant', 'velvet_beetle', 'moth', 'duke_lily', 'rosehip', 'marble_chips', 'rusty_iron', 'precious_shard']
    },
    'A': {
        'name': '🔥 Пекло (A)', 
        'time_minutes': 120, 
        'loot': ['hell_nettle', 'devil_claw', 'flame_berry', 'blood_berry', 'fire_fly', 'demon_roach', 'lava_stone', 'sinner_ash', 'obsidian', 'fire_rose', 'hell_lily']
    },
    'S': {
        'name': '⚡ Искажённые земли (S)', 
        'time_minutes': 180, 
        'loot': ['chaos_grass', 'star_moss', 'cosmic_berry', 'void_berry', 'crystal_dragonfly', 'phantom_beetle', 'chaos_shard', 'aether_crystal', 'primordial_matter', 'void_flower', 'chaos_nectarine']
    }
}
# --- ФУНКЦИИ ---
async def herbalist_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    # 1. Проверяем, построена ли хижина
    if not database.check_building(user_id, 'building_alchemy'):
        await query.answer("Сначала постройте Лавку Травника! (/alchemy)", show_alert=True)
        return

    # 2. Получаем статус экспедиции
    status = database.get_expedition_status(user_id)
    
    if status['state'] == 'idle':
        # --- ТРАВНИК СВОБОДЕН ---
        txt = "🌿 **Травник свободен**\nКуда отправим его на поиски ингредиентов?"
        kb = []
        char = database.get_character(user_id)
        ranks = ['E', 'D', 'C', 'B', 'A', 'S']
        
        for rank_key, conf in EXPEDITION_CONFIG.items():
            # Проверка ранга игрока (нельзя отправить в C, если ты E)
            if ranks.index(char['rank']) >= ranks.index(rank_key):
                kb.append([InlineKeyboardButton(f"{conf['name']} ({conf['time_minutes']} мин)", callback_data=f"send_exp_{rank_key}")])
            else:
                kb.append([InlineKeyboardButton(f"🔒 {conf['name']} (Нужен ранг {rank_key})", callback_data="ignore")])
        
        kb.append([InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')])
        await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['village'], caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))
        
    else:
        # --- ТРАВНИК В ПУТИ ---
        start_time = status['start_time']
        if isinstance(start_time, str): # Конвертация, если база вернула строку
            start_time = datetime.fromisoformat(start_time)
            
        duration = EXPEDITION_CONFIG[status['location']]['time_minutes']
        elapsed = datetime.now() - start_time
        elapsed_minutes = elapsed.total_seconds() / 60
        
        if elapsed_minutes >= duration:
            # === ОН ВЕРНУЛСЯ! ===
            txt = "✅ **Травник вернулся!**\nЕго сумка полна ресурсов."
            kb = [[InlineKeyboardButton("🎒 ЗАБРАТЬ ЛУТ", callback_data='claim_exp_loot')]]
            await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['shop'], caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))
        else:
            # === ЕЩЕ В ПУТИ ===
            left = int(duration - elapsed_minutes)
            txt = f"⏳ **Травник в пути...**\nЛокация: {EXPEDITION_CONFIG[status['location']]['name']}\nВернется через: {left} мин."
            kb = [[InlineKeyboardButton("🔄 Обновить статус", callback_data='herbalist_menu')],
                  [InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]]
            await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['forest'], caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))

    return MAIN_MENU

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    char = database.get_character(user.id)
    
    
    # --- НОВАЯ НИЖНЯЯ КЛАВИАТУРА БЫСТРОГО ДОСТУПА ---
    quick_kb = ReplyKeyboardMarkup([['/start', '/slums'], ['/alchemy', '/reset']], resize_keyboard=True, is_persistent=True)
    
    # Отправляем техническое сообщение, чтобы закрепить нижние кнопки
    if update.message:
        await update.message.reply_text("⚔️ Вход в мир Темного Фентези...", reply_markup=quick_kb)
    
    if char:
        txt = (
            f"С возвращением, {char['character_name']}!\n"
            f"Темные времена настали, надеюсь ты готов к новым испытаниям.\n\n"
            f"🔔 *Следи за обновлениями в канале:*\n"
            f"👉 [Путь героя | Dark Fantasy](https://t.me/hero_spath)"
        )
        
        # Если update.message существует, отвечаем на него, иначе шлем в чат напрямую
        if update.message:
            await update.message.reply_photo(
                IMAGE_URLS['village'], 
                caption=txt, 
                parse_mode='Markdown', 
                reply_markup=get_main_menu_keyboard(user.id)
            )
        else:
            await context.bot.send_photo(
                chat_id=user.id,
                photo=IMAGE_URLS['village'], 
                caption=txt, 
                parse_mode='Markdown', 
                reply_markup=get_main_menu_keyboard(user.id)
            )
        return MAIN_MENU
    else:
        if update.message:
            await update.message.reply_text("Мир погрузился во тьму. Выберите, кем вы родились в этот проклятый век:", reply_markup=get_race_selection_keyboard())
        else:
            await context.bot.send_message(chat_id=user.id, text="Мир погрузился во тьму. Выберите, кем вы родились в этот проклятый век:", reply_markup=get_race_selection_keyboard())
        return CHOOSE_RACE
        
async def start_expedition_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    try:
        # Разбираем callback_data, например send_exp_E
        rank = query.data.split('_')[2]
        
        # Проверка валидности ранга
        if rank not in EXPEDITION_CONFIG:
            await query.answer(f"❌ Ошибка: неверный ранг {rank}", show_alert=True)
            return
        
        # Запускаем экспедицию
        database.start_expedition(user_id, rank)
        
        await query.answer(f"✅ Травник ушел в {EXPEDITION_CONFIG[rank]['name']}!")
        await herbalist_menu_handler(update, context)
        
    except Exception as e:
        logger.error(f"Ошибка экспедиции для user {user_id}: {e}")
        await query.answer(f"❌ Ошибка: {str(e)}", show_alert=True)
        
async def claim_loot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    status = database.get_expedition_status(user_id)
    if status['state'] != 'busy': return
    
    loc_conf = EXPEDITION_CONFIG.get(status['location'])
    if not loc_conf: 
        database.finish_expedition(user_id) # Сброс ошибки
        return

    # ГЕНЕРАЦИЯ ЛУТА
    # Даем 3-5 предметов из списка
    loot_count = random.randint(3, 5)
    received = []
    
    for _ in range(loot_count):
        item_key = random.choice(loc_conf['loot'])
        item_data = ITEMS_DB.get(item_key)
        if item_data:
            # Выдаем предмет (цена 0, так как найден)
            database.buy_item(user_id, item_key, 'material', item_data['name'], 0, 0)
            received.append(item_data['name'])
    
    database.finish_expedition(user_id)
    
    loot_str = ", ".join(received)
    txt = f"🎒 **Вы получили:**\n{loot_str}\n\nТравник готов к новому походу."
    
    await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['village'], caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("🌿 К Травнику", callback_data='herbalist_menu')]]))

def reset_expedition(user_id):
    """Принудительно сбрасывает экспедицию пользователя"""
    conn = get_connection()
    if not conn: return False
    try:
        with conn.cursor() as c:
            c.execute("DELETE FROM expeditions WHERE user_id = %s", (user_id,))
            conn.commit()
            return True
    except Exception as e:
        print(f"Reset expedition error: {e}")
        return False
    finally:
        conn.close()
        
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
    """
    Создает экземпляр врага с характеристиками.
    Враги теперь ограничены своим рангом и не растут бесконечно.
    """
    if enemy_key not in BASE_ENEMIES:
        if 'wolf' in BASE_ENEMIES: 
            return create_enemy('wolf', player_level)
        return None
    
    base = BASE_ENEMIES[enemy_key].copy()
    enemy_rank = base.get('rank', 'E')
    

    # 1. КАПЫ УРОВНЕЙ ДЛЯ КАЖДОГО РАНГА
    rank_caps = {
        'E': (1, 14),   # Руины 
        'D': (15, 24),  # Лес
        'C': (25, 34),  # Катакомбы
        'B': (35, 59),  # Замок (расширен)
        'A': (60, 99),  # Пекло (расширен)
        'S': (100, 150) # Хаос (расширен до 150)
    }
    
    min_lvl, max_lvl = rank_caps.get(enemy_rank, (1, 14))
    
    # Уровень врага ограничивается капом его локации
    enemy_level = max(min_lvl, min(player_level, max_lvl))
    
    # 2. Расчет множителя от УРОВНЯ ВРАГА (а не игрока!)
    level_multiplier = 1.0 + (enemy_level - 1) * 0.15
    
    # Множитель сложности (Боссы)
    bonus = 1.0
    if base.get('difficulty') == 'mini_boss': bonus = 1.8
    elif base.get('difficulty') == 'boss': bonus = 2.5
    
    final_multiplier = level_multiplier * bonus
    

    # 3. НАСТРОЙКА БАЛАНСА (Глобальное ослабление на 5%)
    balance_nerf = 0.90  # Было 1.0, теперь базовый урон/хп -5% для высоких рангов
    if enemy_rank in ['E', 'D']: balance_nerf = 0.80 # Было 0.90 (стало -15%)
    elif enemy_rank == 'C': balance_nerf = 0.85 # Было 0.95 (стало -10%)

    # Создание объекта врага
    enemy = base.copy()
    
    # Применяем множители
    enemy['health'] = int(base['base_health'] * final_multiplier * balance_nerf)
    enemy['max_health'] = enemy['health']
    
    enemy['min_physical_damage'] = int(base['base_min_physical_damage'] * level_multiplier * balance_nerf)
    enemy['max_physical_damage'] = int(base['base_max_physical_damage'] * level_multiplier * balance_nerf)
    
    enemy['min_magic_damage'] = int(base['base_min_magic_damage'] * level_multiplier * balance_nerf)
    enemy['max_magic_damage'] = int(base['base_max_magic_damage'] * level_multiplier * balance_nerf)
    
    # 4. НАГРАДА И ШТРАФ ЗА УРОВЕНЬ
    base_exp = int(base['base_exp'] * final_multiplier)
    base_gold = int(base['base_gold'] * final_multiplier)
    
    # Если игрок намного сильнее врага, режем награду (Анти-фарм)
    level_diff = player_level - enemy_level
    reward_penalty = 1.0
    if level_diff > 5:
        # За каждый уровень выше пятого отнимаем 10% награды, но оставляем минимум 10%
        reward_penalty = max(0.1, 1.0 - (level_diff * 0.1))
        
    enemy['exp'] = int(base_exp * reward_penalty)
    enemy['gold'] = int(base_gold * reward_penalty)
    
    # Флаги боссов
    if enemy.get('difficulty') == 'boss': 
        enemy['is_boss'] = True
    elif enemy.get('difficulty') == 'mini_boss': 
        enemy['is_mini_boss'] = True
        
    return enemy

def get_rank_icon(rank): return {'E': '🆕', 'D': '🟢', 'C': '🔵', 'B': '🟣', 'A': '🟠', 'S': '⚡'}.get(rank, '🆕')
def get_xp_bar(level, exp, length=10):
    needed = (level * (level + 1) * 50) // 2
    prev_needed = ((level - 1) * level * 50) // 2
    
    current_level_exp = exp - prev_needed
    level_diff = needed - prev_needed
    
    # Защита: если уровень уже взят, показываем полную полоску
    if current_level_exp >= level_diff:
        return "█" * length + f" {exp}/{needed} 🌟"
        
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

def calculate_player_dodge_chance(agility, race='human'):
    base_cap = 0.25
    if race == 'elf': base_cap = 0.40 # Эльфы могут увернуться в 40% случаев
    return min(0.03 + (agility * 0.003), base_cap)
def calculate_crit_chance(agility): return min(0.03 + (agility * 0.002), 0.15)

def calculate_damage(character, enemy, damage_type='physical', buffs=None):
    if buffs is None: buffs = {}

   # 1. Базовый стат + БАФФЫ
    if damage_type == 'physical':
        str_val = character['strength'] + buffs.get('strength', {}).get('val', 0)
        agi_val = character['agility'] + buffs.get('agility', {}).get('val', 0)
        
        # БАЛАНС: Механика "Фехтования". Если ловкость выше, бьем от нее (штраф 10%, т.к. она дает еще и уворот/крит)
        if agi_val > str_val:
            stat_val = int(agi_val * 0.9)
        else:
            stat_val = str_val
    else:
        stat_val = character['intelligence'] + buffs.get('intelligence', {}).get('val', 0)

    base_damage = max(1, stat_val // 2)
    
    # --- БОНУС ЭЛЬФОВ ---
    if character.get('race') == 'elf' and damage_type == 'magic':
        magic_type = character.get('elf_magic_type')
        if magic_type: 
            elf_bonus = (character['level'] // 3) * 3
            base_damage += elf_bonus
            
    # Сопротивление врага
    res = enemy.get('physical_resistance' if damage_type == 'physical' else 'magic_resistance', 0.0)
    
    # Разброс урона +- 20%
    damage = random.randint(int(base_damage*0.8), int(base_damage*1.2))
    damage = max(1, int(damage * (1 - res)))
    
    # Крит (учитываем бафф ловкости для шанса крита)
    total_agi = character.get('agility', 8) + buffs.get('agility', {}).get('val', 0)
    is_crit = random.random() < calculate_crit_chance(total_agi)
    
    if is_crit: damage = int(damage * 1.5)
    
    return damage, is_crit
    
def calculate_enemy_damage(enemy, character, buffs=None):
    if buffs is None: buffs = {}

    # Выбор типа атаки врага
    if enemy['damage_type'] == 'physical': 
        min_d, max_d, res = enemy['min_physical_damage'], enemy['max_physical_damage'], character.get('physical_resistance', 0.0)
    elif enemy['damage_type'] == 'magic': 
        min_d, max_d, res = enemy['min_magic_damage'], enemy['max_magic_damage'], character.get('magic_resistance', 0.0)
    else:
        if random.random() < 0.5: 
            min_d, max_d, res = enemy['min_physical_damage'], enemy['max_physical_damage'], character.get('physical_resistance', 0.0)
        else: 
            min_d, max_d, res = enemy['min_magic_damage'], enemy['max_magic_damage'], character.get('magic_resistance', 0.0)
    
    # Расчет урона
    damage = random.randint(min_d, max_d)
    damage = int(damage * (1 - float(res)) * 0.85)

    # --- УЧЕТ БАФФА БРОНИ (Снижает урон на фиксированное значение) ---
    armor_buff = buffs.get('armor', {}).get('val', 0)
    damage = max(1, damage - armor_buff)

    # --- УЧЕТ БАФФА ЛОВКОСТИ (Для уворота) ---
    total_agi = character.get('agility', 8) + buffs.get('agility', {}).get('val', 0)
    is_dodged = random.random() < calculate_player_dodge_chance(total_agi)
    
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
        
        # --- ПЕРЕВОД СПОСОБНОСТЕЙ (И ЗАЩИТА ОТ КРАШЕЙ МАРКДАУНА) ---
        ability_names = {
            'basic_attack': 'Мощный выпад',
            'dirty_trick': 'Грязный трюк',
            'toxic_growth': 'Токсичный взрыв',
            'ignite': 'Воспламенение',
            'power_strike': 'Тяжелый удар',
            'whirlwind_strike': 'Вихрь клинков',
            'web_shot': 'Выстрел паутиной',
            'fear': 'Леденящий ужас',
            'charge': 'Яростный рывок',
            'freeze_bite': 'Ледяной укус',
            'regeneration': 'Регенерация',
            'root_grab': 'Хватка корней',
            'shield_bash': 'Удар щитом',
            'life_drain': 'Похищение жизни',
            'dark_bolt': 'Стрела тьмы',
            'raise_dead': 'Призыв мертвых',
            'royal_decree': 'Королевский указ',
            'shield_wall': 'Глухая оборона',
            'blood_drain': 'Иссушение крови',
            'stone_skin': 'Каменная кожа',
            'death_coil': 'Лик смерти',
            'royal_command': 'Приказ императора',
            'fireball': 'Огненный шар',
            'charm': 'Дьявольское очарование',
            'hellfire': 'Адское пламя',
            'summon_demons': 'Призыв демонов',
            'apocalypse': 'Апокалипсис',
            'warp': 'Искажение реальности',
            'dragon_breath': 'Дыхание дракона',
            'divine_judgment': 'Божественный суд',
            'omnipotence': 'Всемогущество'
        }
        # Если навыка нет в словаре, просто убираем "_" и пишем с заглавной
        ability_ru = ability_names.get(ability, ability.replace('_', ' ').title())

        if ability == 'poison_spit':
            dmg = random.randint(5, 10)
            effect = f"Яд нанес {dmg} урона!"
            status = 'poisoned'
        else:
             effect = f"⚠️ {enemy['name']} использует: *{ability_ru}*!"
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
        [InlineKeyboardButton("📜 Гильдия", callback_data='guild_menu'),
         InlineKeyboardButton("💎 Банк (Донат)", callback_data='donate_menu')], 
        
        [
            InlineKeyboardButton("🏆 Топ героев", callback_data='top_players'),
            InlineKeyboardButton("🛡 Топ кланов", callback_data='top_clans')
        ],
        [InlineKeyboardButton("📢 Новости и Обновления", url='https://t.me/hero_spath')],
        # Где-то в списке кнопок:
        [
            InlineKeyboardButton("🌿 Травник", callback_data='herbalist_menu'),
            InlineKeyboardButton("🌾 Фермер", callback_data='farm_menu'),
        ],
        [
            InlineKeyboardButton("🍳 Кухня", callback_data='kitchen_menu'),
            InlineKeyboardButton("🎣 Рыбалка", callback_data='fishing_menu') # НОВАЯ КНОПКА
        ],
        
        # ---------------------------
        [InlineKeyboardButton("📜 Помощь", callback_data='help'), InlineKeyboardButton("🔄 Обновить", callback_data='refresh')
        ],
        [InlineKeyboardButton("🏰 Кланы", callback_data='clans_menu')]
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
        # --- НОВАЯ КНОПКА ---
        [InlineKeyboardButton("💰 ПРОДАТЬ ВЕЩИ 💰", callback_data='shop_sell_menu')],
        # --------------------
        [InlineKeyboardButton("💍 Аксессуары", callback_data='shop_cat_acc')],
        [InlineKeyboardButton("🔙 Выход", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(kb)

def get_shop_items_keyboard(category, user_gold):
    kb = []
    # --- СПИСОК ЭКСКЛЮЗИВОВ ФЕРМЫ И КУХНИ ---
    farm_and_kitchen = ['wheat', 'carrot', 'potato', 'magic_bean', 'bread_fresh', 'carrot_soup', 'meat_pie', 'magic_stew']
    
    for k, v in ITEMS_DB.items():
        if v.get('cat') == category:
            
            # ФИЛЬТР: Не показываем фермерские продукты и блюда
            if k in farm_and_kitchen:
                continue
            
            # ФИЛЬТР: Не показываем алхимию в магазине
            if category == 'food':
                if v.get('type') == 'buff_potion': continue
                if k.startswith('pot_'): continue # Скрываем новые крафтовые зелья
            
            if v.get('is_test', False):
                continue
                
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

def get_battle_action_keyboard(session):
    """Новая клавиатура для системы Очков Действия (AP)"""
    ap = session['player_ap']
    queued = len(session['queued_actions'])
    char_lvl = session['char']['level'] # Достаем уровень героя из сессии
    
    kb = []
    
    # Кнопки действий (активны, только если хватает AP)
    row1 = []
    if ap >= 1:
        row1.append(InlineKeyboardButton("⚔️ Физ (-1 AP)", callback_data='q_phys'))
        row1.append(InlineKeyboardButton("🔮 Маг (-1 AP)", callback_data='q_mag'))
    else:
        row1.append(InlineKeyboardButton("❌ Нет AP", callback_data='ignore'))
        
    row2 = []
    if ap >= 1:
        row2.append(InlineKeyboardButton("🛡 Блок (-1 AP)", callback_data='q_block'))
    if ap >= 2:
        # Та самая механика удвоения: тратим 2 сейчас, получаем +4 в следующем раунде
        row2.append(InlineKeyboardButton("🧘 Концентрация (-2 AP)", callback_data='q_focus'))
        
    if row1: kb.append(row1)
    if row2: kb.append(row2)

    # --- ВОЗВРАЩАЕМ КНОПКУ СПОСОБНОСТЕЙ ---
    if char_lvl >= 10:
        kb.append([InlineKeyboardButton("💫 Способности (2 AP)", callback_data='abilities_menu')])
    # -------------------------------------

    # Кнопки управления очередью
    ctrl_row = []
    if queued > 0:
        ctrl_row.append(InlineKeyboardButton("↩️ Сбросить очередь", callback_data='q_reset'))
        ctrl_row.append(InlineKeyboardButton(f"🔥 ВЫПОЛНИТЬ ({queued} д.)", callback_data='q_execute'))
    
    if ctrl_row: kb.append(ctrl_row)

    # Дополнительные кнопки
    kb.append([
        InlineKeyboardButton("🏃 Сбежать", callback_data='flee'),
        InlineKeyboardButton("🎒 Предметы", callback_data='battle_items')
    ])
    
    return InlineKeyboardMarkup(kb)
    


def get_level_up_keyboard(char, points):
    kb = [
        [InlineKeyboardButton("Сила", callback_data='levelup_strength'), InlineKeyboardButton("Ловкость", callback_data='levelup_agility')],
        [InlineKeyboardButton("Интеллект", callback_data='levelup_intelligence'), InlineKeyboardButton("Живучесть", callback_data='levelup_vitality')],
        [InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(kb)

def get_race_selection_keyboard():
    # Создаем кнопки рас вручную прямо здесь, чтобы не зависеть от кэша database
    kb = [
        [InlineKeyboardButton("⚔️ Человек", callback_data="race_human")],
        [InlineKeyboardButton("🏹 Эльф", callback_data="race_elf")],
        [InlineKeyboardButton("🛡️ Дварф", callback_data="race_dwarf")],
        [InlineKeyboardButton("🪓 Орк", callback_data="race_orc")],
        [InlineKeyboardButton("🦇 Вампир", callback_data="race_vampire")], # <--- НАШ ВАМПИР!
        [InlineKeyboardButton("🦎 Ящеролюд", callback_data="race_lizardman")],
        [InlineKeyboardButton("🐸 Жаболюд", callback_data="race_frogman")],
        [InlineKeyboardButton("🍀 Лепрекон (+5% Золота)", callback_data="race_leprechaun")],
        [InlineKeyboardButton("💀 Нежить (Много ХП)", callback_data="race_undead")]
    ]
    return InlineKeyboardMarkup(kb)
# --- HANDLERS ---


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
    # 1. Снимаем "часики" загрузки сразу
    try:
        await query.answer()
    except:
        pass
        
    data = query.data
    user_id = query.from_user.id

    # --- [ВАЖНО] ИСПРАВЛЕНИЕ КНОПКИ "НАЗАД" ---
    # Этого не было в вашем коде. Это нужно, чтобы кнопка "Назад" 
    # в меню Магии Эльфов возвращала в Деревню.
    if data == 'back_to_main':
        await safe_edit(
            query, 
            text="В деревне", 
            media=InputMediaPhoto(IMAGE_URLS['village'], caption="В деревне", parse_mode='Markdown'), 
            keyboard=get_main_menu_keyboard(user_id)
        )
        return MAIN_MENU
    # ------------------------------------------

    # 2. ПЕРЕХОД В МАГИЮ ЭЛЬФОВ (Блок в начале, как и нужно)
    if data == 'elf_magic_menu' or data.startswith('school_') or data.startswith('set_spell_'):
        await elf_magic_menu_handler(update, context)
        return MAIN_MENU
    # 2.5 АЛХИМИЯ - КАТЕГОРИИ
    if data == 'alchemy_main':
        await show_alchemy_menu(query, user_id)
        return MAIN_MENU
        
    elif data.startswith('alch_cat_'):
        rank = data.split('_')[2]
        await render_alchemy_category(query, user_id, rank)
        return MAIN_MENU
    # 3. ПРОФИЛЬ ГЕРОЯ
    if data == 'profile':
        char = database.get_character(user_id)
        
        race_key = char['race']
        
        # Надежный перевод расы:
        race_names = {
            'human': 'Человек',
            'elf': 'Эльф',
            'dwarf': 'Дварф',
            'orc': 'Орк',
            'vampire': 'Вампир',
            'lizardman': 'Ящеролюд',
            'frogman': 'Жаболюд',
            'leprechaun': 'Лепрекон', # НОВОЕ
            'undead': 'Нежить'        # НОВОЕ
        }
        race_name = race_names.get(race_key, race_key.capitalize())

        # --- КРАСИВЫЙ РАСЧЕТ УРОНА (С УЧЕТОМ ФЕХТОВАНИЯ) ---
        eff_phys_stat = max(char['strength'], int(char['agility'] * 0.9))
        base_phys = max(1, eff_phys_stat // 2)
        min_phys = int(base_phys * 0.8)
        max_phys = int(base_phys * 1.2)
        if max_phys <= min_phys: max_phys = min_phys + 1

        base_mag = max(1, char['intelligence'] // 2)
        min_mag = int(base_mag * 0.8)
        max_mag = int(base_mag * 1.2)
        if max_mag <= min_mag: max_mag = min_mag + 1
        # -----------------------------

        dodge = int(calculate_player_dodge_chance(char['agility']) * 100)
        crit = int(calculate_crit_chance(char['agility']) * 100)
        
        # Достаем инфу о клане перед тем, как писать текст
        clan = database.get_clan_by_id(char.get('clan_id')) if char.get('clan_id') else None
        clan_tag = f" 🛡️ [{clan['name']}]" if clan else ""
        
        txt = (
            f"👤 *{char['character_name']}*{clan_tag}\n"
            f"📖 Раса: *{race_name}*\n"
            f"🎖 Уровень: *{char['level']}*\n"
            f"💰 Золото: *{char['gold']}g*\n"
            f"──────────────────\n"
            f"❤️ HP: {get_health_bar(char['health'], char['max_health'])}\n"
            f"🌀 MP: {get_mana_bar(char['mana'], char['max_mana'])}\n"
            f"📚 XP: {get_xp_bar(char['level'], char['experience'])}\n"
            f"──────────────────\n"
            f"⚔️ Урон: *{min_phys}-{max_phys}* (Физ) / *{min_mag}-{max_mag}* (Маг)\n"
            f"💨 Уворот: *{dodge}%* | 💥 Крит: *{crit}%*\n"
            f"🧱 Сила: {char['strength']} | 🤸 Ловк: {char['agility']}\n"
            f"🧠 Инт: {char['intelligence']} | 💓 Жив: {char['vitality']}"
        )
        
        if char['race'] == 'vampire':
            img = IMAGE_URLS.get('vampire_hero', IMAGE_URLS['human'])
        else:
            img = IMAGE_URLS.get(char['race'], IMAGE_URLS['human'])

        await safe_edit(query, text=txt, media=InputMediaPhoto(img, caption=txt, parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
        return MAIN_MENU
    # 4. ИНВЕНТАРЬ
    elif data == 'inventory':
        # Перенаправляем сразу в новый обработчик с категориями
        await inventory_menu_handler(update, context)
        return INVENTORY_MENU
        
    # 5. БИТВА
    elif data == 'battle_menu':
        char = database.get_character(user_id)
        if char['health'] <= 0:
             await query.answer("Вы мертвы! Воскресните в деревне.", show_alert=True)
             return MAIN_MENU
        await safe_edit(query, text="Куда лежит твой путь, путник?", media=InputMediaPhoto(IMAGE_URLS['forest'], caption="Куда лежит твой путь, путник?", parse_mode='Markdown'), keyboard=get_battle_menu_keyboard(char))
        return BATTLE_MENU
        
    # 6. МАГАЗИН
    elif data == 'shop':
        char = database.get_character(user_id)
        txt = f"🏪 *Мрачная лавка*\nТорговец смотрит на тебя из-под капюшона.\nЗолото: {char['gold']}💰"
        await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['shop'], caption=txt, parse_mode='Markdown'), keyboard=get_shop_categories_keyboard())
        return SHOP_MENU

    # 7. КРАФТ
    elif data == 'craft_menu':
        await craft_handler(update, context)
        return CRAFT_MENU
        
    # 8. ТОП ИГРОКОВ (С поддержкой страниц)
    elif data.startswith('top_players'):
        parts = data.split('_')
        # Если нажали просто "Топ" из главного меню, то частей 2 (top и players). Значит страница 1.
        # Если нажали "Вперед", то будет top_players_2, значит частей 3.
        page = 1
        if len(parts) > 2 and parts[2].isdigit():
            page = int(parts[2])
            
        await show_top_players(query, user_id, page)
        return MAIN_MENU
        
    # 8.1. ТОП КЛАНОВ
    elif data == 'top_clans':
        await show_top_clans(query, user_id)
        return MAIN_MENU
    # ------------------------------
    # 9. ОБНОВИТЬ (Исправил на возврат в деревню)
    elif data == 'refresh':
        await safe_edit(
            query, 
            text="В деревне", 
            media=InputMediaPhoto(IMAGE_URLS['village'], caption="В деревне", parse_mode='Markdown'), 
            keyboard=get_main_menu_keyboard(user_id)
        )
        
    # 10. ПРОКАЧКА
    elif data == 'level_up_menu':
        char = database.get_character(user_id)
        await query.edit_message_caption("Выберите характеристику для улучшения:", reply_markup=get_level_up_keyboard(char, char['stat_points']))
        return LEVEL_UP
        
    # 11. ГИЛЬДИЯ
    elif data == 'guild_menu':
        await guild_menu_handler(update, context)
        return GUILD_MENU
        
    # 12. ИНФО О РАНГАХ
    # 12. ИНФО О РАНГАХ
    elif data == 'rank_info':
        rank_info = """🏆 *РАНГИ*\n🆕 E: 1-14 ур (Руины)\n🟢 D: 15-24 ур (Лес)\n🔵 C: 25-34 ур (Катакомбы)\n🟣 B: 35-59 ур (Замок)\n🟠 A: 60-99 ур (Ад)\n⚡ S: 100-150 ур (Трон Хаоса)"""
        await query.edit_message_caption(rank_info, parse_mode='Markdown', reply_markup=get_main_menu_keyboard(user_id))
    # 13. ПОМОЩЬ
    elif data == 'help':
        await help_command(update, context)
        
    # (Дубликат elf_magic удален отсюда)

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
        
        # Генерируем описание местных тварей с учетом уровня игрока
        enemy_list_text = ""
        for e_key in loc['enemies']:
            if e_key in BASE_ENEMIES:
                e_data = create_enemy(e_key, char['level'])
                if not e_data: continue
                
                name = e_data['name']
                hp = e_data['max_health']
                
                # Считаем средний урон (берем середину между минимальным и максимальным)
                avg_phys = (e_data['min_physical_damage'] + e_data['max_physical_damage']) // 2
                avg_mag = (e_data['min_magic_damage'] + e_data['max_magic_damage']) // 2
                
                dmg_text = []
                if avg_phys > 0: dmg_text.append(f"{avg_phys} Физ")
                if avg_mag > 0: dmg_text.append(f"{avg_mag} Маг")
                dmg_str = " / ".join(dmg_text) if dmg_text else "0"
                
                # Выделяем Боссов и Элиту
                icon = "💀" if e_data.get('is_boss') else ("👹" if e_data.get('is_mini_boss') else "▫️")
                name_fmt = f"*{name}*" if e_data.get('is_boss') or e_data.get('is_mini_boss') else name
                tag = " [БОСС]" if e_data.get('is_boss') else (" [ЭЛИТА]" if e_data.get('is_mini_boss') else "")
                
                # Формируем красивую строчку
                enemy_list_text += f"{icon} {name_fmt}{tag}\n   └ ❤️ {hp} HP | ⚔️ Урон: ~{dmg_str}\n"

        txt = (
            f"🌲 *{loc['name']}*\n"
            f"_{loc['description']}_\n\n"
            f"🩸 *БЕСТИАРИЙ ЛОКАЦИИ (под ваш {char['level']} ур.):*\n"
            f"{enemy_list_text}\n"
            f"⚠️ _Оцени свои силы, {char['character_name']}..._"
        )
        
        # Обрезаем текст, если он вдруг превысит лимит
        if len(txt) > 1000: txt = txt[:1000] + "..."
        
        await safe_edit(query, text=txt, media=InputMediaPhoto(loc['image'], caption=txt, parse_mode='Markdown'), keyboard=get_location_enemies_keyboard(rank, char['level']))
        return BATTLE_MENU

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

        # --- БРОСОК КУБИКА ИНИЦИАТИВЫ (d16) ---
        p_roll = random.randint(1, 16)
        e_roll = random.randint(1, 16)
        
        log = [f"⚔️ *ВЫЗОВ БРОШЕН!*\n{enemy['description']}"]
        log.append(f"🎲 Инициатива (d16): Вы [{p_roll}] ⚡ Враг [{e_roll}]")

        # Инициализация сессии боя
        battle_sessions[user_id] = {
            'char': char, 
            'enemy': enemy, 
            'enemy_key': enemy_key,
            'log': log, 
            'turn': 1, 
            'status_effects': [], 
            'cooldowns': {}, 
            'last_image': None, 
            'processing': False,
            'slime_stacks': 0, 
            'burn_stacks': 0, 
            'frost_stacks': 0, 
            'active_buffs': {},
            'max_ap': 5,             
            'player_ap': 5,          
            'bonus_ap_next': 0,      
            'queued_actions': []     
        }
        
        s = battle_sessions[user_id]
        
        # Если враг выбросил больше, он нападает первым!
        if e_roll > p_roll:
            log.append(f"👹 {enemy['name']} оказался быстрее и атакует!")
            enemy_ap = 5
            total_enemy_dmg = 0
            enemy_ability_used = False
            
            while enemy_ap > 0:
                if enemy_ap >= 2 and not enemy_ability_used and random.random() < enemy.get('special_chance', 0.20):
                    spec_dmg, spec_desc, spec_status = process_enemy_special_attack(enemy, char, log) 
                    total_enemy_dmg += spec_dmg
                    enemy_ap -= 2
                    enemy_ability_used = True
                else:
                    base_dmg, is_dodged = calculate_enemy_damage(enemy, char)
                    if not is_dodged:
                        total_enemy_dmg += base_dmg
                    else:
                        log.append("💨 Вы увернулись от внезапной атаки!")
                    enemy_ap -= 1

            if total_enemy_dmg > 0:
                char['health'] -= total_enemy_dmg
                log.append(f"💔 Враг нанес *{total_enemy_dmg}* урона внезапной атакой.")

            # Проверка, не убил ли враг нас до начала нашего хода
            if char['health'] <= 0:
                database.update_character_stats(user_id, health=0, battle_losses=char.get('battle_losses',0)+1)
                del battle_sessions[user_id]
                death_msg = "💀 *ВЫ ПОГИБЛИ ДАЖЕ НЕ УСПЕВ ОБНАЖИТЬ МЕЧ...*"
                await safe_edit(query, text=death_msg, media=InputMediaPhoto(IMAGE_URLS.get('dungeon', ''), caption=death_msg, parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
                return MAIN_MENU
        else:
            log.append("⚡ Вы перехватили инициативу! Ваш ход.")

        await render_battle(query, user_id)
        return IN_BATTLE

    # ====== ТОТ САМЫЙ ПРОПАВШИЙ БЛОК НАЗАД ======
    elif data == 'back_to_battle_menu':
        char = database.get_character(user_id)
        txt = "Куда направимся, путник?"
        await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['forest'], caption=txt, parse_mode='Markdown'), keyboard=get_battle_menu_keyboard(char))
        
    return BATTLE_MENU

async def render_battle(query, user_id):
    s = battle_sessions.get(user_id)
    if not s: return 
    
    c, e = s['char'], s['enemy']
    log_str = "\n".join(s['log'][-8:]) # Оставляем 8 строк лога для бросков кубика
    
    player_hp = get_health_bar(c['health'], c['max_health'])
    enemy_hp = get_health_bar(e['health'], e['max_health'])
    enemy_icon = "💀" if e.get('is_boss') else "👺"
    
    # --- ВИЗУАЛИЗАЦИЯ ОЧЕРЕДИ AP ---
    ap_icons = "🟢" * s['player_ap'] + "⚪" * (s['max_ap'] + s.get('bonus_ap_next', 0) - s['player_ap'])
    
    # Красивый вывод очереди (ДОБАВЛЕНЫ ЗЕЛЬЯ И СКИЛЛЫ)
    q_visual = []
    for act in s['queued_actions']:
        if act == 'phys': q_visual.append("⚔️")
        elif act == 'mag': q_visual.append("🔮")
        elif act == 'block': q_visual.append("🛡")
        elif act == 'focus': q_visual.append("🧘")
        elif act.startswith('skill_'): q_visual.append("💫")
        elif act.startswith('item_'): q_visual.append("🧪")
    
    queue_str = " | ".join(q_visual) if q_visual else "_Пусто_"
    # -------------------------------

    txt = (
        f"{enemy_icon} *{e['name']}* `[Ранг {e.get('rank', '?')}]`\n"
        f"{enemy_hp}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 *{c['character_name']}* `[{c['level']} ур.]`\n"
        f"{player_hp} | 🌀 MP: {c['mana']}/{c['max_mana']}\n"
        f"⚡ AP: {ap_icons} ({s['player_ap']} шт.)\n"
        f"📜 Очередь: {queue_str}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{log_str}"
    )
    
    current_image = e['image']
    if s.get('last_image') == current_image:
        await safe_edit(query, text=txt, keyboard=get_battle_action_keyboard(s), media=None)
    else:
        s['last_image'] = current_image
        await safe_edit(query, text=None, media=InputMediaPhoto(current_image, caption=txt, parse_mode='Markdown'), keyboard=get_battle_action_keyboard(s))


async def battle_action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    s = battle_sessions.get(user_id)
    if not s: 
        await query.answer()
        await safe_edit(query, text="⌛ *Бой завершен или сессия истекла.*", keyboard=get_main_menu_keyboard(user_id))
        return MAIN_MENU

    if s.get('processing'):
        await query.answer("⏳ ...", show_alert=False)
        return IN_BATTLE
    
    action = query.data

    # ==========================================
    # === СИСТЕМА ОЧЕРЕДИ AP ===
    # ==========================================
    if action in ['q_phys', 'q_mag', 'q_block', 'q_focus']:
        cost = 2 if action == 'q_focus' else 1
        if s['player_ap'] >= cost:
            s['player_ap'] -= cost
            s['queued_actions'].append(action[2:]) 
            await render_battle(query, user_id)
        else:
            await query.answer("Не хватает AP!", show_alert=True)
        return IN_BATTLE

    elif action == 'q_reset':
        # Возвращаем потраченные AP и ману
        for act in s['queued_actions']:
            if act == 'focus':
                s['player_ap'] += 2
            elif act.startswith('skill_'):
                s['player_ap'] += 2
                sk_key = act.split('_')[1]
                for lvl, sk in RACE_ABILITIES.get(s['char']['race'], {}).items():
                    if sk['key'] == sk_key:
                        s['char']['mana'] += sk['mana']
                        s['cooldowns'][sk_key] = 0
            elif act.startswith('item_'):
                s['player_ap'] += 1 # Зелья стоят 1 AP
            else:
                s['player_ap'] += 1
                
        s['queued_actions'] = []
        await render_battle(query, user_id)
        return IN_BATTLE

    # --- 2. МЕНЮ ПРЕДМЕТОВ В БОЮ ---
    elif action == 'battle_items':
        items = database.get_inventory(user_id)
        kb = []
        found = False
        for i in items:
            it = ITEMS_DB.get(i['item_key'])
            if it and it.get('type') in ['potion', 'buff_potion']:
                 found = True
                 kb.append([InlineKeyboardButton(f"{it['name']} (x{i['quantity']}) [-1 AP]", callback_data=f"use_battle_{i['item_key']}")])
        
        if not found:
            await query.answer("У вас нет зелий!", show_alert=True)
            return IN_BATTLE

        kb.append([InlineKeyboardButton("🔙 Назад", callback_data='back_to_fight')])
        await safe_edit(query, keyboard=InlineKeyboardMarkup(kb))
        return IN_BATTLE

    # --- 3. ИСПОЛЬЗОВАНИЕ ПРЕДМЕТА (ТЕПЕРЬ ИДЕТ В ОЧЕРЕДЬ) ---
    elif action.startswith('use_battle_'):
        if s['player_ap'] < 1:
            await query.answer("⚡ Не хватает AP для использования зелья!", show_alert=True)
            return IN_BATTLE
            
        item_key = action.split('_', 2)[2]
        
        # Защита: проверяем, хватает ли предметов с учетом уже добавленных в очередь
        items = database.get_inventory(user_id)
        owned_qty = sum(i['quantity'] for i in items if i['item_key'] == item_key)
        queued_qty = sum(1 for act in s['queued_actions'] if act == f"item_{item_key}")
        
        if queued_qty >= owned_qty:
            await query.answer("У вас больше нет этого предмета!", show_alert=True)
            return IN_BATTLE

        # Добавляем в очередь
        s['player_ap'] -= 1
        s['queued_actions'].append(f"item_{item_key}")
        await render_battle(query, user_id) # Сразу возвращаем на экран боя с обновленной очередью
        return IN_BATTLE

    # --- 4. МЕНЮ СПОСОБНОСТЕЙ ---
    elif action == 'abilities_menu':
        char = s['char']
        race_skills = RACE_ABILITIES.get(char['race'], {})
        kb = []
        for lvl, skill in race_skills.items():
            if char['level'] >= lvl:
                cd_left = s['cooldowns'].get(skill['key'], 0)
                status_icon = "✅"
                if cd_left > 0: status_icon = f"⏳ {cd_left}"
                elif char['mana'] < skill['mana']: status_icon = "💧"
                
                btn_text = f"{skill['name']} ({skill['mana']} MP) {status_icon}"
                kb.append([InlineKeyboardButton(btn_text, callback_data=f"use_skill_{skill['key']}")])
        
        kb.append([InlineKeyboardButton("🔙 Назад в бой", callback_data='back_to_fight')])
        await safe_edit(query, text=None, keyboard=InlineKeyboardMarkup(kb))
        return IN_BATTLE

    elif action == 'back_to_fight':
        await render_battle(query, user_id)
        return IN_BATTLE

    elif action == 'flee':
        if s['enemy'].get('is_boss') or s['enemy'].get('is_mini_boss'):
            await query.answer("От босса не сбежать!", show_alert=True)
            return IN_BATTLE
        elif random.random() < 0.6:
            database.update_character_stats(user_id, health=s['char']['health'], mana=s['char']['mana'])
            del battle_sessions[user_id]
            txt = "🏃 *Вы сбежали!*"
            await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['village'], caption=txt, parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
            return MAIN_MENU
        else:
            s['log'].append("⛓ *ПОБЕГ НЕ УДАЛСЯ!* Враг атакует!")
            action = 'q_execute' 

    # === ИСПОЛЬЗОВАНИЕ СПОСОБНОСТИ ===
    elif action.startswith('use_skill_'):
        skill_key = action.split('_')[2]
        c, e, log = s['char'], s['enemy'], s['log']
        
        skill = None
        for lvl, sk in RACE_ABILITIES.get(c['race'], {}).items():
            if sk['key'] == skill_key: skill = sk
        
        if not skill: return IN_BATTLE
        
        if s['cooldowns'].get(skill_key, 0) > 0:
            await query.answer(f"⏳ Перезарядка! {s['cooldowns'][skill_key]} ход.", show_alert=True)
            return IN_BATTLE
            
        if c['mana'] < skill['mana']:
            await query.answer("💧 Не хватает маны!", show_alert=True)
            return IN_BATTLE

        if s['player_ap'] >= 2:
            s['player_ap'] -= 2
            c['mana'] -= skill['mana']
            s['cooldowns'][skill_key] = skill['cd']
            
            s['queued_actions'].append(f"skill_{skill_key}") 
            await render_battle(query, user_id)
        else:
            await query.answer("Не хватает AP! (Нужно 2)", show_alert=True)
        return IN_BATTLE


    # ==========================================
    # === РАСЧЕТ РАУНДА (EXECUTE) ===
    # ==========================================
    if action == 'q_execute':
        if not s['queued_actions']:
            await query.answer("Очередь пуста!", show_alert=True)
            return IN_BATTLE
            
        s['processing'] = True
        try:
            await query.answer("Скрестились клинки...")
            c, e, log = s['char'], s['enemy'], s['log']
            if 'active_buffs' not in s: s['active_buffs'] = {}
            
            log.append(f"\n--- Раунд {s['turn']} ---")

            # Обновление кулдаунов и баффов
            for k in list(s['cooldowns'].keys()):
                if s['cooldowns'][k] > 0: s['cooldowns'][k] -= 1
                
            expired_buffs = []
            for b_key, b_data in s['active_buffs'].items():
                b_data['dur'] -= 1
                if b_data['dur'] <= 0: expired_buffs.append(b_key)
            for exp in expired_buffs:
                del s['active_buffs'][exp]

            # 1. ОБРАБОТКА ДЕЙСТВИЙ ИГРОКА
            total_player_dmg = 0
            blocks_active = 0
            focus_used = 0
            
            # --- Механика Фехтования ---
            str_val = c['strength'] + s['active_buffs'].get('strength', {}).get('val', 0)
            agi_val = c['agility'] + s['active_buffs'].get('agility', {}).get('val', 0)
            eff_phys = int(agi_val * 0.9) if agi_val > str_val else str_val

            for act in s['queued_actions']:
                if act == 'phys':
                    dmg, is_crit = calculate_damage(c, e, 'physical', s['active_buffs'])
                    total_player_dmg += dmg
                    if 'poison_weapon' in s['active_buffs']:
                         val = s['active_buffs']['poison_weapon']['val']
                         e['health'] -= val
                         log.append(f"🧪 Яд нанес {val} урона!")
                         
                elif act == 'mag':
                    active_spell_key = c.get('elf_active_spell')
                    spell = None
                    if c['race'] == 'elf' and active_spell_key:
                        for school in ELF_SPELLS.values():
                            if active_spell_key in school['spells']:
                                spell = school['spells'][active_spell_key]; break
                    
                    mana_cost = spell['mana'] if spell else 10
                    if c['mana'] >= mana_cost:
                        c['mana'] -= mana_cost
                        if not spell:
                            dmg, is_crit = calculate_damage(c, e, 'magic', s['active_buffs'])
                            total_player_dmg += int(dmg * 1.2)
                        else:
                            base_mag = (c['intelligence'] + s['active_buffs'].get('intelligence', {}).get('val', 0)) // 2
                            dmg = int(base_mag * spell['val'])
                            total_player_dmg += dmg
                            if spell['type'] == 'drain': 
                                heal = int(dmg * 0.4)
                                c['health'] = min(c['max_health'], c['health'] + heal)
                    else:
                        log.append("💧 Магия сорвалась (нет маны)")
                        
                elif act == 'block':
                    blocks_active += 1
                elif act == 'focus':
                    focus_used += 1
                    
                # --- ОБРАБОТКА ВЫПИТЫХ ЗЕЛИЙ В РАУНДЕ ---
                elif act.startswith('item_'):
                    item_key = act.split('_', 1)[1]
                    it = ITEMS_DB.get(item_key)
                    if it:
                        # Физически удаляем зелье из БД только в момент исполнения!
                        database.remove_item(user_id, item_key, 1)
                        if it['type'] == 'potion':
                            eff = it['effect']
                            if 'hp' in item_key or 'health' in item_key:
                                c['health'] = min(c['max_health'], c['health'] + eff)
                                log.append(f"🧪 Выпито {it['name']} (+{eff} HP)")
                            elif 'mp' in item_key or 'mana' in item_key:
                                c['mana'] = min(c['max_mana'], c['mana'] + eff)
                                log.append(f"🧪 Выпито {it['name']} (+{eff} MP)")
                        elif it['type'] == 'buff_potion':
                            b_type = it['buff_type']
                            val = it['effect']
                            dur = it['duration']
                            s['active_buffs'][b_type] = {'val': val, 'dur': dur}
                            log.append(f"🧪 {it['name']} активировано!")

                elif act.startswith('skill_'):
                    sk_key = act.split('_')[1]
                    skill = None
                    for lvl, sk in RACE_ABILITIES.get(c['race'], {}).items():
                        if sk['key'] == sk_key: skill = sk
                    
                    if skill:
                        if skill['type'] == 'heal':
                            heal = int(c['max_health'] * skill['val'])
                            c['health'] = min(c['max_health'], c['health'] + heal)
                            log.append(f"✨ *{skill['name']}* +{heal} HP!")
                        elif skill['type'] == 'dmg':
                            total_player_dmg += int(eff_phys * skill['val'])
                        elif skill['type'] == 'dmg_agi':
                            total_player_dmg += int(agi_val * skill['val'])
                        elif skill['type'] == 'magic_nuke':
                            int_val = c['intelligence'] + s['active_buffs'].get('intelligence', {}).get('val', 0)
                            total_player_dmg += int(int_val * skill['val'])
                        elif skill['type'] == 'lifesteal':
                            pdmg = int(eff_phys * skill['val'])
                            heal = int(pdmg * 0.5)
                            total_player_dmg += pdmg
                            c['health'] = min(c['max_health'], c['health'] + heal)
                            log.append(f"🩸 *{skill['name']}* Лечение: {heal}!")
                        elif skill['type'] == 'buff_def':
                            blocks_active += 3
                            log.append(f"🛡 *{skill['name']}* активирован!")
                        elif skill['type'] == 'buff_str':
                            total_player_dmg += int(eff_phys * 2.0)
                        elif skill['type'] == 'stun_dmg':
                            total_player_dmg += int(eff_phys * skill['val'])
                            if random.random() < 0.5:
                                e['is_stunned'] = True
                                log.append(f"🔨 *{skill['name']}* ОГЛУШЕНИЕ!")
                        elif skill['type'] == 'dmg_exec':
                            base = eff_phys * skill['val']
                            if e['health'] < (e['max_health'] * 0.3): base *= 2
                            total_player_dmg += int(base)
                        elif skill['type'] == 'heal_mana':
                            heal = int(c['max_health'] * skill['val'])
                            c['health'] = min(c['max_health'], c['health'] + heal)
                            s['slime_stacks'] = 0
                            s['burn_stacks'] = 0
                            s['frost_stacks'] = 0
                            log.append(f"🍃 *{skill['name']}* +{heal} HP и очищение!")

            if total_player_dmg > 0:
                e['health'] -= total_player_dmg
                log.append(f"⚔️ Вы нанесли *{total_player_dmg}* урона!")

            # 2. ПРОВЕРКА ПОБЕДЫ
            if e['health'] <= 0:
                gold_win = int(e['gold'] * random.uniform(0.9, 1.2))
                # --- ПАССИВКА ЛЕПРЕКОНА ---
                if c['race'] == 'leprechaun':
                    gold_win = int(gold_win * 1.05)
                xp_win = e['exp']
                
                dropped_items = []
                if e.get('drops'):
                    for drop in e['drops']:
                        if random.random() < 0.4:
                            item_info = ITEMS_DB.get(drop)
                            if item_info:
                                database.buy_item(user_id, drop, 'material', item_info['name'], 0, 0)
                                dropped_items.append(item_info['name'])
                
                if c.get('quest_type') == 'kill' and c.get('quest_target') == s.get('enemy_key'):
                    if c.get('quest_progress') < c.get('quest_goal'):
                        database.update_quest_progress(user_id, 1)

                database.update_character_stats(user_id, health=c['health'], mana=c['mana'], battle_wins=c.get('battle_wins',0)+1)
                database.add_experience(user_id, xp_win)
                database.add_gold(user_id, gold_win)
                
                if e.get('is_boss'): database.increment_boss_kills(user_id, False)
                if e.get('is_mini_boss'): database.increment_boss_kills(user_id, True)
                
                log_str = "\n".join(s['log'][-7:])
                del battle_sessions[user_id]
                loot_txt = f"\n🎒 Лут: {', '.join(dropped_items)}" if dropped_items else ""
                win_msg = f"🏆 *ПОБЕДА!*\n☠️ {e['name']} повержен.\n💰 +{gold_win}g | 📚 +{xp_win}xp{loot_txt}\n\n📜 *Сводка:* \n{log_str}"
                await safe_edit(query, text=win_msg, media=InputMediaPhoto(IMAGE_URLS['village'], caption=win_msg, parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
                return MAIN_MENU

            # 3. ИСКУССТВЕННЫЙ ИНТЕЛЛЕКТ ВРАГА
            if s['enemy_key'] == 'slime':
                s['slime_stacks'] += 1
                pd = s['slime_stacks'] * 3
                heal = s['slime_stacks'] * 2
                e['health'] = min(e['max_health'], e['health'] + heal)
                c['health'] -= pd
                log.append(f"🤢 *ЯД!* -{pd} HP")

            elif s['enemy_key'] == 'goblin_shaman':
                s['burn_stacks'] = s.get('burn_stacks', 0) + 1
                fd = s['burn_stacks'] * 4
                c['health'] -= fd
                log.append(f"🔥 *ОЖОГ!* -{fd} HP")

            elif s['enemy_key'] == 'frost_spider':
                s['frost_stacks'] = s.get('frost_stacks', 0) + 1
                fr_dmg = s['frost_stacks'] * 5
                c['health'] -= fr_dmg
                log.append(f"❄️ *ХОЛОД!* -{fr_dmg} HP (Стак {s['frost_stacks']})")

            if e.get('is_stunned'):
                log.append("💫 Враг оглушен и пропускает ход!")
                e['is_stunned'] = False
            else:
                enemy_ap = 5
                total_enemy_dmg = 0
                enemy_ability_used = False

                while enemy_ap > 0:
                    if enemy_ap >= 2 and not enemy_ability_used and random.random() < e.get('special_chance', 0.20):
                        spec_dmg, spec_desc, spec_status = process_enemy_special_attack(e, c, log) 
                        total_enemy_dmg += spec_dmg
                        enemy_ap -= 2
                        enemy_ability_used = True
                    else:
                        base_dmg, is_dodged = calculate_enemy_damage(e, c, s['active_buffs'])
                        if not is_dodged:
                            total_enemy_dmg += base_dmg
                        else:
                            log.append("💨 Вы увернулись от атаки!")
                        enemy_ap -= 1

                if total_enemy_dmg > 0:
                    reduction = min(0.9, blocks_active * 0.3) 
                    final_enemy_dmg = int(total_enemy_dmg * (1.0 - reduction))
                    c['health'] -= final_enemy_dmg
                    
                    if blocks_active > 0:
                        log.append(f"🛡 Блок спас от {int(reduction*100)}% урона!")
                    log.append(f"💔 Враг нанес *{final_enemy_dmg}* урона.")

                    if 'fire_shield' in s['active_buffs']:
                        val = s['active_buffs']['fire_shield']['val']
                        e['health'] -= val
                        log.append(f"🔥 Огненный щит обжег врага на {val}!")

            # 4. ПРОВЕРКА ПОРАЖЕНИЯ
            if c['health'] <= 0:
                database.update_character_stats(user_id, health=0, battle_losses=c.get('battle_losses',0)+1)
                del battle_sessions[user_id]
                death_msg = "💀 *ВЫ ПОГИБЛИ...*"
                await safe_edit(query, text=death_msg, media=InputMediaPhoto(IMAGE_URLS.get('dungeon', ''), caption=death_msg, parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
                return MAIN_MENU

            # 5. СЛЕДУЮЩИЙ РАУНД
            s['player_ap'] = min(15, s['max_ap'] + (focus_used * 4)) 
            if focus_used > 0:
                log.append(f"🧘 Концентрация: Энергия кипит (AP: {s['player_ap']}/15).")

            s['queued_actions'] = [] 
            s['turn'] += 1
            await render_battle(query, user_id)

        finally:
            if user_id in battle_sessions:
                battle_sessions[user_id]['processing'] = False

    return IN_BATTLE
# ==========================================
# === СИСТЕМА КЛАНОВ ===
# ==========================================

async def clan_hub_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try: await query.answer()
    except: pass
    user_id = query.from_user.id
    char = database.get_character(user_id)
    
    clan_id = char.get('clan_id')
    if clan_id:
        # --- ИГРОК СОСТОИТ В КЛАНЕ ---
        clan = database.get_clan_by_id(clan_id)
        members = database.get_clan_members(clan_id)
        
        # Строим список участников
        mem_text = "\n".join([f"• {m['character_name']} ({m['level']} ур.)" for m in members[:15]])
        if len(members) > 15: mem_text += f"\n...и еще {len(members)-15} героев."
        
        role = "👑 Владыка" if clan['owner_id'] == user_id else "🛡 Участник"
        
        txt = (
            f"🏰 *КЛАН: [{clan['name']}]*\n"
            f"Ваша роль: {role}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👥 **Участники ({len(members)}):**\n"
            f"{mem_text}"
        )
        
        kb = [
            [InlineKeyboardButton("👹 КЛАНОВЫЙ РЕЙД", callback_data='clan_raid_hub')],
            [InlineKeyboardButton("🎁 Отправить подарок", callback_data='clan_gift_start')],
            [InlineKeyboardButton("🚪 Покинуть клан", callback_data='leave_clan')],
            [InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]
        ]
        
        # Выводим с гербом клана (иконкой), если она есть
        if clan['icon_id']:
            await safe_edit(query, text=None, media=InputMediaPhoto(clan['icon_id'], caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))
        else:
            await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['castle'], caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))
        return CLAN_MENU
        
    else:
        # --- ИГРОК БЕЗ КЛАНА ---
        txt = (
            "🏰 *ЗАЛ СЛАВЫ*\n"
            "Одиночкам не место в Бездне. Объединяйтесь с другими героями!\n\n"
            "• Вступить в клан: **с 10 уровня**\n"
            "• Создать свой клан: **Ранг D+ и 10,000g**"
        )
        kb = [
            [InlineKeyboardButton("📜 Список кланов", callback_data='list_clans')],
            [InlineKeyboardButton("👑 Создать клан (10,000g)", callback_data='create_clan_start')],
            [InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]
        ]
        await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['castle'], caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))
        return CLAN_MENU
async def clan_raid_hub_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try: await query.answer() # Снимаем часики загрузки!
    except: pass
    
    user_id = query.from_user.id
    char = database.get_character(user_id)
    
    clan_id = char.get('clan_id')
    if not clan_id: return MAIN_MENU
    
    clan = database.get_clan_by_id(clan_id)
    if not clan: return MAIN_MENU
    
    # --- БЕЗОПАСНОЕ ИЗВЛЕЧЕНИЕ ДАННЫХ (Защита от KeyError) ---
    raid_hp = clan.get('raid_hp', 0)
    raid_max_hp = clan.get('raid_max_hp', 0)
    raid_level = clan.get('raid_level', 1)
    raid_points = clan.get('raid_points', 0)
    
    kb = []
    if raid_hp > 0:
        # --- БОСС ЖИВ ---
        hp_bar = get_health_bar(raid_hp, raid_max_hp, 20)
        txt = (
            f"👹 *ОХОТА НА ТИТАНА* (Уровень {raid_level})\n\n"
            f"Огромное чудовище крушит земли вашего клана. Объедините силы, чтобы уничтожить его!\n\n"
            f"❤️ Здоровье Титана:\n{hp_bar}\n\n"
            f"_Награда за победу: +{raid_level * 10} Очков Клана_"
        )
        kb.append([InlineKeyboardButton("⚔️ АТАКОВАТЬ ТИТАНА", callback_data='raid_attack')])
    else:
        # --- БОСС МЕРТВ ИЛИ НЕ ПРИЗВАН ---
        txt = (
            f"🏆 *ТИТАН ПОВЕРЖЕН!*\n\n"
            f"Земли вашего клана в безопасности. Текущий уровень рейда: {raid_level}.\n"
            f"Слава клана: {raid_points} 🏆\n\n"
        )
        if clan['owner_id'] == user_id:
            txt += "_Вы как Владыка можете призвать нового, более сильного Титана._"
            kb.append([InlineKeyboardButton("🔮 Призвать Титана", callback_data='raid_summon')])
        else:
            txt += "_Ожидайте, пока Владыка призовет следующего Титана._"

    kb.append([InlineKeyboardButton("🔄 Обновить", callback_data='clan_raid_hub')])
    kb.append([InlineKeyboardButton("🔙 В клан", callback_data='back_to_clan_hub')])
    
    await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS.get('raid_boss', IMAGE_URLS['hell_gate']), caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))
    return CLAN_MENU

async def raid_summon_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    char = database.get_character(user_id)
    clan = database.get_clan_by_id(char.get('clan_id'))
    
    if not clan or clan['owner_id'] != user_id:
        await query.answer("Только Владыка может призывать Титанов!", show_alert=True)
        return CLAN_MENU
        
    if clan.get('raid_hp', 0) > 0:
        await query.answer("Титан уже призван!", show_alert=True)
        return CLAN_MENU

    # 🔥 СУРОВЫЙ БАЛАНС: 1 МИЛЛИОН HP за каждый уровень босса!
    raid_level = clan.get('raid_level', 1)
    max_hp = raid_level * 1000000 
    database.summon_raid_boss(clan['id'], max_hp)
    
    await query.answer("🔮 Титан восстал из Бездны! Созывайте клан!", show_alert=True)
    return await clan_raid_hub_handler(update, context)


async def raid_attack_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    char = database.get_character(user_id)
    clan = database.get_clan_by_id(char.get('clan_id'))
    
    if not clan or clan.get('raid_hp', 0) <= 0:
        await query.answer("Цель уже мертва!", show_alert=True)
        return await clan_raid_hub_handler(update, context)

    # ПРОВЕРКА КУЛДАУНА (Раз в 4 часа)
    last_attack = database.get_raid_attack_time(user_id)
    now = datetime.now()
    cooldown_secs = 14400 # 4 часа
    
    if last_attack:
        if isinstance(last_attack, str): last_attack = datetime.fromisoformat(last_attack)
        elapsed = (now - last_attack).total_seconds()
        if elapsed < cooldown_secs:
            left = cooldown_secs - elapsed
            h = int(left // 3600)
            m = int((left % 3600) // 60)
            await query.answer(f"⏳ Вы истощены! Герой восстановит силы через {h}ч {m}м.", show_alert=True)
            return CLAN_MENU

    # 🔥 СУРОВЫЙ БАЛАНС УРОНА
    best_stat = max(char.get('strength', 0), char.get('intelligence', 0), char.get('agility', 0))
    lvl = char.get('level', 1)
    
    # Адекватная формула: (Стат * 10) + (Уровень * 50) 
    base_dmg = (best_stat * 10) + (lvl * 50)
    damage = int(base_dmg * random.uniform(0.8, 1.2)) # Разброс урона +- 20%
    
    # Крит. шанс 15% (х2 урон)
    is_crit = False
    if random.random() < 0.15: 
        damage *= 2
        is_crit = True
    
    # 🔥 БАЛАНС НАГРАД (Зависит от уровня, а не от нанесенного урона)
    gold_reward = random.randint(30, 80) + (lvl * 3)
    xp_reward = random.randint(50, 150) + (lvl * 10)
    # --- ПАССИВКА ЛЕПРЕКОНА ---
    if char['race'] == 'leprechaun':
        gold_reward = int(gold_reward * 1.05)
    try:
        is_dead, left_hp = database.execute_raid_damage(clan['id'], damage)
        database.update_raid_attack_time(user_id)
        
        database.add_gold(user_id, gold_reward)
        database.add_experience(user_id, xp_reward)
        
        crit_txt = "💥 КРИТИЧЕСКИЙ УДАР!\n" if is_crit else "⚔️ "
        
        if is_dead:
            await query.answer(f"{crit_txt}Вы нанесли {damage} урона и ДОБИЛИ Титана!\n+{gold_reward}g и {xp_reward} XP", show_alert=True)
        else:
            # Форматируем оставшееся HP для красоты: 1000000 -> 1,000,000
            formatted_hp = f"{left_hp:,}".replace(',', ' ')
            await query.answer(f"{crit_txt}Вы нанесли {damage} урона!\n+{gold_reward}g и {xp_reward} XP\nОсталось: {formatted_hp} HP", show_alert=True)
            
    except Exception as e:
        print(f"Raid attack error: {e}")
        await query.answer("Ошибка атаки. Попробуйте еще раз.", show_alert=True)
        
    return await clan_raid_hub_handler(update, context)




async def clan_action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    char = database.get_character(user_id)
    
    if data == 'back_to_main':
        await safe_edit(query, text="В деревне", media=InputMediaPhoto(IMAGE_URLS['village'], caption="В деревне", parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
        return MAIN_MENU
        
    elif data == 'list_clans':
        clans = database.get_all_clans()
        if not clans:
            await query.answer("Мир пуст. Кланов пока нет.", show_alert=True)
            return CLAN_MENU
        
        txt = "📜 *ОТКРЫТЫЕ КЛАНЫ*\nВыберите, куда подать заявку:\n\n"
        kb = []
        for c in clans:
            txt += f"🛡️ *[{c['name']}]* (Участников: {c['members_count']})\n"
            kb.append([InlineKeyboardButton(f"Вступить в [{c['name']}]", callback_data=f"join_clan_{c['id']}")])
        
        kb.append([InlineKeyboardButton("🔙 Назад", callback_data='back_to_clan_hub')])
        await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['castle'], caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))
        return CLAN_MENU
    # === СИСТЕМА ПОДАРКОВ ===
    elif data == 'clan_gift_start':
        clan_id = char.get('clan_id')
        members = database.get_clan_members(clan_id)
        kb = []
        for m in members:
            if m['user_id'] != user_id: # Нельзя дарить самому себе
                kb.append([InlineKeyboardButton(f"🎁 {m['character_name']}", callback_data=f"cg_user_{m['user_id']}")])
        
        if not kb:
            await query.answer("В клане больше никого нет!", show_alert=True)
            return CLAN_MENU
            
        kb.append([InlineKeyboardButton("🔙 Назад", callback_data='back_to_clan_hub')])
        txt = "🎁 *ПОДАРКИ СОКЛАНОВЦАМ*\nВыберите, кого хотите отблагодарить:"
        await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['castle'], caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))
        return CLAN_MENU

    elif data.startswith('cg_user_'):
        target_id = data.split('_')[2]
        context.user_data['gift_target'] = target_id
        
        txt = "Что будем дарить?"
        kb = [
            [InlineKeyboardButton("💰 Золото", callback_data='cg_type_gold')],
            [InlineKeyboardButton("🎒 Материалы / Еду", callback_data='cg_type_item')],
            [InlineKeyboardButton("🔙 Назад", callback_data='clan_gift_start')]
        ]
        await safe_edit(query, text=txt, keyboard=InlineKeyboardMarkup(kb))
        return CLAN_MENU

    elif data == 'cg_type_gold':
        try: await query.message.delete()
        except: pass
        await context.bot.send_message(chat_id=user_id, text=f"💰 У вас есть **{char['gold']}g**.\nСколько золота отправить?\n\n_Напишите число в чат:_")
        return CLAN_GIFT_GOLD_ENTER

    elif data == 'cg_type_item':
        items = database.get_inventory(user_id)
        kb = []
        has_gifts = False
        for i in items:
            info = ITEMS_DB.get(i['item_key'])
            # Дарить можно только расходники и материалы
            if info and info['type'] in ['material', 'food', 'potion', 'buff_potion']:
                has_gifts = True
                kb.append([InlineKeyboardButton(f"{info['name']} (В наличии: {i['quantity']})", callback_data=f"cg_item_{i['item_key']}")])
        
        kb.append([InlineKeyboardButton("🔙 Отмена", callback_data='clan_gift_start')])
        
        txt = "🎁 *ЧТО ПОДАРИМ?*\n_Можно дарить только материалы, еду и зелья._" if has_gifts else "У вас нет подходящих предметов в рюкзаке."
        await safe_edit(query, text=txt, keyboard=InlineKeyboardMarkup(kb))
        return CLAN_MENU

    elif data.startswith('cg_item_'):
        item_key = data.split('_', 2)[2]
        context.user_data['gift_item'] = item_key
        item_info = ITEMS_DB.get(item_key)
        
        try: await query.message.delete()
        except: pass
        await context.bot.send_message(chat_id=user_id, text=f"🎒 Выбран предмет: **{item_info['name']}**.\nСколько штук отправить?\n\n_Напишите число в чат:_")
        return CLAN_GIFT_ITEM_ENTER
    # ========================    
    elif data == 'back_to_clan_hub':
        return await clan_hub_handler(update, context)
        
    elif data.startswith('join_clan_'):
        clan_id = int(data.split('_')[2])
        if char['level'] < 10:
            await query.answer("🔒 Вступление доступно только с 10 уровня!", show_alert=True)
            return CLAN_MENU
            
        database.join_clan(user_id, clan_id)
        await query.answer("✅ Вы успешно присоединились к клану!", show_alert=True)
        return await clan_hub_handler(update, context)
        
    elif data == 'leave_clan':
        database.leave_clan(user_id)
        await query.answer("Вы ушли из клана. (Если вы лидер, клан распущен)", show_alert=True)
        return await clan_hub_handler(update, context)
        
    elif data == 'create_clan_start':
        ranks_order = ['E', 'D', 'C', 'B', 'A', 'S']
        try: p_idx = ranks_order.index(char['rank'])
        except: p_idx = 0
        
        if p_idx < 1: # Нужен ранг D (индекс 1)
            await query.answer("🔒 Вы слишком слабы! Создать клан можно с ранга D.", show_alert=True)
            return CLAN_MENU
            
        if char['gold'] < 10000:
            await query.answer("💸 Не хватает золота! Нужно 10,000g.", show_alert=True)
            return CLAN_MENU
            
        try: await query.message.delete()
        except: pass
        await context.bot.send_message(chat_id=user_id, text="👑 Напишите название вашего будущего Клана (до 20 символов):")
        return CLAN_CREATE_NAME

async def enter_clan_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if len(name) > 20 or len(name) < 2:
        await update.message.reply_text("Название должно быть от 2 до 20 символов. Попробуйте еще раз:")
        return CLAN_CREATE_NAME
        
    context.user_data['temp_clan_name'] = name
    await update.message.reply_text(
        f"🛡 Название «{name}» принято!\n\n"
        "🖼 Теперь отправьте **КАРТИНКУ (ФОТО)**, которая станет гербом вашего клана.\n"
        "_(Отправьте именно как сжатое фото, а не как файл)_"
    )
    return CLAN_CREATE_ICON

async def enter_clan_icon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not update.message.photo:
        await update.message.reply_text("❌ Это не фото! Пожалуйста, загрузите картинку герба.")
        return CLAN_CREATE_ICON
        
    # БЕРЕМ САМОЕ МАЛЕНЬКОЕ ФОТО (индекс 0), чтобы бот не тормозил от 4K изображений
    icon_file_id = update.message.photo[0].file_id
    name = context.user_data.get('temp_clan_name', 'Неизвестно')
    
    success, msg = database.create_clan(user_id, name, icon_file_id)
    
    if success:
        txt = f"🎉 **Вы основали клан [{name}]!**\nТеперь вы можете набирать участников."
        await update.message.reply_photo(photo=icon_file_id, caption=txt, parse_mode='Markdown', reply_markup=get_main_menu_keyboard(user_id))
    else:
        await update.message.reply_text(f"❌ Ошибка: {msg}\nВозврат в деревню.", reply_markup=get_main_menu_keyboard(user_id))
        
    return MAIN_MENU
# ==========================================
# === РЫБАЛКА (Азарт и Смерть) ===
# ==========================================

async def fishing_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if not database.check_building(user_id, 'building_pier'):
        txt = "🌊 **ГНИЛОЙ ПРИЧАЛ**\nДоски прогнили, а лодка пошла ко дну. Восстановите причал, чтобы ловить рыбу.\n💰 Цена: 1000g"
        kb = [[InlineKeyboardButton("🔨 Отстроить Причал (1000g)", callback_data='build_pier')],
              [InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]]
        await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['pier'], caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))
        return MAIN_MENU

    # Проверяем количество наживки
    items = database.get_inventory(user_id)
    bait_count = 0
    for i in items:
        if i['item_key'] == 'bait_worm':
            bait_count = i['quantity']
            break

    txt = (
        "🎣 **МРАЧНЫЙ ПРИЧАЛ**\n"
        "_Вода здесь темная и холодная. Кто знает, что скрывается на дне?_\n\n"
        f"🪱 Наживка (Черви): **{bait_count} шт.**\n"
        "_(Червей можно купить в Магазине в разделе Ресурсов)_"
    )
    
    kb = []
    if bait_count > 0:
        kb.append([InlineKeyboardButton("🎣 ЗАБРОСИТЬ УДОЧКУ (1 червь)", callback_data='catch_fish')])
    else:
        kb.append([InlineKeyboardButton("❌ Нет наживки", callback_data='ignore')])
        
    kb.append([InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')])
    
    await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['pier'], caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))
    return MAIN_MENU

async def build_pier_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    char = database.get_character(user_id)
    
    if char['gold'] >= 1000:
        database.add_gold(user_id, -1000)
        database.build_building(user_id, 'building_pier')
        await query.answer("✅ Причал восстановлен!", show_alert=True)
        await fishing_menu_handler(update, context)
    else:
        await query.answer("❌ Нужно 1000 золота!", show_alert=True)

async def catch_fish_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    char = database.get_character(user_id)
    
    # Списываем 1 наживку
    database.remove_item(user_id, 'bait_worm', 1)
    
    # --- РУЛЕТКА РЫБАКА (СУРОВЫЙ БАЛАНС) ---
    roll = random.random() 
    
    if roll < 0.05: # 5% ШАНС ВЫЛОВИТЬ МОНСТРА 
        if random.random() < 0.20:
            enemy_key = 'swamp_kraken'
        else:
            enemy_key = 'drowned_corpse'
            
        enemy = create_enemy(enemy_key, char['level'])
        
        # --- БРОСОК КУБИКА КАК В ОБЫЧНОМ БОЮ ---
        p_roll = random.randint(1, 16)
        e_roll = random.randint(1, 16)
        
        log = [f"🌊 *УДОЧКА РЕЗКО ДЕРНУЛАСЬ!*\nИз темной воды на вас выпрыгнуло чудовище!\n{enemy['description']}"]
        log.append(f"🎲 Инициатива (d16): Вы [{p_roll}] ⚡ Враг [{e_roll}]")

        # Насильно закидываем в бой (ТЕПЕРЬ С ОЧКАМИ ДЕЙСТВИЯ!)
        battle_sessions[user_id] = {
            'char': char, 
            'enemy': enemy, 
            'enemy_key': enemy_key,
            'log': log, 
            'turn': 1, 'status_effects': [], 'cooldowns': {}, 'last_image': None, 'processing': False,
            'slime_stacks': 0, 'burn_stacks': 0, 'frost_stacks': 0, 'active_buffs': {},
            # --- НОВЫЕ ПЕРЕМЕННЫЕ AP ---
            'max_ap': 5,             
            'player_ap': 5,          
            'bonus_ap_next': 0,      
            'queued_actions': []     
        }
        
        s = battle_sessions[user_id]

        # Если монстр выбросил больше на кубике, он бьет сразу из-под воды!
        if e_roll > p_roll:
            log.append(f"👹 {enemy['name']} оказался быстрее и атакует!")
            enemy_ap = 5
            total_enemy_dmg = 0
            enemy_ability_used = False
            
            while enemy_ap > 0:
                if enemy_ap >= 2 and not enemy_ability_used and random.random() < enemy.get('special_chance', 0.20):
                    spec_dmg, spec_desc, spec_status = process_enemy_special_attack(enemy, char, log) 
                    total_enemy_dmg += spec_dmg
                    enemy_ap -= 2
                    enemy_ability_used = True
                else:
                    base_dmg, is_dodged = calculate_enemy_damage(enemy, char)
                    if not is_dodged:
                        total_enemy_dmg += base_dmg
                    else:
                        log.append("💨 Вы увернулись от внезапной атаки!")
                    enemy_ap -= 1

            if total_enemy_dmg > 0:
                char['health'] -= total_enemy_dmg
                log.append(f"💔 Враг нанес *{total_enemy_dmg}* урона внезапной атакой.")

            # Проверка, не убил ли нас Кракен с одного удара
            if char['health'] <= 0:
                database.update_character_stats(user_id, health=0, battle_losses=char.get('battle_losses',0)+1)
                del battle_sessions[user_id]
                death_msg = "💀 *Тварь утащила вас на дно...*"
                await safe_edit(query, text=death_msg, media=InputMediaPhoto(IMAGE_URLS.get('dungeon', ''), caption=death_msg, parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
                return MAIN_MENU
        else:
            log.append("⚡ Вы успели отскочить от брызг! Ваш ход.")

        await query.answer("УДОЧКА ДЕРНУЛАСЬ! К БОЮ!", show_alert=True)
        await render_battle(query, user_id)
        return IN_BATTLE
        
    elif roll < 0.10: # 5% ШАНС НА СУНДУК
        gold_found = random.randint(30, 100)
        database.add_gold(user_id, gold_found)
        database.buy_item(user_id, 'small_hp', 'potion', '🧪 Малое лечебное', 0, 30)
        
        txt = f"📦 **СУНДУК!**\nВы вытащили со дна старый сундук!\n\nВы получили: {gold_found}g и 🧪 Малое лечебное."
        kb = [[InlineKeyboardButton("🎣 Забросить еще раз", callback_data='fishing_menu')]]
        await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['pier'], caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))
        return MAIN_MENU
        
    elif roll < 0.40: # 30% ШАНС НА МУСОР
        database.buy_item(user_id, 'trash_boot', 'material', '👢 Дырявый сапог', 0, 0)
        txt = "👢 **Мусор...**\nВы вытянули чей-то старый дырявый сапог."
        kb = [[InlineKeyboardButton("🎣 Забросить еще раз", callback_data='fishing_menu')]]
        await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['pier'], caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))
        return MAIN_MENU
        
    else: # 60% ШАНС ВЫЛОВИТЬ РЫБУ
        if random.random() < 0.03:
            database.buy_item(user_id, 'fish_golden', 'material', '🐡 Золотой карп', 0, 0)
            txt = "✨ **РЕДКИЙ УЛОВ!**\nВы поймали 🐡 Золотого карпа! Его можно дорого продать."
        else:
            database.buy_item(user_id, 'fish_blind', 'material', '🐟 Слепая рыба', 0, 0)
            txt = "🐟 **Улов!**\nВы поймали Слепую рыбу. Повар будет рад."
            
        kb = [[InlineKeyboardButton("🎣 Забросить еще раз", callback_data='fishing_menu')]]
        await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['pier'], caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))
        return MAIN_MENU


# --- ГЕНЕРАТОР ЗАДАНИЙ ---
def generate_daily_quests(rank, reputation=0): # <--- Добавили аргумент reputation
    """Генерирует квесты с учетом репутации"""
    quests = []
    
    # Расчет множителя награды от репутации
    rep_multiplier = 1.0
    if reputation >= 100: rep_multiplier = 1.3  # +30%
    elif reputation >= 50: rep_multiplier = 1.15 # +15%
    
    # ... (код сбора available_enemies и drops остается прежним) ...
    # (Скопируйте его из старой функции)
    # ПОВТОРЯЕМ ЛОГИКУ СБОРА ВРАГОВ:
    available_enemies = []
    available_drops = []
    ranks_order = ['E', 'D', 'C', 'B', 'A', 'S']
    try: current_rank_idx = ranks_order.index(rank)
    except: current_rank_idx = 0
    
    for key, data in BASE_ENEMIES.items():
        e_rank = data.get('rank', 'E')
        try: e_idx = ranks_order.index(e_rank)
        except: e_idx = 0
        if e_idx <= current_rank_idx:
            available_enemies.append(key)
            if data.get('drops'):
                for d in data['drops']: available_drops.append(d)
    
    if not available_enemies: available_enemies = ['wolf']

    # ГЕНЕРАЦИЯ
    for _ in range(3):
        q_type = random.choice(['kill', 'kill', 'collect'])
        
        if q_type == 'kill':
            target = random.choice(available_enemies)
            enemy_name = BASE_ENEMIES[target]['name']
            count = random.randint(3, 5) + (current_rank_idx * 2)
            
            # ПРИМЕНЯЕМ МНОЖИТЕЛЬ РЕПУТАЦИИ
            base_gold = count * BASE_ENEMIES[target].get('base_gold', 5) * 1.5
            base_exp = count * BASE_ENEMIES[target].get('base_exp', 5) * 1.5
            
            quests.append({
                'type': 'kill', 'target': target, 'goal': count, 
                'gold': int(base_gold * rep_multiplier), # <--- БОНУС
                'exp': int(base_exp * rep_multiplier),   # <--- БОНУС
                'desc': f"Убить: {enemy_name} ({count} шт.)"
            })
            
        elif q_type == 'collect':
            if not available_drops: continue
            target = random.choice(available_drops)
            item_name = ITEMS_DB.get(target, {'name': target})['name']
            count = random.randint(2, 4) + current_rank_idx
            
            # ПРИМЕНЯЕМ МНОЖИТЕЛЬ РЕПУТАЦИИ
            base_gold = count * ITEMS_DB.get(target, {}).get('price', 5) * 2.0
            base_exp = base_gold * 0.8
            
            quests.append({
                'type': 'collect', 'target': target, 'goal': count, 
                'gold': int(base_gold * rep_multiplier), # <--- БОНУС
                'exp': int(base_exp * rep_multiplier),   # <--- БОНУС
                'desc': f"Принести: {item_name} ({count} шт.)"
            })
            
    return quests

async def guild_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    
    # 1. КНОПКА НАЗАД
    if data == 'back_to_main':
        await safe_edit(query, text="В деревне", media=InputMediaPhoto(IMAGE_URLS['village'], caption="В деревне", parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
        return MAIN_MENU

    # 2. ОБРАБОТКА ДЕЙСТВИЙ
    
    # А) Взятие квеста
    if data.startswith('take_quest_'):
        parts = data.split('_')
        try:
            q_exp = int(parts[-1])
            q_gold = int(parts[-2])
            q_goal = int(parts[-3])
            q_type = parts[2]
            q_target = "_".join(parts[3:-3])
            database.take_quest(user_id, q_type, q_target, q_goal, q_gold, q_exp)
            await query.answer("✅ Контракт подписан!")
        except: pass

    # Б) Реролл (обновление списка)
    elif data == 'reroll_quests':
        char = database.get_character(user_id)
        if char['gold'] >= 50:
            database.add_gold(user_id, -50)
            new_quests = generate_daily_quests(char['rank'], char.get('guild_reputation', 0))
            database.save_daily_quests(user_id, new_quests)
            await query.answer("Обновлено!")
        else:
            await query.answer("Мало золота!")

    # В) Завершение квеста
    elif data == 'complete_quest':
        success, msg = database.complete_quest(user_id)
        if success:
            await query.answer("Награда получена!")
            await safe_edit(query, text=msg, media=InputMediaPhoto(IMAGE_URLS['guild'], caption=msg, parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
            return MAIN_MENU
        else:
            await query.answer(f"❌ {msg}", show_alert=True)

    # Г) НАЖАТИЕ "ОТКАЗАТЬСЯ" (ПРЕДУПРЕЖДЕНИЕ)
    elif data == 'cancel_quest':
        txt = ("⚠️ **РАЗРЫВ КОНТРАКТА**\n\n"
               "Вы уверены, что хотите отказаться от задания?\n"
               "Мастер Гильдии запомнит это.\n\n"
               "📉 **Штраф:** -10 Репутации.")
        
        kb = [
            [InlineKeyboardButton("✅ Да, я сдаюсь (-10 Реп)", callback_data='confirm_cancel')],
            [InlineKeyboardButton("🔙 Нет, я справлюсь!", callback_data='guild_menu')] # Просто обновляем меню, вернет нас к квесту
        ]
        await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['guild'], caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))
        return GUILD_MENU

    # Д) ПОДТВЕРЖДЕНИЕ ОТКАЗА (РЕАЛЬНОЕ УДАЛЕНИЕ)
    elif data == 'confirm_cancel':
        success, msg = database.cancel_quest(user_id)
        if success:
            await query.answer("Контракт разорван.", show_alert=True)
            # Код пойдет дальше вниз и отрисует Доску Объявлений (так как квеста больше нет)
        else:
            await query.answer("Ошибка отмены.", show_alert=True)

    # Е) ПРОСТО ОБНОВЛЕНИЕ МЕНЮ (ЕСЛИ НАЖАЛИ "НЕТ")
    elif data == 'guild_menu':
        pass # Просто идем вниз к отрисовке

    try: await query.answer()
    except: pass

    # 3. ОТРИСОВКА (VIEW)
    char = database.get_character(user_id)
    rep = char.get('guild_reputation', 0)
    
    rep_status = "😐 Нейтрал"
    if rep >= 100: rep_status = "👑 Почет (+30% наград)"
    elif rep >= 50: rep_status = "🤝 Уважение (+15% наград)"
    
    header = f"📜 *ГИЛЬДИЯ ГЕРОЕВ*\nРепутация: {rep} ({rep_status})\n━━━━━━━━━━━━━━━━\n"

    # СЦЕНАРИЙ 1: ЕСТЬ АКТИВНЫЙ КВЕСТ
    if char.get('quest_target'):
        target_name = char['quest_target']
        if char['quest_type'] == 'kill' and char['quest_target'] in BASE_ENEMIES:
            target_name = BASE_ENEMIES[char['quest_target']]['name']
            prog_txt = f"☠️ Убито: {char['quest_progress']}/{char['quest_goal']}"
        else:
            item = ITEMS_DB.get(char['quest_target'])
            if item: target_name = item['name']
            items = database.get_inventory(user_id)
            curr = 0
            for i in items:
                if i['item_key'] == char['quest_target']:
                    curr = i['quantity']
                    break
            prog_txt = f"🎒 Собрано: {curr}/{char['quest_goal']}"

        txt = (f"{header}"
               f"⚔️ *ТЕКУЩИЙ КОНТРАКТ*\n"
               f"Цель: {target_name}\n{prog_txt}\n\n"
               f"💰 {char['quest_reward_gold']}g | 📚 {char['quest_reward_exp']}xp")
        
        kb = [
            [InlineKeyboardButton("✅ Завершить", callback_data='complete_quest')],
            [InlineKeyboardButton("❌ Отказаться", callback_data='cancel_quest')], # Ведет на подтверждение
            [InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]
        ]
        await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['guild'], caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))
        return GUILD_MENU

    # СЦЕНАРИЙ 2: ЛИМИТ ЗАДАНИЙ
    today = datetime.now().date()
    last_date = char.get('last_quest_date')
    done_today = char.get('quests_completed_today', 0)
    if isinstance(last_date, str):
        try: last_date = datetime.strptime(last_date, '%Y-%m-%d').date()
        except: pass
        
    if last_date == today and done_today >= 2:
        txt = f"{header}\nЛимит заданий исчерпан (2/2).\nПриходите завтра."
        kb = [[InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]]
        await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['guild'], caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))
        return GUILD_MENU

    # СЦЕНАРИЙ 3: ДОСКА ОБЪЯВЛЕНИЙ
    stored_quests, last_refresh = database.get_stored_quests(user_id)
    if isinstance(last_refresh, str):
        try: last_refresh = datetime.strptime(last_refresh, '%Y-%m-%d').date()
        except: pass

    quests_to_show = []
    if stored_quests and last_refresh == today:
        quests_to_show = stored_quests
    else:
        quests_to_show = generate_daily_quests(char['rank'], rep)
        database.save_daily_quests(user_id, quests_to_show)

    txt = f"{header}Выберите контракт ({done_today}/2 сегодня):"
    
    kb = []
    for q in quests_to_show:
        cb_data = f"take_quest_{q['type']}_{q['target']}_{q['goal']}_{q['gold']}_{q['exp']}"
        btn_txt = f"{q['desc']} (💰{q['gold']} 📚{q['exp']})"
        kb.append([InlineKeyboardButton(btn_txt, callback_data=cb_data)])
    
    kb.append([InlineKeyboardButton("🔄 Новые задания (50g)", callback_data='reroll_quests')])
    kb.append([InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')])
    
    await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['guild'], caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))
    return GUILD_MENU
    

async def elf_magic_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    # Мы используем этот флаг, чтобы понять, нужно ли рисовать меню в конце
    should_render_menu = True

    # 1. ОБРАБОТКА КНОПКИ "НАЗАД В ГЛАВНОЕ"
    if query.data == 'back_to_main':
        await query.answer()
        await safe_edit(query, text="В деревне", media=InputMediaPhoto(IMAGE_URLS['village'], caption="В деревне", parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
        return MAIN_MENU

    # 2. ОБРАБОТКА ВЫБОРА ШКОЛЫ (Рисуем подменю школы)
    if query.data.startswith('school_'):
        school_key = query.data.split('_')[1] # sun, moon, star
        char = database.get_character(user_id)
        
        school_data = ELF_SPELLS[school_key]
        active_spell = char.get('elf_active_spell')
        
        txt = f"📖 *{school_data['name']}*\nВыберите заклинание, которое будете использовать в бою:\n\n"
        kb = []
        
        for key, spell in school_data['spells'].items():
            status = "🔒 (Нужен ур. " + str(spell['lvl']) + ")"
            if char['level'] >= spell['lvl']:
                if active_spell == key:
                    status = "✅ АКТИВНО"
                else:
                    status = "Выбрать"
                    
            btn_text = f"{spell['name']} ({spell['mana']} MP) - {status}"
            
            if char['level'] >= spell['lvl']:
                kb.append([InlineKeyboardButton(btn_text, callback_data=f"set_spell_{key}")])
            else:
                kb.append([InlineKeyboardButton(f"🔒 {spell['name']} (Ур. {spell['lvl']})", callback_data="ignore")])
                
        kb.append([InlineKeyboardButton("🔙 К списку школ", callback_data='elf_magic_menu')])
        
        await safe_edit(query, text=txt, keyboard=InlineKeyboardMarkup(kb))
        return MAIN_MENU # Выходим, так как мы уже отрисовали подменю

    # 3. ОБРАБОТКА ВЫБОРА ЗАКЛИНАНИЯ (ИСПРАВЛЕНО)
    if query.data.startswith('set_spell_'):
        spell_key = query.data.split('_', 2)[2]
        database.set_elf_spell(user_id, spell_key)
        await query.answer("Заклинание подготовлено!", show_alert=True)
        # ВАЖНО: Мы НЕ вызываем здесь функцию заново.
        # Мы просто позволяем коду идти дальше (в пункт 4), 
        # чтобы он отрисовал главное меню школ.

    # 4. ГЛАВНОЕ МЕНЮ МАГИИ (СПИСОК ШКОЛ)
    # Этот код выполнится, если нажали 'elf_magic_menu' ИЛИ если только что выбрали заклинание (пункт 3)
    char = database.get_character(user_id)
    
    curr_spell_key = char.get('elf_active_spell')
    curr_spell_name = "Не выбрано (Будет обычная магия)"
    
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
    
    img = IMAGE_URLS.get('mage', 'https://i.pinimg.com/736x/9f/8e/25/9f8e2507aceaa217060d249c308e2a13.jpg')
    
    await safe_edit(query, text=txt, media=InputMediaPhoto(img, caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))
    return MAIN_MENU

async def render_sell_menu(query, user_id):
    """Рисует меню продажи с актуальными данными"""
    char = database.get_character(user_id)
    items = database.get_inventory(user_id)
    
    txt = f"💰 *СКУПКА КРАДЕНОГО*\nТорговец готов купить ваши вещи за 50% от стоимости.\n\n_Ваше золото: {char['gold']}g_"
    
    if not items:
        txt += "\n\n_(Рюкзак пуст)_"
    
    kb = []
    for i in items:
        item_info = ITEMS_DB.get(i['item_key'])
        if not item_info: continue
        
        # Цена продажи = Цена / 2
        sell_price = max(1, item_info['price'] // 2)
        
        # Кнопка: "🐺 Шкура (x5) - 2g"
        btn_txt = f"{item_info['name']} (x{i['quantity']}) — {sell_price}g"
        kb.append([InlineKeyboardButton(btn_txt, callback_data=f"sell_item_{i['item_key']}")])
        
    kb.append([InlineKeyboardButton("🔙 Назад в магазин", callback_data='shop')])
    
    # Используем safe_edit для обновления
    await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['shop'], caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))

# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ОТРИСОВКИ МЕНЮ ПРОДАЖИ ---
async def render_sell_menu(query, user_id):
    """Рисует меню продажи с актуальными данными о золоте и предметах"""
    char = database.get_character(user_id)
    items = database.get_inventory(user_id)
    
    txt = f"💰 *СКУПКА КРАДЕНОГО*\nТорговец готов купить ваши вещи за 50% от стоимости.\n\n_Ваше золото: {char['gold']}g_"
    
    if not items:
        txt += "\n\n_(Рюкзак пуст)_"
    
    kb = []
    for i in items:
        item_info = ITEMS_DB.get(i['item_key'])
        if not item_info: continue
        
        # Цена продажи = Цена / 2 (минимум 1 золотая)
        sell_price = max(1, item_info['price'] // 2)
        
        # Кнопка: "🐺 Шкура (x5) - 2g"
        btn_txt = f"{item_info['name']} (x{i['quantity']}) — {sell_price}g"
        kb.append([InlineKeyboardButton(btn_txt, callback_data=f"sell_item_{i['item_key']}")])
        
    kb.append([InlineKeyboardButton("🔙 Назад в магазин", callback_data='shop')])
    
    # Используем safe_edit для обновления картинки и текста
    await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['shop'], caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))

async def render_shop_category(query, user_id, cat):
    """Вспомогательная функция для отрисовки страницы категории (ТЕКСТОВАЯ ВЕРСИЯ)"""
    try:
        char = database.get_character(user_id)
        cat_names = {
            'food': '🍖 Еда и Напитки', 
            'mat': '🧱 Ресурсы', 
            'weapon': '⚔️ Оружие', 
            'armor': '🛡️ Броня', 
            'acc': '💍 Аксессуары'
        }
        
        txt = f"🏪 *{cat_names.get(cat, 'Товары')}*\n_Баланс: {char['gold']}g_\n\n"
        items_found = False
        
        # --- СПИСОК ЭКСКЛЮЗИВОВ ФЕРМЫ И КУХНИ (Скрываем из магазина) ---
        farm_and_kitchen = ['wheat', 'carrot', 'potato', 'magic_bean', 'bread_fresh', 'carrot_soup', 'meat_pie', 'magic_stew']
        
        for key, item in ITEMS_DB.items():
            # 1. Проверяем категорию
            if item.get('cat') != cat:
                continue

            # 2. ФИЛЬТР: Скрываем ферму и кухню
            if key in farm_and_kitchen:
                continue

            # 3. ФИЛЬТР: Скрываем всё, что для Алхимии (начинается на pot_ или это бафф)
            if cat == 'food':
                # Если это новое зелье (крафтовое) — пропускаем
                if key.startswith('pot_'): continue
                # Если это бафф — пропускаем
                if item.get('type') == 'buff_potion': continue 

            # 4. Скрываем тестовые предметы
            if item.get('is_test', False):
                pass 

            items_found = True
            effect_str = ""
            itype = item.get('type', 'unknown')
            ieffect = item.get('effect', 0)
            
            if ieffect:
                if itype == 'weapon':         effect_str = f" (+{ieffect} ⚔️)"
                elif itype == 'agi_weapon':   effect_str = f" (+{ieffect} 💨 / +{max(1, ieffect//2)} ⚔️)"
                elif itype == 'magic_weapon': effect_str = f" (+{ieffect} 🔮)"
                elif itype == 'heavy_armor':  effect_str = f" (+{ieffect} HP/Физ)"
                elif itype == 'light_armor':  effect_str = f" (+{int(ieffect*0.6)} HP/Ловк)"
                elif itype == 'magic_armor':  effect_str = f" (+{ieffect*2} MP/Маг)"
                elif itype == 'armor':        effect_str = f" (+{ieffect} HP)"
                elif itype == 'artifact':     effect_str = f" (+{ieffect} 🧠)"
                elif itype == 'food':         effect_str = f" (+{ieffect} ❤️)"
                elif itype == 'potion':       
                    if 'mp' in key or 'mana' in key: effect_str = f" (+{ieffect} MP)"
                    else: effect_str = f" (+{ieffect} HP)"

            rank_str = f" [Ранг {item['rank']}]" if item.get('rank') else ""
            
            # Иконка
            icon = "▪️"
            if itype == 'heavy_armor': icon = "🛡"
            elif itype == 'light_armor': icon = "💨"
            elif itype == 'magic_armor': icon = "🔮"
            elif itype == 'food': icon = "🍖"
            elif itype == 'potion': icon = "🧪"
            
            txt += f"{icon} *{item['name']}* {rank_str} — {item['price']}g\n   _{item['desc']}_{effect_str}\n\n"

        if not items_found: 
            txt += "В этой категории пока пусто."
        
        if len(txt) > 4000: txt = txt[:4000] + "..."

        try:
            await query.edit_message_text(text=txt, parse_mode='Markdown', reply_markup=get_shop_items_keyboard(cat, char['gold']))
        except BadRequest:
            await query.delete_message()
            await query.message.reply_text(text=txt, parse_mode='Markdown', reply_markup=get_shop_items_keyboard(cat, char['gold']))
        
    except Exception as e:
        import traceback
        print(f"Shop Render Error: {e}")
        await safe_edit(query, text="Ошибка магазина.", keyboard=get_main_menu_keyboard(user_id))


async def shop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    char = database.get_character(user_id)
    
    # 1. КНОПКА НАЗАД
    if data == 'back_to_main':
        await query.answer()
        await safe_edit(query, text="В деревне", media=InputMediaPhoto(IMAGE_URLS['village'], caption="В деревне", parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
        return MAIN_MENU

    # 2. ГЛАВНОЕ МЕНЮ
    elif data == 'shop': 
        await query.answer()
        txt = f"🏪 *Мрачная лавка*\nЗолото: {char['gold']}💰\nЧего желаете?"
        await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['shop'], caption=txt, parse_mode='Markdown'), keyboard=get_shop_categories_keyboard())
        return SHOP_MENU

    # 3. МЕНЮ ПРОДАЖИ
    elif data == 'shop_sell_menu':
        await query.answer()
        await render_sell_menu(query, user_id)
        return SHOP_MENU

    # ==========================================
    # 4. МЕНЮ ВЫБОРА КОЛИЧЕСТВА ДЛЯ ПРОДАЖИ
    # ==========================================
    elif data.startswith('sell_item_') and not data.startswith('sell_exec_'):
        item_key = data.split('_', 2)[2]
        items = database.get_inventory(user_id)
        
        # Ищем предмет в инвентаре
        item_data = next((i for i in items if i['item_key'] == item_key), None)
        if not item_data or item_data['quantity'] <= 0:
            await query.answer("У вас нет этого предмета!", show_alert=True)
            return SHOP_MENU
            
        item_info = ITEMS_DB.get(item_key)
        if not item_info: return SHOP_MENU
        
        sell_price = max(1, item_info.get('price', 10) // 2)
        if char['race'] == 'leprechaun':
                sell_price = int(sell_price * 1.05)
        max_qty = item_data['quantity']
        
        txt = (
            f"⚖️ *Торговец оценивает ваш товар*\n"
            f"📦 Предмет: *{item_info['name']}*\n"
            f"📊 В наличии: {max_qty} шт.\n"
            f"🪙 Цена за 1 шт: {sell_price}g\n\n"
            f"Сколько хотите продать?"
        )
        
        kb = [
            [InlineKeyboardButton(f"1 шт (+{sell_price}g)", callback_data=f"sell_exec_{item_key}_1")]
        ]
        if max_qty >= 5:
            kb.append([InlineKeyboardButton(f"5 шт (+{sell_price * 5}g)", callback_data=f"sell_exec_{item_key}_5")])
        if max_qty >= 10:
            kb.append([InlineKeyboardButton(f"10 шт (+{sell_price * 10}g)", callback_data=f"sell_exec_{item_key}_10")])
        if max_qty > 1:
            kb.append([InlineKeyboardButton(f"💰 Продать ВСЁ ({max_qty} шт за {sell_price * max_qty}g)", callback_data=f"sell_exec_{item_key}_all")])
            
        kb.append([InlineKeyboardButton("🔙 Отмена", callback_data='shop_sell_menu')])
        
        # Если у вас нет IMAGE_URLS['shop'], будет использована 'village'
        await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS.get('shop', IMAGE_URLS.get('village', '')), caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))
        return SHOP_MENU

    # ==========================================
    # 4.1. ФАКТИЧЕСКОЕ ВЫПОЛНЕНИЕ ПРОДАЖИ
    # ==========================================
    elif data.startswith('sell_exec_'):
        if context.user_data.get('is_selling'):
            await query.answer("⏳ Торговец пересчитывает монеты...", show_alert=False)
            return SHOP_MENU
            
        context.user_data['is_selling'] = True
        try:
            parts = data.split('_')
            qty_str = parts[-1]
            item_key = "_".join(parts[2:-1])
            
            items = database.get_inventory(user_id)
            item_data = next((i for i in items if i['item_key'] == item_key), None)
            
            if not item_data or item_data['quantity'] <= 0:
                await query.answer("Предмет уже закончился!", show_alert=True)
                await render_sell_menu(query, user_id)
                return SHOP_MENU
                
            max_qty = item_data['quantity']
            sell_qty = max_qty if qty_str == 'all' else int(qty_str)
            if sell_qty > max_qty: sell_qty = max_qty
            
            item_info = ITEMS_DB.get(item_key)
            if not item_info: return SHOP_MENU
            
            stat_changes = {}
            eff = item_info.get('effect', 0)
            
            # Собираем данные о снятии статов (как было у вас)
            if eff > 0:
                itype = item_info['type']
                if itype == 'weapon': stat_changes['strength'] = -eff
                elif itype == 'magic_weapon':
                    stat_changes['intelligence'] = -eff
                    stat_changes['max_mana'] = -(eff * 3)
                    stat_changes['mana'] = -(eff * 3)
                elif itype == 'agi_weapon': 
                    stat_changes['strength'] = -max(1, eff // 2)
                    stat_changes['agility'] = -eff
                elif itype == 'heavy_armor':
                    stat_changes['max_health'] = -eff
                    stat_changes['health'] = -eff
                    stat_changes['physical_resistance'] = -(eff / 200.0) 
                elif itype == 'light_armor':
                    stat_changes['max_health'] = -int(eff * 0.6)
                    stat_changes['health'] = -int(eff * 0.6)
                    stat_changes['agility'] = -int(eff / 2)
                elif itype == 'magic_armor':
                    stat_changes['max_mana'] = -(eff * 2)
                    stat_changes['mana'] = -(eff * 2)
                    stat_changes['magic_resistance'] = -(eff / 200.0) 
                elif itype in ['artifact', 'acc']:
                    stat_changes['intelligence'] = -eff
                    stat_changes['max_mana'] = -(eff * 5)
                    stat_changes['mana'] = -(eff * 5)

            sell_price = max(1, item_info.get('price', 10) // 2)
            success_count = 0
            
            # Выполняем продажу N раз, чтобы статы корректно снялись за каждую штуку
            for _ in range(sell_qty):
                success, msg = database.execute_sell(user_id, item_key, sell_price, stat_changes)
                if success:
                    success_count += 1
                else:
                    break # Если произошла ошибка в БД, прерываем цикл
            
            if success_count > 0:
                total_profit = success_count * sell_price
                await query.answer(f"💰 Продано {success_count} шт. (+{total_profit}g)", show_alert=True)
            else:
                await query.answer("❌ Ошибка при продаже.", show_alert=True)
                
            await render_sell_menu(query, user_id)
            
        finally:
            context.user_data['is_selling'] = False
            
        return SHOP_MENU

    # 5. КАТЕГОРИИ
    elif data.startswith('shop_cat_'):
        await query.answer()
        cat = data.split('_')[2]
        await render_shop_category(query, user_id, cat)
        return SHOP_MENU
    
    # 6. ПОКУПКА
    elif data.startswith('buy_'):
        item_key = data.split('_', 1)[1]
        item = ITEMS_DB.get(item_key)
        
        if not item: 
            await query.answer("Товар не найден.")
            return SHOP_MENU

        # Проверка ранга
        if item.get('rank'):
            ranks_order = ['E', 'D', 'C', 'B', 'A', 'S']
            try:
                if ranks_order.index(char['rank']) < ranks_order.index(item['rank']):
                    await query.answer(f"🔒 Недоступно! Нужен ранг {item['rank']}", show_alert=True)
                    return SHOP_MENU
            except: pass 

        itype = item['type']
        
        # --- ЕСЛИ ЭТО ЕДА, ЗЕЛЬЕ ИЛИ РЕСУРС -> СПРАШИВАЕМ КОЛИЧЕСТВО ---
        if itype in ['material', 'food', 'potion', 'buff_potion']:
            context.user_data['buy_item_key'] = item_key
            try: await query.message.delete()
            except: pass
            
            max_can_buy = char['gold'] // item['price'] if item['price'] > 0 else 999
            if max_can_buy < 1:
                await query.answer("💸 Не хватает золота даже на одну штуку!", show_alert=True)
                return SHOP_MENU
                
            msg = (f"🛒 **Покупка: {item['name']}**\n"
                   f"Цена: {item['price']}g за шт.\n"
                   f"Ваше золото: {char['gold']}g\n\n"
                   f"_Напишите в чат, сколько штук хотите купить (максимум доступно: {max_can_buy} шт.):_")
            
            await context.bot.send_message(chat_id=user_id, text=msg, parse_mode='Markdown')
            return SHOP_BUY_QUANTITY

        # --- ЕСЛИ ЭТО ЭКИПИРОВКА -> ПОКУПАЕМ СРАЗУ 1 ШТ. ---
        items = database.get_inventory(user_id)
        
        weapon_types = ['weapon', 'magic_weapon','agi_weapon']
        armor_types = ['armor', 'heavy_armor', 'light_armor', 'magic_armor']
        
        if itype in weapon_types or itype in armor_types:
            count = 0
            target_list = weapon_types if itype in weapon_types else armor_types
            for i in items:
                info = ITEMS_DB.get(i['item_key'])
                if info and info['type'] in target_list: count += i['quantity']
            if count >= 5:
                await query.answer(f"🎒 Слот переполнен! (Макс 5 шт.)", show_alert=True)
                return SHOP_MENU

        if itype in ['artifact', 'acc']:
            acc_count = sum(i['quantity'] for i in items if ITEMS_DB.get(i['item_key'], {}).get('type') in ['artifact', 'acc'])
            if acc_count >= 20:
                await query.answer("⛔ Слот аксессуаров полон! (Макс 20 шт.)", show_alert=True)
                return SHOP_MENU

        if char['gold'] >= item['price']:
            res, msg = database.buy_item(user_id, item_key, item['type'], item['name'], item['price'], item.get('effect', 0), amount=1)
            await query.answer(msg, show_alert=True)
            if 'cat' in item:
                await render_shop_category(query, user_id, item['cat'])
        else:
            await query.answer("💸 Не хватает золота!", show_alert=True)
            
    return SHOP_MENU
    
async def show_craft_category(query, user_id, category_filter):
    """Показывает рецепты только выбранной категории (БЕЗ КАРТИНКИ, ЧТОБЫ ВЛЕЗЛО)"""
    try:
        items = database.get_inventory(user_id)
        inv_dict = {i['item_key']: i['quantity'] for i in items}
        
        # Заголовки
        headers = {
            'weapon': "⚔️ КУЗНИЦА: ОРУЖИЕ",
            'armor': "🛡️ КУЗНИЦА: БРОНЯ",
            'consumables': "🧪 АЛХИМИЯ"
        }
        
        txt = f"*{headers.get(category_filter, 'КУЗНИЦА')}*\n\n"
        
        kb = []
        found_recipes = False

        for key, recipe in CRAFT_RECIPES.items():
            result_item = ITEMS_DB.get(recipe['result'])
            if not result_item: continue
            
            # --- ФИЛЬТРАЦИЯ ---
            itype = result_item['type']
            is_match = False
            
            if category_filter == 'weapon':
                if itype in ['weapon', 'magic_weapon']: is_match = True
            
            elif category_filter == 'armor':
                if itype in ['heavy_armor', 'light_armor', 'magic_armor', 'armor']: is_match = True
            
            elif category_filter == 'consumables':
                if itype in ['food', 'potion']: is_match = True
            
            if not is_match: continue
            # ------------------
            
            found_recipes = True
            
            # Текст рецепта
            # Используем эмодзи для типа
            type_icon = "🔸"
            if itype == 'heavy_armor': type_icon = "🛡"
            elif itype == 'light_armor': type_icon = "💨"
            elif itype == 'magic_armor': type_icon = "🔮"
            elif itype == 'magic_weapon': type_icon = "🪄"
            elif itype == 'weapon': type_icon = "⚔️"

            txt += f"{type_icon} *{result_item['name']}* (💰 {recipe['cost']}g)\n"
            if result_item.get('desc'): txt += f"_{result_item['desc']}_\n"
            
            mats_txt = []
            for mat_key, required_amount in recipe['mats'].items():
                mat_info = ITEMS_DB.get(mat_key)
                mat_name = mat_info['name'] if mat_info else mat_key
                user_amount = inv_dict.get(mat_key, 0)
                mark = "✅" if user_amount >= required_amount else "❌"
                mats_txt.append(f"{mark} {mat_name} {user_amount}/{required_amount}")
            
            txt += " + ".join(mats_txt) + "\n\n"
            
            # Кнопка крафта
            kb.append([InlineKeyboardButton(f"🔨 Создать {result_item['name']}", callback_data=f"craft_{key}")])

        if not found_recipes:
            txt += "В этой категории пока нет рецептов."

        # Лимит текста 4096, это очень много, обрезать скорее всего не придется
        if len(txt) > 4000: txt = txt[:4000] + "..."
        
        kb.append([InlineKeyboardButton("🔙 Назад к категориям", callback_data='craft_menu')])

        # ВАЖНО: Используем edit_message_text вместо edit_message_media
        # Сначала пробуем удалить медиа (если предыдущее сообщение было с картинкой)
        try:
            await query.edit_message_text(text=txt, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
        except BadRequest:
            # Если не получилось изменить (например, была картинка), шлем новое сообщение
            await query.delete_message()
            await query.message.reply_text(text=txt, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        await query.answer("Ошибка меню крафта.", show_alert=True)
        
async def craft_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    
    # 1. НАЗАД В ГЛАВНОЕ
    if data == 'back_to_main':
        await query.answer()
        await safe_edit(query, text="В деревне", media=InputMediaPhoto(IMAGE_URLS['village'], caption="В деревне", parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
        return MAIN_MENU
    
    # 2. ГЛАВНОЕ МЕНЮ КРАФТА (ВЫБОР КАТЕГОРИИ)
    # 2. ГЛАВНОЕ МЕНЮ КРАФТА (ВЫБОР КАТЕГОРИИ)
    elif data == 'craft_menu':
        await query.answer()
        txt = "🛠 *Кузница*\nВыберите категорию предметов для создания:"
        
        kb = [
            [InlineKeyboardButton("⚔️ Оружие", callback_data='craft_cat_weapon')],
            [InlineKeyboardButton("🛡️ Броня", callback_data='craft_cat_armor')],
            [InlineKeyboardButton("🧪 Зелья и Еда", callback_data='craft_cat_consumables')],
            [InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]
        ]
        await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['craft'], caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))
        return CRAFT_MENU
        
    # 3. ПРОСМОТР КАТЕГОРИИ
    elif data.startswith('craft_cat_'):
        await query.answer()
        cat_type = data.split('_')[2] # weapon, armor, consumables
        await show_craft_category(query, user_id, cat_type)
        return CRAFT_MENU

    # 4. САМ КРАФТ (СОЗДАНИЕ ПРЕДМЕТА)
    elif data.startswith('craft_'):
        try:
            recipe_key = data[6:] 
            recipe = CRAFT_RECIPES.get(recipe_key)
            
            if not recipe:
                await query.answer("Рецепт не найден.", show_alert=True)
                return CRAFT_MENU
            
            result_item = ITEMS_DB.get(recipe['result'])
            if not result_item:
                await query.answer("Ошибка базы предметов.", show_alert=True)
                return CRAFT_MENU
                
            target_type = result_item['type']
            items = database.get_inventory(user_id)

            # Проверка лимита (5 шт) для экипировки (Ваш старый код)
            equip_types = ['weapon', 'magic_weapon', 'heavy_armor', 'light_armor', 'magic_armor']
            if target_type in equip_types:
                current_count = 0
                target_group = ['weapon', 'magic_weapon'] if 'weapon' in target_type else ['heavy_armor', 'light_armor', 'magic_armor']
                
                for item in items:
                    info = ITEMS_DB.get(item['item_key'])
                    if info and info['type'] in target_group: 
                        current_count += item['quantity']

                if current_count >= 5:
                    await query.answer(f"⛔ ПРЕДЕЛ! (Макс 5 шт. этого типа).", show_alert=True)
                    return CRAFT_MENU

            # 2. НОВАЯ ПРОВЕРКА ДЛЯ АКСЕССУАРОВ (Лимит 20)
            if target_type in ['artifact', 'acc']:
                acc_count = 0
                for item in items:
                    info = ITEMS_DB.get(item['item_key'])
                    if info and info['type'] in ['artifact', 'acc']: 
                        acc_count += item['quantity']

                if acc_count >= 20:
                    await query.answer(f"⛔ ПРЕДЕЛ! (Макс 20 аксессуаров).", show_alert=True)
                    return CRAFT_MENU

            # Проверка золота
            char = database.get_character(user_id)
            if char['gold'] < recipe['cost']:
                await query.answer(f"⚠️ Не хватает золота! Нужно {recipe['cost']}g", show_alert=True)
                return CRAFT_MENU
            
            # Проверка материалов
            inv_dict = {i['item_key']: i['quantity'] for i in items}
            for mat, amt in recipe['mats'].items():
                if inv_dict.get(mat, 0) < amt:
                    mat_name = ITEMS_DB.get(mat, {'name': mat})['name']
                    await query.answer(f"⚠️ Не хватает: {mat_name}", show_alert=True)
                    return CRAFT_MENU
            
            # Списание и выдача
            database.add_gold(user_id, -recipe['cost']) # Списываем золото
            for mat, amt in recipe['mats'].items():
                database.remove_item(user_id, mat, amt)

            res, msg = database.buy_item(user_id, recipe['result'], result_item['type'], result_item['name'], 0, result_item.get('effect', 0))
            # Цена 0 в buy_item, т.к. мы золото уже списали выше вручную, чтобы проверить его ДО списания ресурсов
            
            await query.answer(f"✅ Создано: {result_item['name']}", show_alert=True)
            
            # Возвращаемся в ту же категорию, чтобы было удобно
            # Определяем категорию по типу созданного предмета
            cat_back = 'consumables'
            if target_type in ['weapon', 'magic_weapon']: cat_back = 'weapon'
            elif target_type in ['heavy_armor', 'light_armor', 'magic_armor']: cat_back = 'armor'
            
            await show_craft_category(query, user_id, cat_back)

        except Exception as e:
            print(f"CRAFT ERROR: {e}")
            await query.answer("Ошибка крафта.", show_alert=True)
            
    return CRAFT_MENU
    
async def render_inventory_category(query, user_id, cat):
    """Отрисовывает конкретную вкладку инвентаря"""
    try:
        items = database.get_inventory(user_id)
        
        # Заголовки разделов
        headers = {
            'equip': "⚔️ ВАШЕ СНАРЯЖЕНИЕ",
            'food': "🧪 ПРИПАСЫ (ЕДА И ЗЕЛЬЯ)",
            'mat': "🧱 МАТЕРИАЛЫ И РЕСУРСЫ",
            'acc': "💍 АКСЕССУАРЫ И ПРОЧЕЕ"
        }
        
        # Определяем, какие типы предметов показывать в какой категории
        types_map = {
            'equip': ['weapon', 'magic_weapon', 'heavy_armor', 'light_armor', 'magic_armor','agi_weapon'],
            'food': ['food', 'potion', 'buff_potion'],
            'mat': ['material'],
            'acc': ['artifact', 'acc', 'combat_item']
        }
        
        target_types = types_map.get(cat, [])
        
        txt = f"*{headers.get(cat, 'РЮКЗАК')}*\n━━━━━━━━━━━━━━━━\n"
        kb = []
        has_items = False

        for i in items:
            info = ITEMS_DB.get(i['item_key'])
            if not info: continue
            
            # Если тип предмета не подходит для этой категории — пропускаем
            if info.get('type') not in target_types:
                continue
                
            has_items = True
            
            # --- ОТОБРАЖЕНИЕ ---
            # Если это еда/зелье - делаем кнопку "Использовать"
            if cat == 'food':
                btn_txt = f"{info['name']} (x{i['quantity']})"
                # Для баффов пишем подсказку в кнопке, или просто даем использовать
                kb.append([InlineKeyboardButton(f"🍽 {btn_txt}", callback_data=f"use_{i['item_key']}")])
            else:
                # Для остальных (броня, ресурсы) — просто красивый список текстом
                # Чтобы не забивать чат кнопками
                txt += f"▪️ *{info['name']}* (x{i['quantity']})\n"

        if not has_items:
            txt += "\n_(В этом кармане пусто)_"
        
        if cat == 'food' and has_items:
            txt += "\n_Нажмите на предмет, чтобы использовать._"

        # Кнопка возврата к категориям
        kb.append([InlineKeyboardButton("🔙 Назад к категориям", callback_data='inventory')])
        
        # Обновляем сообщение (оставляем картинку инвентаря)
        await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['inventory'], caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))
    
    except Exception as e:
        print(f"Inv Render Error: {e}")
        await query.answer("Ошибка отображения инвентаря", show_alert=True)


async def inventory_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    
    # 1. КНОПКА НАЗАД В ДЕРЕВНЮ
    if data == 'back_to_main':
        await query.answer()
        await safe_edit(query, text="В деревне", media=InputMediaPhoto(IMAGE_URLS['village'], caption="В деревне", parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
        return MAIN_MENU

    # 2. ГЛАВНОЕ МЕНЮ ИНВЕНТАРЯ (ВЫБОР КАТЕГОРИИ)
    elif data == 'inventory':
        await query.answer()
        
        # Считаем предметы для красоты на кнопках
        items = database.get_inventory(user_id)
        c_equip = 0
        c_food = 0
        c_mat = 0
        c_acc = 0
        
        for i in items:
            itype = ITEMS_DB.get(i['item_key'], {}).get('type', 'unknown')
            if itype in ['weapon', 'magic_weapon', 'heavy_armor', 'light_armor', 'magic_armor','agi_weapon']: c_equip += 1
            elif itype in ['food', 'potion', 'buff_potion']: c_food += 1
            elif itype == 'material': c_mat += 1
            elif itype in ['artifact', 'acc', 'combat_item']: c_acc += 1

        txt = "🎒 *РЮКЗАК ГЕРОЯ*\n\nВ вашем мешке слишком много всего. Какой карман проверить?"

        kb = [
            [InlineKeyboardButton(f"⚔️ Снаряжение ({c_equip})", callback_data='inv_cat_equip')],
            [InlineKeyboardButton(f"🧪 Еда и Зелья ({c_food})", callback_data='inv_cat_food')],
            [InlineKeyboardButton(f"🧱 Ресурсы ({c_mat})", callback_data='inv_cat_mat')],
            [InlineKeyboardButton(f"💍 Аксессуары ({c_acc})", callback_data='inv_cat_acc')],
            [InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]
        ]
        
        await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['inventory'], caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))
        return INVENTORY_MENU

    # 3. ПЕРЕХОД В КАТЕГОРИЮ
    elif data.startswith('inv_cat_'):
        await query.answer()
        cat = data.split('_')[2] # equip, food, mat, acc
        await render_inventory_category(query, user_id, cat)
        return INVENTORY_MENU

    # 4. ИСПОЛЬЗОВАНИЕ ПРЕДМЕТА
    elif data.startswith('use_'):
        try:
            item_key = data.split('_', 1)[1]
            item_info = ITEMS_DB.get(item_key)
            
            if not item_info:
                await query.answer("Ошибка: предмет не найден.", show_alert=True)
            
            # Проверка типа (можно ли юзать)
            elif item_info['type'] not in ['potion', 'food', 'buff_potion']:
                await query.answer("Это нельзя использовать здесь.", show_alert=True)
            
            else:
                # Если это бафф — предупреждаем, что лучше в бою
                if item_info['type'] == 'buff_potion':
                     await query.answer("⚠️ Зелья силы/защиты лучше пить прямо в бою!", show_alert=True)
                     return INVENTORY_MENU

                # Логика лечения/маны
                char = database.get_character(user_id)
                effect = item_info.get('effect', 0)
                
                # Определяем, что восстанавливаем
                is_mana = 'mana' in item_key or 'mp' in item_key or 'void_nrg' in item_key
                used = False
                
                if is_mana:
                    if char['mana'] >= char['max_mana']:
                        await query.answer("Мана полная!", show_alert=True)
                    else:
                        new_mp = min(char['max_mana'], char['mana'] + effect)
                        database.update_character_stats(user_id, mana=new_mp)
                        used = True
                        await query.answer(f"🌀 Выпито: {item_info['name']} (+{effect} MP)", show_alert=True)
                else:
                    if char['health'] >= char['max_health']:
                        await query.answer("Здоровье полное!", show_alert=True)
                    else:
                        new_hp = min(char['max_health'], char['health'] + effect)
                        database.update_character_stats(user_id, health=new_hp)
                        used = True
                        await query.answer(f"❤️ Съедено: {item_info['name']} (+{effect} HP)", show_alert=True)

                if used:
                    # Удаляем 1 шт
                    database.remove_item(user_id, item_key, 1)
                    # Обновляем текущую категорию (еда), чтобы показать актуальное кол-во
                    await render_inventory_category(query, user_id, 'food')

        except Exception as e:
            print(f"Use Item Error: {e}")
            await query.answer("Сбой использования.", show_alert=True)
            
    return INVENTORY_MENU



async def show_top_players(query, user_id, page=1):
    limit = 10
    offset = (page - 1) * limit
    top_players = database.get_top_players(limit, offset)
    
    top_text = f"🏆 *ЛЕГЕНДЫ ЭТОГО МИРА (Страница {page}/5)*\n━━━━━━━━━━━━━━━━\n"
    
    if not top_players:
        top_text += "\n_Здесь пока никого нет..._"
    
    race_names = {
        'human': 'Человек',
        'elf': 'Эльф',
        'dwarf': 'Дварф',
        'orc': 'Орк',
        'vampire': 'Вампир',
        'lizardman': 'Ящеролюд',
        'frogman': 'Жаболюд',
        'leprechaun': 'Лепрекон', # <--- ДОБАВИЛИ
        'undead': 'Нежить'
    }
    
    for i, player in enumerate(top_players, 1):
        # Настоящий номер в топе (например: 10 + 1 = 11-е место)
        rank_num = i + offset 
        
        name = player['character_name'].replace('_', '\\_').replace('*', '\\*')
        lvl = player['level']
        race_key = player['race']
        race_name = race_names.get(race_key, 'Неизвестно')
        bosses = player.get('boss_kills', 0)
        
        clan_name = player.get('clan_name')
        if clan_name:
            safe_clan_name = clan_name.replace('_', '\\_').replace('*', '\\*')
            clan_tag = f" *[{safe_clan_name}]* "
        else:
            clan_tag = " "
        
        # Медали только для первой тройки
        if rank_num == 1: medal = "🥇"
        elif rank_num == 2: medal = "🥈"
        elif rank_num == 3: medal = "🥉"
        else: medal = f"*{rank_num}.*"
        
        top_text += f"{medal}{clan_tag}*{name}*\n   └ 🎭 {race_name} | ⭐ {lvl} ур.\n   └ ☠️ Убито боссов: {bosses}\n\n"
        
    kb = []
    
    # --- КНОПКИ ПАГИНАЦИИ (Вперед / Назад) ---
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton("⬅️ Назад", callback_data=f'top_players_{page-1}'))
    
    # Показываем кнопку "Вперед" только если мы не на 5-й странице и текущая страница полная (есть 10 человек)
    if page < 5 and len(top_players) == limit:
        nav_row.append(InlineKeyboardButton("Вперед ➡️", callback_data=f'top_players_{page+1}'))
        
    if nav_row:
        kb.append(nav_row)
        
    kb.append([InlineKeyboardButton("🔙 Назад в меню", callback_data='back_to_main')])
    
    await safe_edit(
        query, 
        text=top_text, 
        media=InputMediaPhoto(IMAGE_URLS['village'], caption=top_text, parse_mode='Markdown'), 
        keyboard=InlineKeyboardMarkup(kb)
    )

async def show_top_clans(query, user_id):
    clans = database.get_all_clans()
    
    if not clans:
        top_text = "🛡 *ТОП КЛАНОВ*\n\nВ этом мире еще не основано ни одного клана. Станьте первым!"
    else:
        top_text = "🛡 *ТОП КЛАНОВ ЭТОГО МИРА*\n━━━━━━━━━━━━━━━━\n"
        for i, c in enumerate(clans, 1):
            # Очищаем названия от спецсимволов для Markdown
            name = c['name'].replace('_', '\\_').replace('*', '\\*')
            owner_name = c.get('owner_name', 'Неизвестный').replace('_', '\\_').replace('*', '\\*')
            members = c['members_count']
            
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"*{i}.*"
            
            # Собираем красивую строчку с лидером и участниками
            top_text += f"{medal} *[{name}]* 🏆 {c.get('raid_points', 0)} очков\n   ├ 👑 Владыка: {owner_name}\n   └ 👥 Участников: {members}\n\n"
            
    kb = [[InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]]
    
    await safe_edit(
        query, 
        text=top_text, 
        media=InputMediaPhoto(IMAGE_URLS['castle'], caption=top_text, parse_mode='Markdown'), 
        keyboard=InlineKeyboardMarkup(kb)
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🆘 *Книга Знаний*\n\n"
        "🏰 **Основные места:**\n"
        "• ⚔️ **Битва** — Сражения за золото, опыт и редкий лут.\n"
        "• 🛍 **Лавка** — Покупка снаряжения и зелий.\n"
        "• 🛠 **Кузница** — Создание мощных предметов из ресурсов.\n"
        "• 📜 **Гильдия** — Ежедневные задания. Обновляются раз в 24 часа. Можно обновить платно, если задания слишком сложные.\n\n"
        
        "✨ **БОЕВЫЕ СПОСОБНОСТИ:**\n"
        "У каждой расы на *10, 25 и 40 уровне* открываются уникальные активные навыки. Ищите кнопку «💫 Способности» в бою.\n\n"
        
        "🧝‍♀️ **ОСОБЕННОСТЬ ЭЛЬФОВ:**\n"
        "Эльфы владеют «Магией Древних»:\n"
        "1. В Главном Меню выберите школу (Солнце, Луна или Звезды).\n"
        "2. Выберите активное заклинание.\n"
        "3. В бою кнопка **«🔮 Магия»** будет использовать именно его!\n"
        "_(Заклинания открываются на 1, 15 и 30 ур.)_\n\n"

        "⚠️ **Советы выживания:**\n"
        "• Здоровье восстанавливается медленно. Купите **Зелья** (🧪) в лавке!\n"
        "• Не нападайте на Боссов (☠️), пока не откроете первые способности."
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
async def alchemy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    char = database.get_character(user_id)
    
    if not char: return

    # 1. Проверка Ранга (Нужен минимум D)
    ranks_order = ['E', 'D', 'C', 'B', 'A', 'S']
    if ranks_order.index(char['rank']) < 1: # 0 это E, 1 это D
        await update.message.reply_text("🌿 Травник смотрит на вас: «Подрасти, малыш. Я работаю только с опытными (Ранг D+)».")
        return

    # 2. Проверка постройки
    is_built = database.check_building(user_id, 'building_alchemy')
    
    if not is_built:
        # Меню постройки (ЦЕНА 5000)
        txt = ("🏚 **СТАРАЯ ХИЖИНА**\n\n"
               "В деревню прибыл Травник. Он готов варить для вас мощные зелья, но ему нужна лаборатория.\n\n"
               "💰 **Цена постройки:** 5000 золота\n"
               "🔨 **Требуется:** Ранг D")
        
        kb = [[InlineKeyboardButton("🔨 Построить Лавку (5000g)", callback_data='build_alchemy')]]
        await update.message.reply_photo(IMAGE_URLS['village'], caption=txt, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
    else:
        # Меню алхимии (Показываем категории)
        await show_alchemy_menu(update, user_id)
        
async def build_alchemy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    char = database.get_character(user_id)
    
    # ПРОВЕРКА НА 5000 ЗОЛОТА
    if char['gold'] >= 5000:
        database.add_gold(user_id, -5000)
        database.build_building(user_id, 'building_alchemy')
        await query.answer("✅ Лавка построена!", show_alert=True)
        await show_alchemy_menu(query, user_id) # Сразу открываем меню
    else:
        await query.answer("❌ Не хватает золота (нужно 5000g)", show_alert=True)

async def show_alchemy_menu(source, user_id):
    """Главное меню алхимии с выбором ранга"""
    char = database.get_character(user_id)
    txt = (
        "🌿 **ЛАВКА ТРАВНИКА**\n"
        "_«Секреты трав открываются лишь терпеливым...»_\n\n"
        f"💰 Золото: {char['gold']}g\n"
        "Выберите уровень рецептов:"
    )
    
    kb = [
        [InlineKeyboardButton("🆕 Ранг E (Обычные)", callback_data='alch_cat_E')],
        [InlineKeyboardButton("🟢 Ранг D (Улучшенные)", callback_data='alch_cat_D')],
        [InlineKeyboardButton("🔵 Ранг C (Редкие)", callback_data='alch_cat_C')],
        [InlineKeyboardButton("🟣 Ранг B (Мистические)", callback_data='alch_cat_B')],
        [InlineKeyboardButton("🟠 Ранг A (Адские)", callback_data='alch_cat_A')],
        [InlineKeyboardButton("⚡ Ранг S (Эпические)", callback_data='alch_cat_S')],
        [InlineKeyboardButton("🔙 В деревню", callback_data='back_to_main')]
    ]
    
    if isinstance(source, Update):
        await source.message.reply_photo(IMAGE_URLS['village'], caption=txt, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
    else:
        await safe_edit(source, text=txt, media=InputMediaPhoto(IMAGE_URLS['village'], caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))

async def render_alchemy_category(query, user_id, rank):
    """Отрисовка рецептов выбранного ранга"""
    items = database.get_inventory(user_id)
    inv_dict = {i['item_key']: i['quantity'] for i in items}
    char = database.get_character(user_id)
    
    txt = f"⚗️ **РЕЦЕПТЫ (РАНГ {rank})**\n_Ваше золото: {char['gold']}g_\n━━━━━━━━━━━━━━━━\n"
    kb = []
    found = False
    
    for key, recipe in ALCHEMY_RECIPES.items():
        res_item = ITEMS_DB.get(recipe['result'])
        # Фильтруем рецепты по рангу (если ранг не указан, считаем его 'E')
        if not res_item or res_item.get('rank', 'E') != rank:
            continue
            
        found = True
        txt += f"🧪 *{res_item['name']}* (💰 {recipe['cost']}g)\n   _{res_item['desc']}_\n"
        
        mats_str = []
        can_brew = True
        for mat, amt in recipe['mats'].items():
            m_name = ITEMS_DB.get(mat, {'name': mat})['name']
            u_amt = inv_dict.get(mat, 0)
            mark = "✅" if u_amt >= amt else "❌"
            if u_amt < amt: can_brew = False
            mats_str.append(f"{mark} {u_amt}/{amt} {m_name}")
        
        txt += "   " + ", ".join(mats_str) + "\n\n"
        
        # Кнопка зелёная, только если хватает ресурсов И золота
        if can_brew and char['gold'] >= recipe['cost']:
            kb.append([InlineKeyboardButton(f"⚗️ Варить {res_item['name']}", callback_data=f"brew_{key}")])
        else:
            kb.append([InlineKeyboardButton(f"❌ {res_item['name']} (Не хватает)", callback_data="ignore")])
            
    if not found:
        txt += "Для этого ранга пока нет известных рецептов.\n"
        
    kb.append([InlineKeyboardButton("🔙 Назад к рангам", callback_data='alchemy_main')])
    
    await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['village'], caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))


async def brew_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    
    recipe_key = data.split('_', 1)[1]
    recipe = ALCHEMY_RECIPES.get(recipe_key)
    
    if not recipe: return
    
    items = database.get_inventory(user_id)
    inv_dict = {i['item_key']: i['quantity'] for i in items}
    char = database.get_character(user_id)
    
    if char['gold'] < recipe['cost']:
        await query.answer("Не хватает золота!", show_alert=True); return

    for mat, amt in recipe['mats'].items():
        if inv_dict.get(mat, 0) < amt:
            await query.answer("Не хватает ингредиентов!", show_alert=True); return
            
    # Списание
    database.add_gold(user_id, -recipe['cost'])
    for mat, amt in recipe['mats'].items():
        database.remove_item(user_id, mat, amt)
        
    # Выдача
    res_item = ITEMS_DB[recipe['result']]
    database.buy_item(user_id, recipe['result'], res_item['type'], res_item['name'], 0, res_item.get('effect', 0))
    
    await query.answer(f"⚗️ Сварено: {res_item['name']}")
    
    # Возвращаемся в ту же категорию!
    rank = res_item.get('rank', 'E')
    await render_alchemy_category(query, user_id, rank)

# ==========================================
# === ФЕРМЕР И ПОВАР ===
# ==========================================

async def farm_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    char = database.get_character(user_id)
    
    # 1. Проверяем постройку фермы
    if not database.check_building(user_id, 'building_farm'):
        txt = "🌾 **ЗАБРОШЕННОЕ ПОЛЕ**\nЗдесь можно разбить грядки и нанять Фермера.\n💰 Цена: 2000g"
        kb = [[InlineKeyboardButton("🔨 Построить Ферму (2000g)", callback_data='build_farm')],
              [InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]]
        await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['village'], caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))
        return MAIN_MENU

    # 2. Статус фермы
    status = database.get_farm_status(user_id)
    kb = []
    txt = ""
    
    if status['state'] == 'idle':
        txt = "🌾 **ФЕРМА СВОБОДНА**\nЧто прикажете посадить, милорд?"
        ranks = ['E', 'D', 'C', 'B', 'A', 'S']
        for crop_key, conf in FARM_CONFIG.items():
            if ranks.index(char['rank']) >= ranks.index(conf['req_rank']):
                kb.append([InlineKeyboardButton(f"🌱 Посадить {conf['name']} ({conf['time_minutes']} мин)", callback_data=f"plant_{crop_key}")])
            else:
                kb.append([InlineKeyboardButton(f"🔒 {conf['name']} (Нужен ранг {conf['req_rank']})", callback_data="ignore")])
    else:
        start_time = status['start_time']
        if isinstance(start_time, str): start_time = datetime.fromisoformat(start_time)
            
        crop = FARM_CONFIG.get(status['crop_key'])
        if not crop: 
             database.finish_farming(user_id)
             await query.answer("Урожай погиб. Поле снова свободно.")
             return MAIN_MENU
             
        elapsed_minutes = (datetime.now() - start_time).total_seconds() / 60
        
        if elapsed_minutes >= crop['time_minutes']:
            txt = f"✅ **Урожай созрел!**\nВаша {crop['name']} готова к сбору."
            kb.append([InlineKeyboardButton("🧺 СОБРАТЬ УРОЖАЙ", callback_data='harvest_crop')])
        else:
            left = int(crop['time_minutes'] - elapsed_minutes)
            txt = f"⏳ **Растения зреют...**\nПосажено: {crop['name']}\nОсталось: {left} мин."
            kb.append([InlineKeyboardButton("🔄 Обновить грядки", callback_data='farm_menu')])

    # --- БЛОК ПАСЕКИ (Показывается всегда, независимо от грядок) ---
    has_apiary = database.check_building(user_id, 'building_apiary')
    if not has_apiary:
        kb.append([InlineKeyboardButton("🐝 Построить Пасеку (5000g)", callback_data='build_apiary')])
    else:
        kb.append([InlineKeyboardButton("🍯 Собрать мёд", callback_data='collect_honey')])
    # -------------------------------------------------------------

    kb.append([InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')])
    await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['village'], caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))
    return MAIN_MENU

# --- НОВЫЕ ФУНКЦИИ ПАСЕКИ ---
async def build_apiary_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    char = database.get_character(user_id)
    
    if char['gold'] >= 5000:
        database.add_gold(user_id, -5000)
        database.build_building(user_id, 'building_apiary')
        await query.answer("✅ Пасека построена! Пчелы начали трудиться.", show_alert=True)
        await farm_menu_handler(update, context)
    else:
        await query.answer("❌ Нужно 5000 золота!", show_alert=True)

async def collect_honey_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    try:
        last_time = database.get_honey_collection_time(user_id)
        now = datetime.now()
        
        cooldown_seconds = 14400 # 4 часа в секундах
        
        if last_time:
            if isinstance(last_time, str):
                last_time = datetime.fromisoformat(last_time)
            elapsed = (now - last_time).total_seconds()
        else:
            elapsed = cooldown_seconds + 1 # Если собирает первый раз
            
        if elapsed >= cooldown_seconds:
            # Выдаем мёд (указываем эффект 50, чтобы он лечил)
            amount = random.randint(1, 3)
            database.buy_item(user_id, 'honey_hp', 'potion', '🍯 Дикий мёд', 0, 50, amount=amount)
            database.update_honey_collection_time(user_id)
            
            await query.answer(f"🍯 Вы собрали свежий мёд: {amount} шт!", show_alert=True)
            await farm_menu_handler(update, context)
        else:
            # Считаем остаток времени
            left_seconds = cooldown_seconds - elapsed
            hours = int(left_seconds // 3600)
            minutes = int((left_seconds % 3600) // 60)
            await query.answer(f"⏳ Пчелы еще собирают нектар. Осталось: {hours}ч {minutes}м.", show_alert=True)
            
    except Exception as e:
        print(f"Honey Error: {e}")
        await query.answer("🔧 Ошибка сбора мёда. Перезапустите меню.", show_alert=True)

async def harvest_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    status = database.get_farm_status(user_id)
    if status['state'] != 'growing': return
    
    crop = FARM_CONFIG.get(status['crop_key'])
    if not crop: return
    
    amount = random.randint(crop['yield_min'], crop['yield_max'])
    item_data = ITEMS_DB.get(status['crop_key'])
    if not item_data: return
    
    item_name = item_data['name']
    
    # Добавляем предметы в цикле через buy_item, чтобы не ломать базу ручными запросами
    # Цена 0, так как мы их вырастили
    for _ in range(amount):
        database.buy_item(user_id, status['crop_key'], 'material', item_name, 0, 0)

    database.finish_farming(user_id)
    
    txt = f"🧺 **УРОЖАЙ СОБРАН!**\nВы получили: {item_name} (x{amount})"
    await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['village'], caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("🌾 Вернуться на ферму", callback_data='farm_menu')]]))

async def build_farm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    char = database.get_character(user_id)
    if char['gold'] >= 2000:
        database.add_gold(user_id, -2000)
        database.build_building(user_id, 'building_farm')
        await query.answer("✅ Ферма построена!", show_alert=True)
        await farm_menu_handler(update, context)
    else:
        await query.answer("❌ Нужно 2000 золота!", show_alert=True)

async def plant_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    # ИСПРАВЛЕНИЕ ЗДЕСЬ: добавляем единичку в split, 
    # чтобы 'plant_magic_bean' разбилось на 'plant' и 'magic_bean'
    crop_key = query.data.split('_', 1)[1] 
    
    database.start_farming(query.from_user.id, crop_key)
    await query.answer(f"🌱 Семена посажены!")
    await farm_menu_handler(update, context)

async def harvest_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    status = database.get_farm_status(user_id)
    if status['state'] != 'growing': return
    
    crop = FARM_CONFIG.get(status['crop_key'])
    amount = random.randint(crop['yield_min'], crop['yield_max'])
    item_name = ITEMS_DB[status['crop_key']]['name']
    
    database.buy_item(user_id, status['crop_key'], 'material', item_name, 0, 0)
    # Добавляем нужное количество (первый раз добавился в buy_item)
    if amount > 1: database.buy_item(user_id, status['crop_key'], 'material', item_name, 0, 0) # Упрощенный костыль или прописать SQL

    # Корректное добавление нужного количества:
    conn = database.get_connection()
    c = conn.cursor()
    c.execute("UPDATE player_inventory SET quantity = quantity + %s WHERE user_id = %s AND item_key = %s", (amount-1, user_id, status['crop_key']))
    conn.commit()
    conn.close()

    database.finish_farming(user_id)
    
    txt = f"🧺 **УРОЖАЙ СОБРАН!**\nВы получили: {item_name} (x{amount})"
    await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['village'], caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup([[InlineKeyboardButton("🌾 Вернуться на ферму", callback_data='farm_menu')]]))


async def kitchen_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if not database.check_building(user_id, 'building_kitchen'):
        txt = "🍳 **РУИНЫ ТАВЕРНЫ**\nВосстановите кухню, чтобы Повар готовил вам сытную еду.\n💰 Цена: 3000g"
        kb = [[InlineKeyboardButton("🔨 Восстановить Кухню (3000g)", callback_data='build_kitchen')],
              [InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]]
        await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['village'], caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))
        return MAIN_MENU

    items = database.get_inventory(user_id)
    inv_dict = {i['item_key']: i['quantity'] for i in items}
    
    txt = "🍳 **ПОЛЕВАЯ КУХНЯ**\n_«Запах жареного мяса манит монстров... и героев.»_\n━━━━━━━━━━━━━━━━\n"
    kb = []
    
    for key, recipe in COOKING_RECIPES.items():
        res_item = ITEMS_DB.get(recipe['result'])
        if not res_item: continue
        txt += f"🍽 *{res_item['name']}*\n   _{res_item['desc']}_\n"
        
        mats_str = []
        can_cook = True
        for mat, amt in recipe['mats'].items():
            m_name = ITEMS_DB.get(mat, {'name': mat})['name']
            u_amt = inv_dict.get(mat, 0)
            mark = "✅" if u_amt >= amt else "❌"
            if u_amt < amt: can_cook = False
            mats_str.append(f"{mark} {u_amt}/{amt} {m_name}")
            
        txt += "   " + ", ".join(mats_str) + "\n\n"
        
        # Кнопка активна только если хватает ресурсов
        if can_cook:
            kb.append([InlineKeyboardButton(f"🍳 Готовить {res_item['name']}", callback_data=f"cook_{key}")])
        else:
            kb.append([InlineKeyboardButton(f"❌ {res_item['name']} (Нет продуктов)", callback_data="ignore")])

    kb.append([InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')])
    await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['village'], caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))
    return MAIN_MENU
    
async def build_kitchen_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    char = database.get_character(user_id)
    if char['gold'] >= 3000:
        database.add_gold(user_id, -3000)
        database.build_building(user_id, 'building_kitchen')
        await query.answer("✅ Кухня восстановлена!", show_alert=True)
        await kitchen_menu_handler(update, context)
    else:
        await query.answer("❌ Нужно 3000 золота!", show_alert=True)

async def cook_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    recipe_key = query.data.split('_', 1)[1]
    recipe = COOKING_RECIPES.get(recipe_key)
    if not recipe: return
    
    items = database.get_inventory(user_id)
    inv_dict = {i['item_key']: i['quantity'] for i in items}
    char = database.get_character(user_id)
    
    if char['gold'] < recipe['cost']:
        await query.answer("Не хватает золота на специи!", show_alert=True); return

    for mat, amt in recipe['mats'].items():
        if inv_dict.get(mat, 0) < amt:
            await query.answer("Не хватает продуктов!", show_alert=True); return
            
    database.add_gold(user_id, -recipe['cost'])
    for mat, amt in recipe['mats'].items():
        database.remove_item(user_id, mat, amt)
        
    res_item = ITEMS_DB[recipe['result']]
    database.buy_item(user_id, recipe['result'], res_item['type'], res_item['name'], 0, res_item.get('effect', 0))
    
    await query.answer(f"🍲 Приготовлено: {res_item['name']}")
    await kitchen_menu_handler(update, context)
# ==========================================
# === РЕИНКАРНАЦИЯ (УДАЛЕНИЕ ГЕРОЯ) ===
# ==========================================

async def rebirth_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    char = database.get_character(user_id)
    
    if not char:
        await update.message.reply_text("Духи не видят вас. Сначала создайте героя командой /start.")
        return

    txt = (
        "🔥 **РИТУАЛ ПЕРЕРОЖДЕНИЯ** 🔥\n\n"
        "Вы стоите у края Бездны. Шаг в неё уничтожит ваше нынешнее тело, но душа сможет переродиться в новом обличии.\n\n"
        "⚠️ **ВНИМАНИЕ:** Ваше золото, уровень, раса, постройки (Травник, Ферма) и инвентарь будут **НАВСЕГДА УДАЛЕНЫ**!\n\n"
        "Вы точно готовы?"
    )
    
    kb = [
        [InlineKeyboardButton("💀 ШАГНУТЬ В БЕЗДНУ (Удалить героя)", callback_data='confirm_rebirth')],
        [InlineKeyboardButton("🔙 ОТОЙТИ ОТ КРАЯ (Отмена)", callback_data='cancel_rebirth')]
    ]
    
    await update.message.reply_photo(
        photo=IMAGE_URLS['hell_gate'], 
        caption=txt, 
        parse_mode='Markdown', 
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def confirm_rebirth_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    # Подчищаем кэш боев на всякий случай
    if user_id in battle_sessions:
        del battle_sessions[user_id]
        
    success = database.delete_character(user_id)
    
    if success:
        txt = "Ваше тело обратилось в пепел... 💨\n\nНапишите /start, чтобы родиться заново."
        await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['dungeon'], caption=txt, parse_mode='Markdown'))
    else:
        await query.answer("Бездна отвергла вас (Ошибка БД).", show_alert=True)

async def cancel_rebirth_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer("Вы отступили от края.")
    
    # Возвращаем в деревню
    char = database.get_character(user_id)
    if char:
        await safe_edit(query, text="В деревне", media=InputMediaPhoto(IMAGE_URLS['village'], caption="В деревне", parse_mode='Markdown'), keyboard=get_main_menu_keyboard(user_id))
        return MAIN_MENU
# ==========================================
# === ИМПЕРСКИЙ БАНК (ДОНАТ ЧЕРЕЗ STARS) ===
# ==========================================

async def donate_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    char = database.get_character(user_id)
    
    txt = (
        "💎 *ИМПЕРСКИЙ БАНК*\n"
        "_Смотритель банка оценивающе смотрит на вас._\n\n"
        "Здесь вы можете обменять **Telegram Stars (⭐)** на золото.\n"
        "Это очень поможет развитию нашего проклятого мира!\n\n"
        f"Ваше золото: {char['gold']}g"
    )
    
    kb = []
    for k, v in DONATE_PACKAGES.items():
        # Кнопки с пакетами
        kb.append([InlineKeyboardButton(f"{v['name']} — {v['price']} ⭐", callback_data=f"buy_gold_{k}")])
        
    kb.append([InlineKeyboardButton("🔙 Выйти из банка", callback_data='back_to_main')])
    
    await safe_edit(query, text=txt, media=InputMediaPhoto(IMAGE_URLS['bank'], caption=txt, parse_mode='Markdown'), keyboard=InlineKeyboardMarkup(kb))
    return MAIN_MENU

async def send_gold_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() # Убираем часики
    
    user_id = query.from_user.id
    pack_key = query.data.split('_', 2)[2] # Получаем pack1, pack2...
    
    pack = DONATE_PACKAGES.get(pack_key)
    if not pack: return MAIN_MENU
    
    # ОТПРАВЛЯЕМ СЧЕТ (INVOICE)
    await context.bot.send_invoice(
        chat_id=query.message.chat_id,
        title=pack['name'],
        description=f"Мгновенное зачисление {pack['gold']} золотых монет на ваш аккаунт.",
        payload=f"gold_{user_id}_{pack_key}", # Секретная метка платежа
        provider_token="", # ПУСТАЯ СТРОКА ОБЯЗАТЕЛЬНА ДЛЯ TELEGRAM STARS
        currency="XTR",    # Код валюты Telegram Stars
        prices=[LabeledPrice("Telegram Stars", pack['price'])]
    )
    return MAIN_MENU

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отвечает Telegram, что мы готовы принять платеж"""
    query = update.pre_checkout_query
    if query.invoice_payload.startswith("gold_"):
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="Ошибка идентификации заказа.")

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает успешный платеж и начисляет золото"""
    payment = update.message.successful_payment
    payload = payment.invoice_payload
    
    if payload.startswith("gold_"):
        # ИСПРАВЛЕНИЕ ЗДЕСЬ: добавляем двойку в split('_', 2)
        # Теперь 'gold_12345_pack_mini' разобьется ровно на 3 части: 'gold', '12345' и 'pack_mini'
        parts = payload.split('_', 2)
        user_id = int(parts[1])
        pack_key = parts[2]
        
        pack = DONATE_PACKAGES.get(pack_key)
        if pack:
            database.add_gold(user_id, pack['gold'])
            
            # Отправляем радостное сообщение
            success_txt = (
                "🎉 *ОПЛАТА УСПЕШНО ПРОШЛА!*\n\n"
                f"Смотритель банка с уважением передает вам тугой мешок.\n"
                f"💰 **+{pack['gold']} золота** зачислено на ваш счет!\n\n"
                "Огромное спасибо за поддержку развития игры! ❤️"
            )
            await update.message.reply_photo(IMAGE_URLS['bank'], caption=success_txt, parse_mode='Markdown')
        else:
            # На случай непредвиденных сбоев, чтобы бот не молчал
            await update.message.reply_text("⚠️ Оплата прошла, но пакет не распознан. Пожалуйста, обратитесь к администратору.")
async def enter_gift_gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    target_id = int(context.user_data.get('gift_target', 0))
    char = database.get_character(user_id)
    
    try:
        amount = int(update.message.text.strip())
        if amount <= 0: raise ValueError
    except:
        await update.message.reply_text("Введите корректное число (больше нуля):")
        return CLAN_GIFT_GOLD_ENTER

    success, msg = database.transfer_gold(user_id, target_id, amount)
    
    if success:
        try:
            # Пытаемся уведомить получателя в личку!
            await context.bot.send_message(chat_id=target_id, text=f"🎁 **Вам посылка!**\nСоклановец {char['character_name']} прислал вам {amount} золота!")
        except: pass
        await update.message.reply_text(f"✅ Вы успешно отправили {amount}g!", reply_markup=get_main_menu_keyboard(user_id))
    else:
        await update.message.reply_text(f"❌ Ошибка: {msg}", reply_markup=get_main_menu_keyboard(user_id))
        
    return MAIN_MENU

async def enter_gift_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    target_id = int(context.user_data.get('gift_target', 0))
    item_key = context.user_data.get('gift_item')
    
    char = database.get_character(user_id)
    target_char = database.get_character(target_id) # Получаем данные того, кому дарим
    item_info = ITEMS_DB.get(item_key)
    
    # === НОВАЯ ПРОВЕРКА РАНГА ===
    item_rank = item_info.get('rank', 'E')
    ranks_order = ['E', 'D', 'C', 'B', 'A', 'S']
    
    try: item_rank_idx = ranks_order.index(item_rank)
    except: item_rank_idx = 0
    
    try: target_rank_idx = ranks_order.index(target_char['rank'])
    except: target_rank_idx = 0

    if target_rank_idx < item_rank_idx:
        await update.message.reply_text(
            f"🔒 **Магия отвергает этот дар!**\n"
            f"У соклановца {target_char['character_name']} слишком низкий ранг для {item_info['name']}.\n"
            f"_Требуется ранг: {item_rank}_", 
            reply_markup=get_main_menu_keyboard(user_id)
        )
        return MAIN_MENU
    # ============================
    
    try:
        amount = int(update.message.text.strip())
        if amount <= 0: raise ValueError
    except:
        await update.message.reply_text("Введите корректное число (больше нуля):")
        return CLAN_GIFT_ITEM_ENTER

    success, msg = database.transfer_item(user_id, target_id, item_key, amount, item_info)
    
    if success:
        try:
            # Уведомляем получателя
            await context.bot.send_message(chat_id=target_id, text=f"📦 **Вам посылка!**\nСоклановец {char['character_name']} прислал вам: {item_info['name']} (x{amount})")
        except: pass
        await update.message.reply_text(f"✅ Предметы успешно отправлены!", reply_markup=get_main_menu_keyboard(user_id))
    else:
        await update.message.reply_text(f"❌ Ошибка: {msg}", reply_markup=get_main_menu_keyboard(user_id))
        
    return MAIN_MENU
async def enter_buy_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    item_key = context.user_data.get('buy_item_key')
    
    if not item_key:
        await update.message.reply_text("Ошибка покупки. Вернитесь в магазин.", reply_markup=get_main_menu_keyboard(user_id))
        return MAIN_MENU
        
    item = ITEMS_DB.get(item_key)
    
    try:
        amount = int(update.message.text.strip())
        if amount <= 0: raise ValueError
    except:
        await update.message.reply_text("Пожалуйста, введите корректное число (больше нуля):")
        return SHOP_BUY_QUANTITY
        
    char = database.get_character(user_id)
    total_price = item['price'] * amount
    
    # Проверка золота
    if char['gold'] < total_price:
        await update.message.reply_text(
            f"💸 У вас не хватает золота!\n"
            f"Вы пытаетесь купить {amount} шт. за {total_price}g, а у вас всего {char['gold']}g.\n\n"
            f"_Введите число поменьше:_"
        )
        return SHOP_BUY_QUANTITY
        
    # Защита от сумасшедших чисел, чтобы не сломать базу
    if amount > 10000:
        await update.message.reply_text("Ого! Торговец не может продать больше 10,000 штук за раз. Введите число поменьше:")
        return SHOP_BUY_QUANTITY
        
    # Проводим покупку
    res, msg = database.buy_item(user_id, item_key, item['type'], item['name'], item['price'], item.get('effect', 0), amount=amount)
    
    if res:
        await update.message.reply_text(f"{msg}", reply_markup=get_main_menu_keyboard(user_id))
    else:
        await update.message.reply_text(f"❌ Ошибка: {msg}", reply_markup=get_main_menu_keyboard(user_id))
        
    # Очищаем временную память
    context.user_data.pop('buy_item_key', None)
    return MAIN_MENU
# ==========================================
# === ТРУЩОБЫ (АЗАРТНАЯ ИГРА) ===
# ==========================================

async def slums_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    char = database.get_character(user_id)
    
    if not char:
        return

    txt = (
        "🏚 *ТРУЩОБЫ ГРЕШНИКОВ*\n\n"
        "Грязь, вонь и крики оборванцев. В темном переулке на ящике сидит человек в капюшоне. "
        "Он ловко перекатывает костяной шарик под тремя черепами.\n\n"
        f"👤 *Шулер:* _«Подходи, герой! Угадай, где шарик, и я умножу твою ставку в 50 раз! Всё абсолютно честно!»_\n\n"
        f"💰 Ваше золото: {char['gold']}g"
    )

    kb = [
        [InlineKeyboardButton("🎲 Сыграть в черепа (Ставка)", callback_data='slums_bet_start')],
        [InlineKeyboardButton("🔙 Уйти от греха подальше", callback_data='back_to_main')]
    ]

    # Если вызвано командой /slums
    if update.message:
        await update.message.reply_photo(
            photo=IMAGE_URLS.get('slums', IMAGE_URLS['village']), 
            caption=txt, 
            parse_mode='Markdown', 
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return MAIN_MENU # <--- ВОТ ЭТОГО НЕ ХВАТАЛО!
        
    # Если вызвано кнопкой возврата
    elif update.callback_query:
        try: await update.callback_query.answer()
        except: pass
        await safe_edit(
            update.callback_query, 
            text=txt, 
            media=InputMediaPhoto(IMAGE_URLS.get('slums', IMAGE_URLS['village']), caption=txt, parse_mode='Markdown'), 
            keyboard=InlineKeyboardMarkup(kb)
        )
        return MAIN_MENU



async def slums_bet_start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try: await query.answer()
    except: pass
    user_id = query.from_user.id

    await context.bot.send_message(
        chat_id=user_id, 
        text="💰 Сколько золота вы хотите поставить на кон?\n\n_Напишите сумму в чат (или введите 0 для отмены):_", 
        parse_mode='Markdown'
    )
    return SLUMS_BET_ENTER

async def enter_slums_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    char = database.get_character(user_id)

    try:
        bet = int(update.message.text.strip())
    except:
        await update.message.reply_text("Шулер хмурится: _«Я принимаю только золотые монеты. Назови нормальное число!»_", parse_mode='Markdown')
        return SLUMS_BET_ENTER

    if bet <= 0:
        await update.message.reply_text("Вы махнули рукой и отошли от бочки.", reply_markup=get_main_menu_keyboard(user_id))
        return MAIN_MENU

    if char['gold'] < bet:
        await update.message.reply_text(f"Шулер смеется: _«У тебя нет столько монет, оборванец! В карманах всего {char['gold']}g!»_\nВведите число поменьше:", parse_mode='Markdown')
        return SLUMS_BET_ENTER

    # Списываем ставку сразу
    database.add_gold(user_id, -bet)

    # --- ЖЕСТОКАЯ РУЛЕТКА (ШАНС 1 ИЗ 100) ---
    roll = random.randint(1, 100)

    # Загадываем число 42. Только если выпадет 42 - игрок побеждает.
    if roll == 42: 
        win_amount = bet * 50
        database.add_gold(user_id, win_amount)
        txt = (
            f"🎉 *НЕВЕРОЯТНО!*\n\n"
            f"Вы уверенно тыкаете пальцем в правый череп. Шулер бледнеет, поднимает его, и там... костяной шарик!\n"
            f"Он с проклятиями отсчитывает вам огромный выигрыш.\n\n"
            f"💰 **+{win_amount}g!**"
        )
    else:
        txt = (
            f"💀 *ОБМАН!*\n\n"
            f"Вы поднимаете центральный череп... Пусто.\n"
            f"Шулер мерзко хихикает и сгребает ваше золото себе за пазуху: _«Не повезло, друг! Попробуешь еще?»_\n\n"
            f"💸 **-{bet}g**"
        )

    await update.message.reply_photo(
        photo=IMAGE_URLS.get('slums', IMAGE_URLS['village']), 
        caption=txt, 
        parse_mode='Markdown', 
        reply_markup=get_main_menu_keyboard(user_id)
    )
    return MAIN_MENU
# --- НАСТРОЙКА БЫСТРОГО МЕНЮ TELEGRAM ---
async def setup_bot_commands(application: Application):
    await application.bot.set_my_commands([
        BotCommand("slums", "🏚 Трущобы (Азартная игра)"),
        BotCommand("start", "🏠 В деревню (Главное меню)"),
        BotCommand("alchemy", "⚗️ Лавка Травника"),
        BotCommand("reset", "💀 Реинкарнация (Сброс героя)")
    ])
def main():
    database.init_db()
    database.init_clans_table()
    database.migrate_expeditions_table() 
    if hasattr(database, 'init_companion_table'):
        database.init_companion_table()
    if hasattr(database, 'init_farm_table'):
        database.init_farm_table()
    
    app = Application.builder().token(TOKEN).post_init(setup_bot_commands).build()
    
    app.add_handler(CommandHandler('alchemy', alchemy_command))
    app.add_handler(CommandHandler('reset', rebirth_command))
    
    app.add_handler(CallbackQueryHandler(confirm_rebirth_handler, pattern='^confirm_rebirth$'))
    app.add_handler(CallbackQueryHandler(cancel_rebirth_handler, pattern='^cancel_rebirth$'))

    conv = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CommandHandler('slums', slums_command)
        ],
        states={
            CHOOSE_RACE: [CallbackQueryHandler(choose_race, pattern='^race_')],
            ENTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_name)],
            
            MAIN_MENU: [
                # --- ЖЕЛЕЗОБЕТОННЫЙ ПЕРЕХВАТ КОМАНДЫ ---
                CommandHandler('slums', slums_command),
                CallbackQueryHandler(herbalist_menu_handler, pattern='^herbalist_menu$'),
                CallbackQueryHandler(build_alchemy_handler, pattern='^build_alchemy$'),
                CallbackQueryHandler(brew_handler, pattern='^brew_'),
                CallbackQueryHandler(start_expedition_handler, pattern='^send_exp_'),
                CallbackQueryHandler(claim_loot_handler, pattern='^claim_exp_loot$'),
                CallbackQueryHandler(clan_hub_handler, pattern='^clans_menu$'),
                CallbackQueryHandler(farm_menu_handler, pattern='^farm_menu$'),
                CallbackQueryHandler(build_farm_handler, pattern='^build_farm$'),
                CallbackQueryHandler(build_apiary_handler, pattern='^build_apiary$'),
                CallbackQueryHandler(collect_honey_handler, pattern='^collect_honey$'),
                CallbackQueryHandler(plant_handler, pattern='^plant_'),
                CallbackQueryHandler(harvest_handler, pattern='^harvest_crop$'),
                
                CallbackQueryHandler(kitchen_menu_handler, pattern='^kitchen_menu$'),
                CallbackQueryHandler(build_kitchen_handler, pattern='^build_kitchen$'),
                CallbackQueryHandler(cook_handler, pattern='^cook_'),
                CallbackQueryHandler(slums_command, pattern='^slums_menu$'),
                CallbackQueryHandler(slums_bet_start_handler, pattern='^slums_bet_start$'),
                CallbackQueryHandler(fishing_menu_handler, pattern='^fishing_menu$'),
                CallbackQueryHandler(build_pier_handler, pattern='^build_pier$'),
                CallbackQueryHandler(catch_fish_handler, pattern='^catch_fish$'),
                CallbackQueryHandler(donate_menu_handler, pattern='^donate_menu$'),
                CallbackQueryHandler(send_gold_invoice, pattern='^buy_gold_'),
                CallbackQueryHandler(main_menu_handler)
            ],
            
            BATTLE_MENU: [CallbackQueryHandler(battle_menu_handler)],
            IN_BATTLE: [CallbackQueryHandler(battle_action_handler)],
            GUILD_MENU: [CallbackQueryHandler(guild_menu_handler)],
            SHOP_MENU: [CallbackQueryHandler(shop_handler)],
            CRAFT_MENU: [CallbackQueryHandler(craft_handler)],
            LEVEL_UP: [CallbackQueryHandler(level_up_handler)],
            INVENTORY_MENU: [CallbackQueryHandler(inventory_menu_handler)],
            CLAN_MENU: [
                CallbackQueryHandler(clan_raid_hub_handler, pattern='^clan_raid_hub$'),
                CallbackQueryHandler(raid_summon_handler, pattern='^raid_summon$'),
                CallbackQueryHandler(raid_attack_handler, pattern='^raid_attack$'),
                CallbackQueryHandler(clan_action_handler)
            ],
            CLAN_CREATE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_clan_name)],
            CLAN_CREATE_ICON: [
                MessageHandler(filters.PHOTO, enter_clan_icon),
                MessageHandler(filters.ALL & ~filters.COMMAND, enter_clan_icon)
            ],
            CLAN_GIFT_GOLD_ENTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_gift_gold)],
            CLAN_GIFT_ITEM_ENTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_gift_item)],
            SHOP_BUY_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_buy_quantity)],
            SLUMS_BET_ENTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_slums_bet)],
        },
        fallbacks=[
            CommandHandler('start', start),
            CommandHandler('slums', slums_command)
        ]
    )
    
    app.add_handler(conv)
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_text))
    app.add_handler(CallbackQueryHandler(unknown_callback))
    
    print("⚔️ Бот Темного Фентези перезапущен! Нажмите /start")
    app.run_polling()
    
if __name__ == '__main__':
    main()
