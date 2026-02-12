import os
import logging
import random
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    ContextTypes, ConversationHandler, MessageHandler, filters
)
import database

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния
CHOOSE_RACE, ENTER_NAME, MAIN_MENU, BATTLE_MENU, IN_BATTLE, SHOP_MENU, LEVEL_UP, INVENTORY_MENU = range(8)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
battle_sessions = {}

# --- КОНТЕНТ ---
IMAGE_URLS = {
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
    'knight': 'https://i.pinimg.com/originals/92/11/34/9211349d21f146a07aa1e2f920d5c2f4.jpg',
    'demon': 'https://img.freepik.com/free-photo/demon_23-2150762325.jpg'
}

BASE_ENEMIES = {
    'wolf': {'name': '🐺 Волк', 'hp': 40, 'str': 8, 'agi': 12, 'exp': 15, 'gold': 10, 'img': IMAGE_URLS['wolf']},
    'goblin': {'name': '👹 Гоблин', 'hp': 50, 'str': 10, 'agi': 8, 'exp': 20, 'gold': 15, 'img': IMAGE_URLS['goblin']},
    'slime': {'name': '🟢 Слизь', 'hp': 60, 'str': 6, 'agi': 2, 'exp': 15, 'gold': 12, 'img': IMAGE_URLS['slime']},
    'knight': {'name': '⚔️ Падший Рыцарь', 'hp': 120, 'str': 18, 'agi': 10, 'exp': 50, 'gold': 40, 'img': IMAGE_URLS['knight']},
    'demon': {'name': '👿 Демон', 'hp': 200, 'str': 25, 'agi': 15, 'exp': 100, 'gold': 80, 'img': IMAGE_URLS['demon']}
}

LOCATIONS = {
    'E': {'name': '🎪 Лагерь', 'min': 1, 'max': 10, 'enemies': ['wolf', 'goblin'], 'img': IMAGE_URLS['training_camp']},
    'D': {'name': '🌲 Лес', 'min': 10, 'max': 25, 'enemies': ['wolf', 'goblin', 'slime'], 'img': IMAGE_URLS['forest']},
    'C': {'name': '🪦 Катакомбы', 'min': 20, 'max': 40, 'enemies': ['goblin', 'knight'], 'img': IMAGE_URLS['dungeon']},
    'B': {'name': '🌋 Врата Ада', 'min': 40, 'max': 60, 'enemies': ['knight', 'demon'], 'img': IMAGE_URLS['hell_gate']}
}

SHOP_ITEMS = {
    'small_hp': {'name': '💊 Зелье HP (+30)', 'price': 30, 'effect': 30},
    'small_mp': {'name': '🔮 Зелье MP (+20)', 'price': 30, 'effect': 20},
}

# --- ЛОГИКА БОЯ ---

def calculate_damage(attacker_str, defender_agi, is_magic=False):
    """Считает урон с учетом уклонения и критов"""
    # Шанс уклонения: 1% за каждое очко ловкости защитника
    dodge_chance = min(defender_agi * 0.01, 0.40) # Макс 40% уклонения
    if random.random() < dodge_chance:
        return 0, "💨 *Промах!* (Уклонение)"
    
    # Шанс крита: 1% за каждое очко ловкости атакующего
    # Для магии используем Интеллект (передаем как attacker_str для магии)
    crit_chance = min(attacker_str * 0.02, 0.50)
    is_crit = random.random() < crit_chance
    
    # Разброс урона: +/- 20%
    base_dmg = attacker_str / 2  # Формула урона: Сила / 2
    damage = int(base_dmg * random.uniform(0.8, 1.2))
    
    status = ""
    if is_crit:
        damage = int(damage * 1.5)
        status = "💥 *КРИТ!*"
        
    return max(1, damage), status

def create_enemy(key, player_level):
    base = BASE_ENEMIES[key].copy()
    mult = 1 + (player_level * 0.1) # +10% статов за уровень игрока
    
    return {
        'name': base['name'],
        'hp': int(base['hp'] * mult),
        'max_hp': int(base['hp'] * mult),
        'str': int(base['str'] * mult),
        'agi': int(base['agi'] * mult),
        'exp': int(base['exp'] * mult),
        'gold': int(base['gold'] * mult),
        'image': base['img']
    }

