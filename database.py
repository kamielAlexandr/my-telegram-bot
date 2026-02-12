import os
import logging
import random
import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    ContextTypes, ConversationHandler, MessageHandler, filters
)
# Импортируем функции из database.py
import database

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния
CHOOSE_RACE, ENTER_NAME, MAIN_MENU, BATTLE_MENU, IN_BATTLE, SHOP_MENU, LEVEL_UP, INVENTORY_MENU = range(8)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
battle_sessions = {}

# Константы (Картинки, Враги, Локации, Предметы) оставляем в Bot.py, так как они нужны для UI
IMAGE_URLS = {
    'human': 'https://i126.fastpic.org/thumb/2026/0130/2c/_d2515d33e45fa7ffb5246cacabdaba2c.jpeg',
    'elf': 'https://i126.fastpic.org/thumb/2026/0130/81/_d3d94be5aa45b9239aeb5adc41443081.jpeg',
    'dwarf': 'https://i126.fastpic.org/thumb/2026/0130/5b/_c188fac4eb6d205bd9fc0486c9b9355b.jpeg',
    'orc': 'https://i126.fastpic.org/thumb/2026/0130/20/_b8c1f666bd21bb415e8fb35145eb3e20.jpeg',
    'village': 'https://img.freepik.com/premium-photo/tavern-like-game_808092-1770.jpg',
    'forest': 'https://img.freepik.com/premium-photo/ancient-forest-ai-generated_1127-13930.jpg',
    'shop': 'https://img.freepik.com/premium-photo/tavern-like-game_808092-1770.jpg',
    # ... остальные URL из твоего кода ...
    'training_camp': 'https://img1.liveinternet.ru/images/attach/b/2/1/726/1726838_full0011.jpg',
    'dungeon': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSTZd9YHDcPOGmD8ezmHB0xD-HfA9O7OpgVyA&s',
    'castle': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTrAoGzKjgZxurLbxZ_Dyhtkm1gBqMUMtA87w&s',
    'hell_gate': 'https://abrakadabra.fun/uploads/posts/2022-01/1642490542_3-abrakadabra-fun-p-temnii-mag-art-5.jpg',
    'throne_god': 'https://abrakadabra.fun/uploads/posts/2022-03/1646721873_1-abrakadabra-fun-p-pauk-fantezi-art-1.jpg'
}

# Враги (сокращенно для примера, используй свой полный список)
BASE_ENEMIES = {
    'wolf': {'name': '🐺 Бешеный Волк', 'base_health': 35, 'rank': 'E', 'difficulty': 'easy', 'damage_type': 'physical', 'min_physical_damage': 5, 'max_physical_damage': 8, 'exp': 12, 'gold': 8, 'image': 'https://i.pinimg.com/736x/9f/8e/25/9f8e2507aceaa217060d249c308e2a13.jpg', 'abilities': ['basic_attack']},
    # ... сюда вставь весь словарь BASE_ENEMIES из твоего кода ...
}

LOCATIONS = {
    'E': {'name': '🎪 Тренировочный лагерь', 'min_level': 1, 'max_level': 15, 'difficulty': 'easy', 'enemies': ['wolf'], 'image': IMAGE_URLS['training_camp']},
    'D': {'name': '🌲 Лес призраков', 'min_level': 10, 'max_level': 25, 'difficulty': 'medium', 'enemies': ['wolf'], 'image': IMAGE_URLS['forest']},
    # ... скопируй остальные локации ...
}

SHOP_ITEMS = {
    'small_health_potion': {'name': '💊 Малое зелье здоровья', 'price': 40, 'type': 'potion', 'effect': 20},
    'large_health_potion': {'name': '💊 Большое зелье здоровья', 'price': 75, 'type': 'potion', 'effect': 40},
    'small_mana_potion': {'name': '🔮 Малое зелье маны', 'price': 35, 'type': 'potion', 'effect': 15},
    # ... остальные товары ...
}

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def get_rank_icon(rank):
    return {'E': '🆕', 'D': '🟢', 'C': '🔵', 'B': '🟣', 'A': '🟠', 'S': '⚡'}.get(rank, '🆕')

def create_enemy(enemy_key, player_level):
    if enemy_key not in BASE_ENEMIES: return None
    base = BASE_ENEMIES[enemy_key].copy()
    
    # Множитель уровня: +15% за уровень
    mult = 1.0 + (player_level - 1) * 0.15
    
    enemy = base.copy()
    enemy['health'] = int(base.get('base_health', 50) * mult)
    enemy['max_health'] = enemy['health']
    # Остальные статы... (упрощено для краткости, вставь свою полную логику)
    enemy['min_physical_damage'] = int(base.get('min_physical_damage', 5) * mult)
    enemy['max_physical_damage'] = int(base.get('max_physical_damage', 8) * mult)
    enemy['min_magic_damage'] = int(base.get('min_magic_damage', 0) * mult)
    enemy['max_magic_damage'] = int(base.get('max_magic_damage', 0) * mult)
    enemy['exp'] = int(base.get('exp', 10) * mult)
    enemy['gold'] = int(base.get('gold', 10) * mult)
    
    return enemy

