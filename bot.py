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

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
battle_sessions = {}

# --- АТМОСФЕРНЫЙ КОНТЕНТ ---
# Больше картинок и описаний для погружения
IMAGES = {
    'start': 'https://img.freepik.com/premium-photo/fantasy-medieval-village-tavern_360032-15.jpg',
    'human': 'https://i.pinimg.com/736x/2c/34/96/2c34960309995471699975b967672228.jpg',
    'elf': 'https://i.pinimg.com/564x/4b/32/e4/4b32e407055966130500742523297079.jpg',
    'dwarf': 'https://i.pinimg.com/564x/f3/d9/3e/f3d93e430490729729007f3526529323.jpg',
    'orc': 'https://i.pinimg.com/564x/72/72/79/72727937397022233903903273390390.jpg',
    'forest': 'https://i.pinimg.com/564x/5b/5b/5b/5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b.jpg',
    'dungeon': 'https://i.pinimg.com/564x/6c/6c/6c/6c6c6c6c6c6c6c6c6c6c6c6c6c6c6c6c.jpg',
    'shop': 'https://i.pinimg.com/564x/1a/1a/1a/1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a.jpg',
}

# Расширенный бестиарий с уникальными описаниями и статами
ENEMIES = {
    'wolf': {'name': '🐺 Лютоволк', 'desc': 'Огромный волк с горящими глазами.', 'hp': 45, 'str': 9, 'agi': 12, 'exp': 15, 'gold': 8, 'img': 'https://i.pinimg.com/564x/wolf.jpg'},
    'goblin': {'name': '👹 Гоблин-Вор', 'desc': 'Хитрый коротышка с зазубренным кинжалом.', 'hp': 55, 'str': 11, 'agi': 9, 'exp': 20, 'gold': 15, 'img': 'https://i.pinimg.com/564x/goblin.jpg'},
    'bandit': {'name': '🗡 Бандит', 'desc': 'Разбойник с большой дороги.', 'hp': 70, 'str': 14, 'agi': 10, 'exp': 30, 'gold': 25, 'img': 'https://i.pinimg.com/564x/bandit.jpg'},
    'skeleton': {'name': '💀 Скелет', 'desc': 'Кости, скрепленные темной магией.', 'hp': 60, 'str': 12, 'agi': 6, 'exp': 25, 'gold': 12, 'img': 'https://i.pinimg.com/564x/skeleton.jpg'},
    'orc_warrior': {'name': '👺 Орк-Воин', 'desc': 'Груда мышц в железной броне.', 'hp': 120, 'str': 20, 'agi': 5, 'exp': 55, 'gold': 40, 'img': 'https://i.pinimg.com/564x/orc.jpg'},
    'ghost': {'name': '👻 Призрак', 'desc': 'Бестелесный дух, уворачивающийся от ударов.', 'hp': 40, 'str': 15, 'agi': 20, 'exp': 45, 'gold': 10, 'img': 'https://i.pinimg.com/564x/ghost.jpg'},
    'dragon': {'name': '🐲 Молодой Дракон', 'desc': 'Босс локации. Дышит огнем.', 'hp': 300, 'str': 35, 'agi': 15, 'exp': 200, 'gold': 150, 'img': 'https://i.pinimg.com/564x/dragon.jpg', 'boss': True}
}

LOCATIONS = {
    'E': {'name': '🌲 Темный Лес', 'desc': 'Место для новичков, но будь осторожен ночью.', 'lvl': '1-10', 'mobs': ['wolf', 'goblin'], 'img': IMAGES['forest']},
    'D': {'name': '🏚 Руины Форта', 'desc': 'Здесь обитают бандиты и нежить.', 'lvl': '10-20', 'mobs': ['bandit', 'skeleton'], 'img': IMAGES['dungeon']},
    'C': {'name': '⛰ Пещеры Орков', 'desc': 'Опасные туннели.', 'lvl': '20-35', 'mobs': ['orc_warrior', 'ghost'], 'img': IMAGES['dungeon']},
    'B': {'name': '🌋 Пик Дракона', 'desc': 'Смертельная зона.', 'lvl': '35+', 'mobs': ['dragon'], 'img': IMAGES['dungeon']} # Только дракон
}

# Состояния
CHOOSE_RACE, ENTER_NAME, MAIN_MENU, BATTLE_MENU, IN_BATTLE, SHOP_MENU, LEVEL_UP, INVENTORY_MENU = range(8)

