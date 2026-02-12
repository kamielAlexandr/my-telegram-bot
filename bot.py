import os
import logging
import random
import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    ContextTypes, ConversationHandler, MessageHandler, filters
)
# Импортируем наш модуль базы данных
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

# --- КОНТЕНТ (КАРТИНКИ И ДАННЫЕ) ---
IMAGE_URLS = {
    'human': 'https://i126.fastpic.org/thumb/2026/0130/2c/_d2515d33e45fa7ffb5246cacabdaba2c.jpeg',
    'elf': 'https://i126.fastpic.org/thumb/2026/0130/81/_d3d94be5aa45b9239aeb5adc41443081.jpeg',
    'dwarf': 'https://i126.fastpic.org/thumb/2026/0130/5b/_c188fac4eb6d205bd9fc0486c9b9355b.jpeg',
    'orc': 'https://i126.fastpic.org/thumb/2026/0130/20/_b8c1f666bd21bb415e8fb35145eb3e20.jpeg',
    'village': 'https://img.freepik.com/premium-photo/tavern-like-game_808092-1770.jpg',
    'forest': 'https://img.freepik.com/premium-photo/ancient-forest-ai-generated_1127-13930.jpg',
    'training_camp': 'https://img1.liveinternet.ru/images/attach/b/2/1/726/1726838_full0011.jpg',
    'dungeon': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSTZd9YHDcPOGmD8ezmHB0xD-HfA9O7OpgVyA&s',
    'castle': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTrAoGzKjgZxurLbxZ_Dyhtkm1gBqMUMtA87w&s',
    'hell_gate': 'https://abrakadabra.fun/uploads/posts/2022-01/1642490542_3-abrakadabra-fun-p-temnii-mag-art-5.jpg',
    'throne_god': 'https://abrakadabra.fun/uploads/posts/2022-03/1646721873_1-abrakadabra-fun-p-pauk-fantezi-art-1.jpg',
    'shop': 'https://img.freepik.com/premium-photo/tavern-like-game_808092-1770.jpg',
    # Враги
    'wolf': 'https://i.pinimg.com/736x/9f/8e/25/9f8e2507aceaa217060d249c308e2a13.jpg',
    'goblin': 'https://img.freepik.com/free-photo/goblin-digital-art_23-2151061965.jpg',
    'slime': 'https://papik.pro/uploads/posts/2023-02/1676176492_papik-pro-p-risunok-sliz-1.jpg',
    'knight': 'https://i.pinimg.com/originals/92/11/34/9211349d21f146a07aa1e2f920d5c2f4.jpg'
}

BASE_ENEMIES = {
    'wolf': {'name': '🐺 Волк', 'base_health': 35, 'min_physical_damage': 5, 'max_physical_damage': 8, 'exp': 12, 'gold': 8, 'rank': 'E', 'difficulty': 'easy', 'damage_type': 'physical', 'dodge_chance': 0.08, 'image': IMAGE_URLS['wolf']},
    'goblin': {'name': '👹 Гоблин', 'base_health': 40, 'min_physical_damage': 6, 'max_physical_damage': 10, 'exp': 16, 'gold': 12, 'rank': 'E', 'difficulty': 'easy', 'damage_type': 'physical', 'dodge_chance': 0.12, 'image': IMAGE_URLS['goblin']},
    'slime': {'name': '🟢 Слизь', 'base_health': 45, 'min_physical_damage': 3, 'max_physical_damage': 8, 'min_magic_damage': 2, 'max_magic_damage': 5, 'exp': 10, 'gold': 7, 'rank': 'E', 'difficulty': 'easy', 'damage_type': 'mixed', 'image': IMAGE_URLS['slime']},
    'training_master': {'name': '⚔️ Мастер', 'base_health': 100, 'min_physical_damage': 10, 'max_physical_damage': 20, 'exp': 40, 'gold': 32, 'rank': 'E', 'difficulty': 'boss', 'damage_type': 'physical', 'image': IMAGE_URLS['knight'], 'boss_bonus': 2.5}
}