# --- КЛАВИАТУРЫ ---
def kb_main():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📜 Герой", callback_data="profile"), InlineKeyboardButton("🎒 Инвентарь", callback_data="inventory")],
        [InlineKeyboardButton("⚔️ В БОЙ", callback_data="battle_menu")],
        [InlineKeyboardButton("🛍 Магазин", callback_data="shop"), InlineKeyboardButton("🏆 Топ", callback_data="stats")],
        [InlineKeyboardButton("🔄 Обновить", callback_data="refresh")]
    ])

def kb_battle():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚔️ Атака", callback_data="act_atk"), InlineKeyboardButton("🔮 Магия (10 MP)", callback_data="act_mag")],
        [InlineKeyboardButton("🛡 Защита", callback_data="act_def"), InlineKeyboardButton("🏃 Сбежать", callback_data="act_run")]
    ])

# --- ОБРАБОТЧИКИ ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    char = database.get_character(user.id)
    if char:
        await update.message.reply_photo(IMAGE_URLS['village'], caption=f"С возвращением, {char['character_name']}!", reply_markup=kb_main())
        return MAIN_MENU
    
    kb = [[InlineKeyboardButton(r['name'], callback_data=f"race_{k}")] for k, r in database.RACES.items()]
    await update.message.reply_text("Выберите расу:", reply_markup=InlineKeyboardMarkup(kb))
    return CHOOSE_RACE

async def race_picked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['race'] = query.data.split('_')[1]
    await query.message.reply_text("Как зовут героя?")
    return ENTER_NAME