def get_xp_bar(level, exp, length=10):
    needed = level * 150
    # Простая логика прогресс бара
    percent = min(1.0, exp / needed) if needed > 0 else 0
    filled = int(length * percent)
    return "█" * filled + "░" * (length - filled) + f" {exp}/{needed}"

# --- КЛАВИАТУРЫ ---

def get_main_menu_keyboard(user_id):
    char = database.get_character(user_id)
    kb = [
        [InlineKeyboardButton("📜 Герой", callback_data='profile'), InlineKeyboardButton("🎒 Инвентарь", callback_data='inventory')],
        [InlineKeyboardButton("⚔️ НА БИТВУ!", callback_data='battle_menu')],
        [InlineKeyboardButton("🛍 Торговец", callback_data='shop'), InlineKeyboardButton("🔄 Обновить", callback_data='refresh')]
    ]
    if char and char['stat_points'] > 0:
        kb.insert(2, [InlineKeyboardButton(f"🌟 ПРОКАЧАТЬ ({char['stat_points']})", callback_data='level_up_menu')])
    return InlineKeyboardMarkup(kb)

def get_race_keyboard():
    kb = []
    for k, v in database.RACES.items():
        kb.append([InlineKeyboardButton(f"{v['name']}", callback_data=f"race_{k}")])
    return InlineKeyboardMarkup(kb)

# --- HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    char = database.get_character(user.id)
    
    if char:
        await update.message.reply_photo(
            photo=IMAGE_URLS['village'],
            caption=f"🏰 С возвращением, {char['character_name']}!\nТвои силы восстанавливались пока ты спал...",
            reply_markup=get_main_menu_keyboard(user.id)
        )
        return MAIN_MENU
    else:
        await update.message.reply_text("Приветствую, герой! Выбери расу:", reply_markup=get_race_keyboard())
        return CHOOSE_RACE

async def choose_race(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    race = query.data.split('_')[1]
    context.user_data['race'] = race
    await query.message.reply_text("Как зовут героя?")
    return ENTER_NAME

async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    user_id = update.effective_user.id
    race = context.user_data['race']
    
    success, msg = database.create_new_character_db(user_id, name, race)
    if success:
        await update.message.reply_text("Герой создан!", reply_markup=get_main_menu_keyboard(user_id))
        return MAIN_MENU
    else:
        await update.message.reply_text(f"Ошибка: {msg}")
        return ConversationHandler.END

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    # ЗДЕСЬ СРАБАТЫВАЕТ РЕГЕНЕРАЦИЯ (внутри get_character)
    char = database.get_character(user_id)
    
    text = (
        f"👤 *{char['character_name']}* ({database.RACES[char['race']]['name']})\n"
        f"Уровень: {char['level']} | Золото: {char['gold']}\n"
        f"❤️ HP: {char['health']}/{char['max_health']}\n"
        f"🔮 Mana: {char['mana']}/{char['max_mana']}\n"
        f"Опыт: {get_xp_bar(char['level'], char['experience'])}\n"
        f"Сила: {char['strength']} | Ловкость: {char['agility']}\n"
        f"Интеллект: {char['intelligence']} | Живучесть: {char['vitality']}\n"
        f"\n_Здоровье и мана восстанавливаются 5% в минуту_"
    )
    
    await query.edit_message_caption(caption=text, parse_mode='Markdown', reply_markup=get_main_menu_keyboard(user_id))
    return MAIN_MENU

# ... (Остальные хендлеры: Inventory, Shop, Battle - используй свою логику, 
# но вместо прямых SQL запросов вызывай функции из database.py или используй get_connection внутри функций в database.py)

async def refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просто обновляет меню, триггеря регенерацию"""
    query = update.callback_query
    await query.answer("Данные обновлены!")
    await show_profile(update, context)
    return MAIN_MENU

def main():
    database.init_db()
    
    app = Application.builder().token(TOKEN).build()
    
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSE_RACE: [CallbackQueryHandler(choose_race, pattern='^race_')],
            ENTER_NAME: [MessageHandler(filters.TEXT, enter_name)],
            MAIN_MENU: [
                CallbackQueryHandler(show_profile, pattern='^profile$'),
                CallbackQueryHandler(refresh, pattern='^refresh$'),
                # Добавь остальные хендлеры
            ],
            # Добавь остальные состояния
        },
        fallbacks=[CommandHandler('start', start)]
    )
    
    app.add_handler(conv)
    print("Bot started...")
    app.run_polling()

if __name__ == '__main__':
    main()