# --- БОЕВАЯ СИСТЕМА (ПРОМАХИ, КРИТЫ, УКЛОНЕНИЕ) ---

def calculate_attack(attacker_str, attacker_agi, defender_agi, is_magic=False):
    """
    Рассчитывает исход удара: Урон, Крит, Промах или Уклонение.
    Возвращает: (урон, текст_события)
    """
    # 1. Шанс попадания (Hit Chance)
    # База 90%, +1% за каждое очко ловкости атакующего, -1% за ловкость защитника
    hit_chance = 0.90 + ((attacker_agi - defender_agi) * 0.01)
    hit_chance = max(0.30, min(1.0, hit_chance)) # Минимум 30%, максимум 100%

    if random.random() > hit_chance and not is_magic: # Магия не промахивается так просто
        return 0, "💨 *ПРОМАХ!* Враг слишком быстр."

    # 2. Шанс крита (Crit Chance)
    crit_chance = attacker_agi * 0.015 # 1.5% за очко ловкости
    is_crit = random.random() < crit_chance

    # 3. Базовый урон (Разброс +/- 15%)
    base = attacker_str if not is_magic else attacker_str * 1.5 # Магия сильнее, но стоит маны
    dmg = int(base * random.uniform(0.85, 1.15))

    status = ""
    if is_crit:
        dmg = int(dmg * 1.5)
        status = "💥 *КРИТИЧЕСКИЙ УДАР!*"
    
    return max(1, dmg), status

def create_mob(key, player_lvl):
    base = ENEMIES[key].copy()
    # Скейлинг: Враги становятся сильнее на 8% за каждый уровень игрока
    scale = 1 + (player_lvl * 0.08)
    
    mob = base.copy()
    mob['hp'] = int(base['hp'] * scale)
    mob['max_hp'] = mob['hp']
    mob['str'] = int(base['str'] * scale)
    mob['agi'] = int(base['agi'] * scale)
    mob['exp'] = int(base['exp'] * scale)
    mob['gold'] = int(base['gold'] * scale)
    return mob

# --- КЛАВИАТУРЫ ---
def kb_main():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📜 Герой", callback_data="profile"), InlineKeyboardButton("🎒 Мешок", callback_data="inv")],
        [InlineKeyboardButton("⚔️ ИСКАТЬ ПРИКЛЮЧЕНИЯ", callback_data="battle")],
        [InlineKeyboardButton("🛖 Лавка", callback_data="shop"), InlineKeyboardButton("🏆 Легенды", callback_data="top")],
        [InlineKeyboardButton("💤 Отдых (Обновить)", callback_data="refresh")]
    ])

def kb_battle():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚔️ Удар", callback_data="atk"), InlineKeyboardButton("🔥 Магия (15 MP)", callback_data="mag")],
        [InlineKeyboardButton("🛡 Блок", callback_data="def"), InlineKeyboardButton("🏃 Бежать!", callback_data="run")]
    ])