LOCATIONS = {
    'E': {'name': '🎪 Лагерь', 'min_level': 1, 'max_level': 15, 'difficulty': 'easy', 'enemies': ['wolf', 'goblin', 'slime', 'training_master'], 'boss': 'training_master', 'image': IMAGE_URLS['training_camp']},
    'D': {'name': '🌲 Лес', 'min_level': 10, 'max_level': 25, 'difficulty': 'medium', 'enemies': ['wolf'], 'image': IMAGE_URLS['forest']},
    'C': {'name': '🪦 Катакомбы', 'min_level': 20, 'max_level': 35, 'difficulty': 'hard', 'enemies': ['wolf'], 'image': IMAGE_URLS['dungeon']},
    'B': {'name': '🏰 Замок', 'min_level': 30, 'max_level': 45, 'difficulty': 'very_hard', 'enemies': ['wolf'], 'image': IMAGE_URLS['castle']},
    'A': {'name': '🌋 Врата', 'min_level': 40, 'max_level': 55, 'difficulty': 'extreme', 'enemies': ['wolf'], 'image': IMAGE_URLS['hell_gate']},
    'S': {'name': '⚡ Трон', 'min_level': 50, 'max_level': 70, 'difficulty': 'legendary', 'enemies': ['wolf'], 'image': IMAGE_URLS['throne_god']}
}

SHOP_ITEMS = {
    'small_health_potion': {'name': '💊 Малое зелье HP (+20)', 'price': 40, 'type': 'potion', 'effect': 20},
    'large_health_potion': {'name': '💊 Большое зелье HP (+40)', 'price': 75, 'type': 'potion', 'effect': 40},
    'small_mana_potion': {'name': '🔮 Малое зелье MP (+15)', 'price': 35, 'type': 'potion', 'effect': 15},
    'large_mana_potion': {'name': '🔮 Большое зелье MP (+30)', 'price': 65, 'type': 'potion', 'effect': 30}
}

# --- ФУНКЦИИ БОТА ---

def get_rank_icon(rank):
    return {'E': '🆕', 'D': '🟢', 'C': '🔵', 'B': '🟣', 'A': '🟠', 'S': '⚡'}.get(rank, '🆕')

def create_enemy(enemy_key, player_level):
    if enemy_key not in BASE_ENEMIES: return None
    base = BASE_ENEMIES[enemy_key].copy()
    
    # Множитель уровня: +15% за каждый уровень игрока
    mult = 1.0 + (player_level - 1) * 0.15
    
    enemy = base.copy()
    enemy['health'] = int(base['base_health'] * mult)
    enemy['max_health'] = enemy['health']
    
    # Скейлинг урона
    for dmg_key in ['min_physical_damage', 'max_physical_damage', 'min_magic_damage', 'max_magic_damage']:
        if dmg_key in base:
            enemy[dmg_key] = int(base[dmg_key] * mult)
        else:
            enemy[dmg_key] = 0
            
    enemy['exp'] = int(base.get('exp', 10) * mult)
    enemy['gold'] = int(base.get('gold', 10) * mult)
    
    if base.get('difficulty') == 'boss':
        enemy['health'] = int(enemy['health'] * 2.5) # Бонус босса
        enemy['is_boss'] = True
    
    return enemy

def get_xp_bar(level, exp, length=10):
    needed = (level * (level + 1) * 150) // 2 # Накопительный опыт
    # Для упрощения показа текущего уровня
    prev_needed = ((level - 1) * level * 150) // 2
    
    current_level_exp = exp - prev_needed
    level_diff = needed - prev_needed
    
    if level_diff <= 0: return "█" * length
    
    percent = min(1.0, current_level_exp / level_diff)
    filled = int(length * percent)
    return "█" * filled + "░" * (length - filled)

# --- КЛАВИАТУРЫ ---