async def name_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    user = update.effective_user
    database.create_character(user.id, user.username, name, context.user_data['race'])
    await update.message.reply_photo(IMAGE_URLS['village'], caption="Герой создан!", reply_markup=kb_main())
    return MAIN_MENU

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    char = database.get_character(query.from_user.id)
    
    txt = (f"👤 *{char['character_name']}* ({database.RACES[char['race']]['name']})\n"
           f"⭐ Уровень: {char['level']} | Опыт: {char['experience']}\n"
           f"❤️ HP: {char['health']}/{char['max_health']}\n"
           f"🔮 MP: {char['mana']}/{char['max_mana']}\n"
           f"💪 Сила: {char['strength']} | 🦵 Ловкость: {char['agility']}\n"
           f"🧠 Интеллект: {char['intelligence']} | 🛡 Живучесть: {char['vitality']}\n"
           f"💰 Золото: {char['gold']}")
    
    kb = kb_main().inline_keyboard
    if char['stat_points'] > 0:
        kb.insert(0, [InlineKeyboardButton(f"🌟 Прокачать ({char['stat_points']})", callback_data="level_up")])
    
    try:
        await query.edit_message_caption(caption=txt, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
    except:
        await query.edit_message_media(media=telegram.InputMediaPhoto(IMAGE_URLS['village'], caption=txt, parse_mode='Markdown'), reply_markup=InlineKeyboardMarkup(kb))
    return MAIN_MENU

async def level_up_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = [
        [InlineKeyboardButton("Сила", callback_data="up_strength"), InlineKeyboardButton("Ловкость", callback_data="up_agility")],
        [InlineKeyboardButton("Интеллект", callback_data="up_intelligence"), InlineKeyboardButton("Живучесть", callback_data="up_vitality")],
        [InlineKeyboardButton("🔙 Назад", callback_data="profile")]
    ]
    await query.edit_message_caption(caption="Выберите характеристику:", reply_markup=InlineKeyboardMarkup(kb))
    return LEVEL_UP

async def stat_up(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    stat = query.data.split('_')[1]
    database.add_stat_point(query.from_user.id, stat)
    await query.answer("Улучшено!")
    await profile(update, context) # Вернуть в профиль
    return MAIN_MENU

async def stats_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    top = database.get_top_players(10)
    txt = "🏆 *ТОП ИГРОКОВ*\n\n"
    for i, p in enumerate(top, 1):
        medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
        txt += f"{medal} *{p['character_name']}* (Ур.{p['level']})\n   💰 {p['gold']} | ⚔️ {p['battle_wins']}\n"
    
    kb = [[InlineKeyboardButton("🔙 Назад", callback_data="profile")]]
    await query.edit_message_caption(caption=txt, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
    return MAIN_MENU

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    char = database.get_character(query.from_user.id)
    kb = []
    for k, v in SHOP_ITEMS.items():
        kb.append([InlineKeyboardButton(f"{v['name']} ({v['price']}💰)", callback_data=f"buy_{k}")])
    kb.append([InlineKeyboardButton("🔙 Назад", callback_data="profile")])
    
    await query.edit_message_media(
        media=telegram.InputMediaPhoto(IMAGE_URLS['shop'], caption=f"Ваше золото: {char['gold']}", parse_mode='Markdown'),
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return SHOP_MENU

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    item_key = query.data.split('_')[1]
    item = SHOP_ITEMS[item_key]
    success, msg = database.buy_item(query.from_user.id, item_key, item['name'], item['price'], item['effect'])
    await query.answer(msg, show_alert=True)
    await shop(update, context)
    return SHOP_MENU

async def inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    items = database.get_inventory(query.from_user.id)
    txt = "🎒 *Инвентарь*\n" + ("Пусто" if not items else "")
    kb = []
    for i in items:
        txt += f"\n📦 {i['item_name']} (x{i['quantity']})"
        kb.append([InlineKeyboardButton(f"Использовать {i['item_name']}", callback_data=f"use_{i['item_key']}")])
    kb.append([InlineKeyboardButton("🔙 Назад", callback_data="profile")])
    
    await query.edit_message_caption(caption=txt, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
    return INVENTORY_MENU

async def use_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    key = query.data.split('_')[1]
    success, msg = database.use_item(query.from_user.id, key)
    await query.answer(msg, show_alert=True)
    await inventory(update, context)
    return INVENTORY_MENU

# --- БИТВА ---

async def battle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    char = database.get_character(query.from_user.id)
    kb = []
    
    # Определение ранга по уровню (упрощенно)
    rank = 'E'
    if char['level'] >= 10: rank = 'D'
    if char['level'] >= 20: rank = 'C'
    
    ranks = ['E', 'D', 'C', 'B', 'A', 'S']
    player_idx = ranks.index(rank) if rank in ranks else 0
    
    for r, loc in LOCATIONS.items():
        if ranks.index(r) <= player_idx:
            kb.append([InlineKeyboardButton(f"{loc['name']} (Ранг {r})", callback_data=f"loc_{r}")])
            
    kb.append([InlineKeyboardButton("🔙 Назад", callback_data="profile")])
    await query.edit_message_media(media=telegram.InputMediaPhoto(IMAGE_URLS['forest'], caption="Куда отправимся?", parse_mode='Markdown'), reply_markup=InlineKeyboardMarkup(kb))
    return BATTLE_MENU

async def start_battle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    rank = query.data.split('_')[1]
    loc = LOCATIONS[rank]
    
    char = database.get_character(query.from_user.id)
    if char['health'] < 10:
        await query.answer("⚠️ Слишком мало здоровья!", show_alert=True)
        return BATTLE_MENU
        
    enemy_key = random.choice(loc['enemies'])
    enemy = create_enemy(enemy_key, char['level'])
    
    battle_sessions[query.from_user.id] = {
        'char': char,
        'enemy': enemy,
        'log': [f"⚔️ Вы встретили: {enemy['name']} (HP: {enemy['hp']})"]
    }
    
    await render_battle(query, query.from_user.id)
    return IN_BATTLE

async def render_battle(query, user_id):
    session = battle_sessions[user_id]
    char = session['char']
    enemy = session['enemy']
    
    log_text = "\n".join(session['log'][-3:]) # Последние 3 записи
    
    txt = (f"🆚 *БОЙ*\n\n"
           f"👤 *{char['character_name']}*: {char['health']}/{char['max_health']} HP | {char['mana']} MP\n"
           f"👹 *{enemy['name']}*: {enemy['hp']}/{enemy['max_hp']} HP\n\n"
           f"{log_text}")
    
    try:
        await query.edit_message_media(
            media=telegram.InputMediaPhoto(enemy['image'], caption=txt, parse_mode='Markdown'),
            reply_markup=kb_battle()
        )
    except:
        # Если картинка та же, меняем только текст
        await query.edit_message_caption(caption=txt, parse_mode='Markdown', reply_markup=kb_battle())

async def battle_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    action = query.data.split('_')[1]
    
    session = battle_sessions.get(user_id)
    if not session:
        await query.message.reply_text("Бой не найден.")
        return MAIN_MENU
        
    char = session['char']
    enemy = session['enemy']
    log = session['log']
    
    player_dmg = 0
    player_defending = False
    
    # --- ХОД ИГРОКА ---
    if action == 'run':
        # Шанс побега зависит от ловкости
        esc_chance = 0.4 + (char['agility'] * 0.01)
        if random.random() < esc_chance:
            del battle_sessions[user_id]
            await query.edit_message_caption("🏃‍♂️ Вы успешно сбежали!", reply_markup=kb_main())
            return MAIN_MENU
        else:
            log.append("🚫 Побег не удался! Враг атакует.")
    
    elif action == 'atk':
        dmg, status = calculate_damage(char['strength'], enemy['agi'])
        if dmg > 0:
            enemy['hp'] -= dmg
            log.append(f"⚔️ Вы нанесли {dmg} урона. {status}")
        else:
            log.append(status) # Промах
            
    elif action == 'mag':
        if char['mana'] >= 10:
            char['mana'] -= 10
            # Магия бьет от Интеллекта и игнорирует часть уклонения
            dmg, status = calculate_damage(char['intelligence'], enemy['agi'] // 2, is_magic=True)
            dmg = int(dmg * 1.5) # Магия сильнее
            enemy['hp'] -= dmg
            log.append(f"🔮 Магия нанесла {dmg} урона! {status}")
        else:
            log.append("❌ Не хватает маны!")
            
    elif action == 'def':
        player_defending = True
        log.append("🛡 Вы приготовились к защите.")

    # --- ПРОВЕРКА ПОБЕДЫ ---
    if enemy['hp'] <= 0:
        database.add_experience(user_id, enemy['exp'])
        database.update_stats(user_id, gold=char['gold'] + enemy['gold'], health=char['health'], mana=char['mana'], battle_wins=char['battle_wins']+1)
        del battle_sessions[user_id]
        await query.edit_message_caption(
            caption=f"🏆 *ПОБЕДА!*\n\n{enemy['name']} повержен.\nПолучено: {enemy['exp']} XP и {enemy['gold']} золота.",
            parse_mode='Markdown',
            reply_markup=kb_main()
        )
        return MAIN_MENU

    # --- ХОД ВРАГА ---
    # Враг атакует, если игрок не убежал или если побег не удался
    enemy_dmg, status = calculate_damage(enemy['str'], char['agility'])
    
    if enemy_dmg > 0:
        if player_defending:
            enemy_dmg //= 2
            status += " (Блок)"
        char['health'] -= enemy_dmg
        log.append(f"💔 {enemy['name']} нанес {enemy_dmg} урона. {status}")
    else:
        log.append(f"💨 {enemy['name']} промахнулся!")

    # --- ПРОВЕРКА ПОРАЖЕНИЯ ---
    if char['health'] <= 0:
        database.update_stats(user_id, health=0, battle_losses=char['battle_losses']+1)
        del battle_sessions[user_id]
        await query.edit_message_caption(
            caption="☠️ *ВЫ ПОГИБЛИ...*\nВас оттащили в деревню.",
            parse_mode='Markdown',
            reply_markup=kb_main()
        )
        return MAIN_MENU

    # Обновляем БД (сохраняем текущее HP/MP)
    database.update_stats(user_id, health=char['health'], mana=char['mana'])
    
    await render_battle(query, user_id)
    return IN_BATTLE

def main():
    database.init_db()
    app = Application.builder().token(TOKEN).build()
    
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSE_RACE: [CallbackQueryHandler(race_picked, pattern='^race_')],
            ENTER_NAME: [MessageHandler(filters.TEXT, name_entered)],
            MAIN_MENU: [
                CallbackQueryHandler(profile, pattern='^profile$'),
                CallbackQueryHandler(inventory, pattern='^inventory$'),
                CallbackQueryHandler(battle_menu, pattern='^battle_menu$'),
                CallbackQueryHandler(shop, pattern='^shop$'),
                CallbackQueryHandler(stats_top, pattern='^stats$'), # Исправлена кнопка ТОП
                CallbackQueryHandler(profile, pattern='^refresh$')
            ],
            SHOP_MENU: [CallbackQueryHandler(buy, pattern='^buy_'), CallbackQueryHandler(profile, pattern='^profile$')],
            INVENTORY_MENU: [CallbackQueryHandler(use_item, pattern='^use_'), CallbackQueryHandler(profile, pattern='^profile$')],
            LEVEL_UP: [CallbackQueryHandler(stat_up, pattern='^up_'), CallbackQueryHandler(profile, pattern='^profile$')],
            BATTLE_MENU: [CallbackQueryHandler(start_battle, pattern='^loc_'), CallbackQueryHandler(profile, pattern='^profile$')],
            IN_BATTLE: [CallbackQueryHandler(battle_action, pattern='^act_')]
        },
        fallbacks=[CommandHandler('start', start)]
    )
    
    app.add_handler(conv)
    print("Бот запущен...")
    app.run_polling()

if __name__ == '__main__':
    main()