# --- ХЕНДЛЕРЫ ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    char = database.get_character(user.id)
    if char:
        await update.message.reply_photo(IMAGES['start'], caption=f"🏰 *Таверна*\n\nПриветствую, {char['character_name']}! Твоя кружка эля ждет тебя.", parse_mode='Markdown', reply_markup=kb_main())
        return MAIN_MENU
    
    txt = "✨ *Создание Героя*\n\nМир в опасности. Выбери, кем ты рожден:"
    kb = [[InlineKeyboardButton(f"{r['name']}", callback_data=f"race_{k}")] for k, r in database.RACES.items()]
    await update.message.reply_photo(IMAGES['start'], caption=txt, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
    return CHOOSE_RACE

async def choose_race(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    race_key = query.data.split('_')[1]
    context.user_data['race'] = race_key
    race = database.RACES[race_key]
    
    txt = (f"Вы выбрали: *{race['name']}*\n_{race['desc']}_\n\n"
           f"Способность: {race['ability']}\n\n"
           "Как будут звать легенду? (Напиши имя):")
    
    # Показываем картинку расы, если есть, или дефолт
    img = IMAGES.get(race_key, IMAGES['start'])
    await query.edit_message_media(media=telegram.InputMediaPhoto(img, caption=txt, parse_mode='Markdown'))
    return ENTER_NAME

async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text[:20]
    user = update.effective_user
    res, msg = database.create_character(user.id, user.username, name, context.user_data['race'])
    
    if res:
        await update.message.reply_text("✅ Герой создан! Добро пожаловать в мир.", reply_markup=kb_main())
        return MAIN_MENU
    else:
        await update.message.reply_text(f"Ошибка: {msg}. Введите /start заново.")
        return ConversationHandler.END

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    char = database.get_character(query.from_user.id)
    
    race_info = database.RACES[char['race']]
    
    # Прогресс бар опыта
    needed = (char['level'] * (char['level'] + 1) * 150) // 2
    prev = ((char['level'] - 1) * char['level'] * 150) // 2
    cur = char['experience'] - prev
    need_lvl = needed - prev
    perc = int((cur / need_lvl) * 10)
    bar = "🟦" * perc + "⬜" * (10 - perc)

    txt = (f"👤 *{char['character_name']}* | {race_info['name']}\n"
           f"⭐ Уровень: {char['level']} | {bar} ({cur}/{need_lvl})\n"
           f"💰 Золото: {char['gold']}\n\n"
           f"❤️ Здоровье: `{char['health']}/{char['max_health']}`\n"
           f"🧿 Мана: `{char['mana']}/{char['max_mana']}`\n\n"
           f"⚔️ *Характеристики:*\n"
           f"💪 Сила: {char['strength']} (Физ. урон)\n"
           f"🦶 Ловкость: {char['agility']} (Уклонение/Крит)\n"
           f"🧠 Интеллект: {char['intelligence']} (Магия)\n"
           f"🛡 Живучесть: {char['vitality']} (Здоровье)\n\n"
           f"🏆 Побед: {char['battle_wins']}")
    
    kb = kb_main().inline_keyboard
    if char['stat_points'] > 0:
        kb.insert(0, [InlineKeyboardButton(f"🌟 ПОВЫСИТЬ УРОВЕНЬ ({char['stat_points']})", callback_data="levelup")])
        
    try:
        await query.edit_message_caption(caption=txt, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
    except:
        await query.message.reply_text(txt, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
    return MAIN_MENU

# --- СИСТЕМА БОЯ ---

async def battle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    char = database.get_character(query.from_user.id)
    
    if char['health'] < char['max_health'] * 0.1:
        await query.answer("⚠️ Вы слишком ранены! Отдохните или выпейте зелье.", show_alert=True)
        return MAIN_MENU

    # Выбор локации по уровню
    loc_key = 'E'
    if char['level'] >= 10: loc_key = 'D'
    if char['level'] >= 20: loc_key = 'C'
    if char['level'] >= 35: loc_key = 'B'
    
    loc = LOCATIONS[loc_key]
    mob_key = random.choice(loc['mobs'])
    mob = create_mob(mob_key, char['level'])
    
    battle_sessions[query.from_user.id] = {
        'char': char,
        'mob': mob,
        'log': [f"⚔️ Вы вошли в *{loc['name']}* и встретили *{mob['name']}*!"]
    }
    
    await render_battle(query, query.from_user.id)
    return IN_BATTLE

async def render_battle(query, user_id):
    s = battle_sessions[user_id]
    c = s['char']
    m = s['mob']
    
    log_str = "\n".join(s['log'][-4:]) # Последние 4 сообщения
    
    txt = (f"🆚 *БОЙ*\n\n"
           f"👤 *{c['character_name']}*\n"
           f"❤️ {c['health']}/{c['max_health']}  🧿 {c['mana']}\n\n"
           f"👺 *{m['name']}*\n"
           f"❤️ {m['hp']}/{m['max_hp']}\n\n"
           f"📜 *Ход сражения:*\n{log_str}")
    
    # Чтобы не моргала картинка, пробуем редактировать только текст
    try:
        await query.edit_message_media(
            media=telegram.InputMediaPhoto(m.get('img', IMAGES['start']), caption=txt, parse_mode='Markdown'),
            reply_markup=kb_battle()
        )
    except:
        await query.edit_message_caption(caption=txt, parse_mode='Markdown', reply_markup=kb_battle())

async def battle_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    act = query.data
    
    if uid not in battle_sessions:
        await query.message.reply_text("Бой потерян...")
        return MAIN_MENU
        
    s = battle_sessions[uid]
    c = s['char']
    m = s['mob']
    
    player_turn_done = False
    player_defending = False
    
    # --- ХОД ИГРОКА ---
    if act == "run":
        # Шанс побега: (Ловкость игрока / Ловкость моба) * 50%
        chance = (c['agility'] / m['agi']) * 0.5
        if random.random() < chance:
            del battle_sessions[uid]
            await query.edit_message_caption("🏃‍♂️ *Вы успешно скрылись в тенях!*", parse_mode='Markdown', reply_markup=kb_main())
            return MAIN_MENU
        else:
            s['log'].append("🚫 *Побег не удался!* Вы споткнулись.")
            player_turn_done = True

    elif act == "atk":
        dmg, status = calculate_attack(c['strength'], c['agility'], m['agi'])
        if dmg > 0:
            m['hp'] -= dmg
            s['log'].append(f"⚔️ Вы ударили на *{dmg}* урона. {status}")
        else:
            s['log'].append(status) # Промах
        player_turn_done = True
        
    elif act == "mag":
        if c['mana'] >= 15:
            c['mana'] -= 15
            # Магия бьет от Интеллекта, игнорирует половину ловкости врага
            dmg, status = calculate_attack(c['intelligence'], c['agility'], m['agi'] // 2, is_magic=True)
            m['hp'] -= dmg
            s['log'].append(f"🔥 Огненный шар нанес *{dmg}* урона! {status}")
            player_turn_done = True
        else:
            s['log'].append("❌ *Не хватает маны!*")
            # Ход не тратится, игрок должен выбрать другое действие
            player_turn_done = False 

    elif act == "def":
        s['log'].append("🛡 Вы встали в глухую оборону.")
        player_defending = True
        player_turn_done = True

    # --- ПРОВЕРКА ПОБЕДЫ (Сразу после удара игрока) ---
    if m['hp'] <= 0:
        lvl_up = database.add_rewards(uid, m['exp'], m['gold'])
        database.update_hp_mp(uid, c['health'], c['mana']) # Сохраняем остаток хп
        del battle_sessions[uid]
        
        win_text = (f"🏆 *ПОБЕДА!*\n\n"
                    f"Монстр {m['name']} повержен.\n"
                    f"➕ {m['exp']} Опыта\n"
                    f"💰 {m['gold']} Золота")
        if lvl_up:
            win_text += "\n\n🆙 *НОВЫЙ УРОВЕНЬ!* Откройте профиль."
            
        await query.edit_message_caption(caption=win_text, parse_mode='Markdown', reply_markup=kb_main())
        return MAIN_MENU

    # --- ХОД ВРАГА (Только если игрок завершил ход) ---
    if player_turn_done:
        dmg, status = calculate_attack(m['str'], m['agi'], c['agility'])
        
        if dmg > 0:
            if player_defending:
                dmg = dmg // 2
                status += " (Блок)"
            
            c['health'] -= dmg
            s['log'].append(f"💔 {m['name']} нанес вам *{dmg}*. {status}")
        else:
            s['log'].append(f"💨 {m['name']} промахнулся!")
            
    # --- ПРОВЕРКА ПОРАЖЕНИЯ ---
    if c['health'] <= 0:
        database.update_hp_mp(uid, 0, c['mana'])
        del battle_sessions[uid]
        await query.edit_message_caption(
            caption="☠️ *ВЫ ПАЛИ В БОЮ...*\nМестные жрецы воскресили вас в деревне, но гордость пострадала.",
            parse_mode='Markdown',
            reply_markup=kb_main()
        )
        return MAIN_MENU

    # Сохраняем промежуточное состояние (чтобы реген не сработал во время боя)
    database.update_hp_mp(uid, c['health'], c['mana'])
    await render_battle(query, uid)
    return IN_BATTLE

# --- ПРОКАЧКА, МАГАЗИН И ТОП ---

async def level_up(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = [
        [InlineKeyboardButton("💪 Сила", callback_data="up_strength"), InlineKeyboardButton("🦶 Ловкость", callback_data="up_agility")],
        [InlineKeyboardButton("🧠 Интеллект", callback_data="up_intelligence"), InlineKeyboardButton("🛡 Живучесть", callback_data="up_vitality")],
        [InlineKeyboardButton("🔙 Назад", callback_data="profile")]
    ]
    await query.edit_message_caption("Выберите характеристику для улучшения:", reply_markup=InlineKeyboardMarkup(kb))
    return LEVEL_UP

async def stat_up(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    stat = query.data.split('_')[1]
    database.add_stat_point(query.from_user.id, stat)
    await query.answer("Характеристика улучшена!")
    await profile(update, context)
    return MAIN_MENU

async def show_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    top = database.get_top_players(10)
    
    txt = "🏆 *ДОСКА ПОЧЕТА*\n━━━━━━━━━━━━━━━\n"
    if not top:
        txt += "Пока пусто..."
    
    for i, p in enumerate(top, 1):
        medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else "▫️"
        txt += f"{medal} *{p['character_name']}* (Ур. {p['level']})\n"
        txt += f"   ⚔️ {p['battle_wins']} побед | 💰 {p['gold']}\n\n"
        
    kb = [[InlineKeyboardButton("🔙 В меню", callback_data="profile")]]
    try:
        await query.edit_message_caption(caption=txt, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
    except:
        await query.message.reply_text(txt, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
    return MAIN_MENU

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = [
        [InlineKeyboardButton("💊 Зелье HP (30g)", callback_data="buy_hp"), InlineKeyboardButton("🔮 Зелье MP (30g)", callback_data="buy_mp")],
        [InlineKeyboardButton("🔙 Назад", callback_data="profile")]
    ]
    await query.edit_message_media(media=telegram.InputMediaPhoto(IMAGES['shop'], caption="Торговец: *Что желаешь купить?*", parse_mode='Markdown'), reply_markup=InlineKeyboardMarkup(kb))
    return SHOP_MENU

async def buy_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    item_type = query.data.split('_')[1]
    
    item = {'name': 'Зелье здоровья', 'effect': 30} if item_type == 'hp' else {'name': 'Зелье маны', 'effect': 20}
    key = 'small_hp' if item_type == 'hp' else 'small_mp'
    
    res, msg = database.buy_item(query.from_user.id, key, item['name'], 30, item['effect'])
    await query.answer(msg, show_alert=not res)
    return SHOP_MENU

async def inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    items = database.get_inventory(query.from_user.id)
    
    txt = "🎒 *Ваш мешок:*\n\n"
    kb = []
    if not items: txt += "_Пусто..._"
    
    for i in items:
        txt += f"📦 *{i['item_name']}* (x{i['quantity']})\n"
        kb.append([InlineKeyboardButton(f"Использовать {i['item_name']}", callback_data=f"use_{i['id']}")])
        
    kb.append([InlineKeyboardButton("🔙 Назад", callback_data="profile")])
    await query.edit_message_caption(caption=txt, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
    return INVENTORY_MENU

async def use_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    item_id = query.data.split('_')[1]
    res, msg = database.use_inventory_item(query.from_user.id, item_id)
    await query.answer(msg)
    await inventory(update, context)
    return INVENTORY_MENU

async def refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Отдых...")
    await profile(update, context)
    return MAIN_MENU

# --- ЗАПУСК ---
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
                CallbackQueryHandler(battle_start, pattern='^battle$'),
                CallbackQueryHandler(shop, pattern='^shop$'),
                CallbackQueryHandler(inventory, pattern='^inv$'),
                CallbackQueryHandler(refresh, pattern='^refresh$'),
                CallbackQueryHandler(show_top, pattern='^top$') # Исправлена кнопка топа
            ],
            BATTLE_MENU: [CallbackQueryHandler(battle_start, pattern='^fight')],
            IN_BATTLE: [CallbackQueryHandler(battle_action, pattern='^(atk|mag|def|run)')],
            SHOP_MENU: [CallbackQueryHandler(buy_item, pattern='^buy_'), CallbackQueryHandler(profile, pattern='^profile')],
            LEVEL_UP: [CallbackQueryHandler(stat_up, pattern='^up_'), CallbackQueryHandler(profile, pattern='^profile')],
            INVENTORY_MENU: [CallbackQueryHandler(use_item, pattern='^use_'), CallbackQueryHandler(profile, pattern='^profile')]
        },
        fallbacks=[CommandHandler('start', start)]
    )
    
    app.add_handler(conv)
    print("Бот запущен! (Атмосфера RPG включена)")
    app.run_polling()

if __name__ == '__main__':
    main()