def get_main_menu_keyboard(user_id):
    # При получении клавиатуры мы запрашиваем персонажа, что триггерит регенерацию в базе
    char = database.get_character(user_id)
    
    kb = [
        [InlineKeyboardButton("📜 Герой", callback_data='profile'), InlineKeyboardButton("🎒 Инвентарь", callback_data='inventory')],
        [InlineKeyboardButton("⚔️ НА БИТВУ!", callback_data='battle_menu')],
        [InlineKeyboardButton("🛍 Торговец", callback_data='shop'), InlineKeyboardButton("🏆 Топ", callback_data='stats')],
        [InlineKeyboardButton("🔄 Обновить (Реген)", callback_data='refresh')]
    ]
    if char and char['stat_points'] > 0:
        kb.insert(3, [InlineKeyboardButton(f"🌟 ПРОКАЧАТЬ ({char['stat_points']})", callback_data='level_up_menu')])
    return InlineKeyboardMarkup(kb)

def get_shop_keyboard(char):
    kb = []
    for k, v in SHOP_ITEMS.items():
        kb.append([InlineKeyboardButton(f"{v['name']} - {v['price']}💰", callback_data=f"buy_{k}")])
    kb.append([InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')])
    return InlineKeyboardMarkup(kb)

# --- HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    char = database.get_character(user.id)
    
    if char:
        await update.message.reply_photo(
            photo=IMAGE_URLS['village'],
            caption=f"🏰 Привет, {char['character_name']}!\nТвои силы восстанавливаются (5%/мин)...",
            reply_markup=get_main_menu_keyboard(user.id)
        )
        return MAIN_MENU
    else:
        kb = [[InlineKeyboardButton(v['name'], callback_data=f"race_{k}")] for k, v in database.RACES.items()]
        await update.message.reply_text("✨ Выбери расу:", reply_markup=InlineKeyboardMarkup(kb))
        return CHOOSE_RACE

async def choose_race(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['race'] = query.data.split('_')[1]
    await query.message.reply_text("✍️ Введи имя героя:")
    return ENTER_NAME

async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text[:20]
    user = update.effective_user
    success, msg = database.create_character(user.id, user.username, name, context.user_data['race'])
    
    if success:
        await update.message.reply_photo(IMAGE_URLS['village'], caption="Герой создан!", reply_markup=get_main_menu_keyboard(user.id))
        return MAIN_MENU
    else:
        await update.message.reply_text(f"Ошибка: {msg}")
        return ConversationHandler.END

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    char = database.get_character(user_id) # ТУТ СРАБАТЫВАЕТ РЕГЕНЕРАЦИЯ
    
    text = (
        f"👤 *{char['character_name']}* ({database.RACES[char['race']]['name']})\n"
        f"{get_rank_icon(char['rank'])} Ранг: {char['rank']} | Уровень: {char['level']}\n"
        f"💰 Золото: {char['gold']}\n\n"
        f"❤️ HP: {char['health']}/{char['max_health']}\n"
        f"🔮 MP: {char['mana']}/{char['max_mana']}\n"
        f"📊 Опыт: {get_xp_bar(char['level'], char['experience'])}\n\n"
        f"Сила: {char['strength']} | Ловкость: {char['agility']}\n"
        f"Интеллект: {char['intelligence']} | Живучесть: {char['vitality']}\n"
        f"\n_HP и MP восстанавливаются сами (5% в минуту)_"
    )
    await query.edit_message_caption(caption=text, parse_mode='Markdown', reply_markup=get_main_menu_keyboard(user_id))
    return MAIN_MENU

async def refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Кнопка для визуального обновления регенерации"""
    query = update.callback_query
    await query.answer("Данные обновлены!")
    await profile(update, context) # Просто вызываем профиль снова
    return MAIN_MENU

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    char = database.get_character(query.from_user.id)
    await query.edit_message_media(
        media=telegram.InputMediaPhoto(IMAGE_URLS['shop'], caption=f"🛍 Магазин. У тебя: {char['gold']}💰"),
        reply_markup=get_shop_keyboard(char)
    )
    return SHOP_MENU

async def buy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    item_key = query.data.split('_')[1]
    item = SHOP_ITEMS.get(item_key)
    
    if item:
        success, msg = database.buy_item(query.from_user.id, item_key, item['type'], item['name'], item['price'], item['effect'])
        await query.answer(msg, show_alert=True)
    
    # Обновляем меню магазина
    await shop(update, context)
    return SHOP_MENU

async def inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    items = database.get_inventory(query.from_user.id)
    
    text = "🎒 *Инвентарь:*\n"
    kb = []
    if not items:
        text += "Пусто..."
    else:
        for i in items:
            text += f"• {i['item_name']} (x{i['quantity']})\n"
            if 'potion' in i['item_key']:
                kb.append([InlineKeyboardButton(f"Использовать {i['item_name']}", callback_data=f"use_{i['item_key']}")])
    
    kb.append([InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')])
    await query.edit_message_caption(caption=text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
    return INVENTORY_MENU

async def use_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    item_key = query.data.split('_')[1]
    success, msg = database.use_item(query.from_user.id, item_key)
    await query.answer(msg, show_alert=True)
    await inventory(update, context)
    return INVENTORY_MENU

async def battle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    char = database.get_character(query.from_user.id)
    
    kb = []
    rank_order = ['E', 'D', 'C', 'B', 'A', 'S']
    p_rank_idx = rank_order.index(char['rank'])
    
    for k, v in LOCATIONS.items():
        if rank_order.index(k) <= p_rank_idx:
            kb.append([InlineKeyboardButton(f"{v['name']} ({k}-ранг)", callback_data=f"loc_{k}")])
            
    kb.append([InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')])
    await query.edit_message_media(
        media=telegram.InputMediaPhoto(IMAGE_URLS['forest'], caption="⚔️ Выбери локацию:"),
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return BATTLE_MENU

async def start_battle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    loc_key = query.data.split('_')[1]
    loc = LOCATIONS[loc_key]
    user_id = query.from_user.id
    char = database.get_character(user_id)
    
    # Выбор врага
    enemy_key = random.choice(loc['enemies'])
    enemy = create_enemy(enemy_key, char['level'])
    
    battle_sessions[user_id] = {
        'enemy': enemy,
        'char': char,
        'log': [f"⚔️ Вы встретили: {enemy['name']} (Ур. {char['level']})"]
    }
    
    await show_battle_interface(query, user_id)
    return IN_BATTLE

async def show_battle_interface(query, user_id):
    session = battle_sessions[user_id]
    enemy = session['enemy']
    char = session['char'] # Это копия, здоровье отнимаем тут
    
    text = (
        f"🆚 *БОЙ*\n"
        f"👤 {char['character_name']}: {char['health']}/{char['max_health']} HP\n"
        f"👿 {enemy['name']}: {enemy['health']}/{enemy['max_health']} HP\n\n"
        f"{chr(10).join(session['log'][-3:])}"
    )
    
    kb = [
        [InlineKeyboardButton("⚔️ Атака", callback_data='atk_phys'), InlineKeyboardButton("🔮 Магия", callback_data='atk_mag')],
        [InlineKeyboardButton("🛡 Блок", callback_data='defend'), InlineKeyboardButton("🏃 Сбежать", callback_data='flee')]
    ]
    
    # Используем edit_message_caption если картинка та же, или media если меняем
    try:
        await query.edit_message_media(
            media=telegram.InputMediaPhoto(enemy['image'], caption=text, parse_mode='Markdown'),
            reply_markup=InlineKeyboardMarkup(kb)
        )
    except:
        await query.edit_message_caption(caption=text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))

async def battle_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    action = query.data.split('_')[1]
    session = battle_sessions[user_id]
    char = session['char']
    enemy = session['enemy']
    log = session['log']
    
    # Ход игрока
    if action == 'flee':
        if random.random() < 0.5:
            del battle_sessions[user_id]
            await query.edit_message_caption(caption="🏃 Вы успешно сбежали!", reply_markup=get_main_menu_keyboard(user_id))
            return MAIN_MENU
        else:
            log.append("🚫 Побег не удался!")
    
    dmg = 0
    if action == 'phys':
        dmg = max(1, int(char['strength'] / 3 * random.uniform(0.8, 1.2)))
        log.append(f"⚔️ Вы нанесли {dmg} урона.")
    elif action == 'mag':
        if char['mana'] >= 5:
            dmg = max(1, int(char['intelligence'] / 3 * random.uniform(1.0, 1.5)))
            char['mana'] -= 5
            log.append(f"🔮 Вы нанесли {dmg} урона (-5 MP).")
        else:
            log.append("❌ Нет маны!")
            
    enemy['health'] -= dmg
    
    # Проверка победы
    if enemy['health'] <= 0:
        database.add_experience(user_id, enemy['exp'])
        database.add_gold(user_id, enemy['gold'])
        database.update_character_stats(user_id, health=char['health'], mana=char['mana'], battle_wins=char['battle_wins']+1)
        del battle_sessions[user_id]
        
        await query.edit_message_caption(
            caption=f"🏆 *ПОБЕДА!*\nПолучено: {enemy['gold']}💰 и {enemy['exp']} XP",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(user_id)
        )
        return MAIN_MENU
    
    # Ход врага
    if action != 'flee':
        e_dmg = random.randint(enemy['min_physical_damage'], enemy['max_physical_damage'])
        if action == 'defend':
            e_dmg //= 2
            log.append(f"🛡 Вы заблокировали часть урона ({e_dmg} получено).")
        else:
            log.append(f"💔 Враг нанес {e_dmg} урона.")
        
        char['health'] -= e_dmg
        
    # Проверка поражения
    if char['health'] <= 0:
        database.update_character_stats(user_id, health=0, battle_losses=char['battle_losses']+1)
        del battle_sessions[user_id]
        await query.edit_message_caption(
            caption="💀 *ВЫ ПОГИБЛИ...*\nЗдоровье упало до 0. Отдохните в деревне.",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(user_id)
        )
        return MAIN_MENU
        
    await show_battle_interface(query, user_id)
    return IN_BATTLE

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    char = database.get_character(query.from_user.id)
    await query.edit_message_media(
        media=telegram.InputMediaPhoto(IMAGE_URLS['village'], caption=f"🏰 В деревне. HP: {char['health']}", parse_mode='Markdown'),
        reply_markup=get_main_menu_keyboard(query.from_user.id)
    )
    return MAIN_MENU

# Добавлен import telegram для InputMediaPhoto
import telegram 

def main():
    database.init_db()
    app = Application.builder().token(TOKEN).build()
    
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSE_RACE: [CallbackQueryHandler(choose_race, pattern='^race_')],
            ENTER_NAME: [MessageHandler(filters.TEXT, enter_name)],
            MAIN_MENU: [
                CallbackQueryHandler(profile, pattern='^profile$'),
                CallbackQueryHandler(inventory, pattern='^inventory$'),
                CallbackQueryHandler(battle_menu, pattern='^battle_menu$'),
                CallbackQueryHandler(shop, pattern='^shop$'),
                CallbackQueryHandler(refresh, pattern='^refresh$') # Рефреш для регенерации
            ],
            SHOP_MENU: [CallbackQueryHandler(buy_handler, pattern='^buy_'), CallbackQueryHandler(back_to_main, pattern='^back_')],
            INVENTORY_MENU: [CallbackQueryHandler(use_handler, pattern='^use_'), CallbackQueryHandler(back_to_main, pattern='^back_')],
            BATTLE_MENU: [CallbackQueryHandler(start_battle, pattern='^loc_'), CallbackQueryHandler(back_to_main, pattern='^back_')],
            IN_BATTLE: [CallbackQueryHandler(battle_action, pattern='^(atk_|defend|flee)')]
        },
        fallbacks=[CommandHandler('start', start)]
    )
    
    app.add_handler(conv)
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
