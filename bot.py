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

# --- КОНТЕНТ: ЛОКАЦИИ И МОНСТРЫ ---

# 2 Локации для ранга E, в каждой по 5 разных мобов
# Картинки уникальные для каждого
LOCATIONS = {
    'forest': {
        'name': '🌲 Гнилой Лес',
        'rank': 'E',
        'img': 'https://i.pinimg.com/736x/2d/7b/72/2d7b72522c009945030222079075727e.jpg',
        'desc': 'Темная чаща, где деревья шепчут проклятия. Идеально для новичков.',
        'mobs': ['rat', 'spider', 'wolf', 'bandit', 'bear']
    },
    'mine': {
        'name': '⛏ Заброшенная Шахта',
        'rank': 'E',
        'img': 'https://i.pinimg.com/736x/8a/34/06/8a340632b49673992224772863777722.jpg',
        'desc': 'Старые туннели, кишащие подземными тварями.',
        'mobs': ['bat', 'kobold', 'slime', 'dwarf_zombie', 'golem']
    },
    # Можно добавить D, C ранг и т.д.
}

# Бестиарий (10 уникальных мобов для E-ранга)
MOBS = {
    # Лес
    'rat': {'name': '🐀 Чумная Крыса', 'lvl': 1, 'hp': 25, 'str': 5, 'agi': 5, 'xp': 10, 'gold': 5, 'img': 'https://i.pinimg.com/564x/f3/d3/de/f3d3de7a56327344073f84307379766d.jpg'},
    'spider': {'name': '🕷 Лесной Паук', 'lvl': 3, 'hp': 35, 'str': 7, 'agi': 10, 'xp': 15, 'gold': 8, 'img': 'https://i.pinimg.com/564x/27/7f/73/277f73db0c202022464736f94793672d.jpg'},
    'wolf': {'name': '🐺 Серый Волк', 'lvl': 5, 'hp': 50, 'str': 10, 'agi': 8, 'xp': 20, 'gold': 12, 'img': 'https://i.pinimg.com/564x/c7/2b/9d/c72b9d034237d6929944372922442c7f.jpg'},
    'bandit': {'name': '🗡 Разбойник', 'lvl': 7, 'hp': 70, 'str': 12, 'agi': 7, 'xp': 30, 'gold': 20, 'img': 'https://i.pinimg.com/564x/7d/87/40/7d8740d2492d52927233267232230206.jpg'},
    'bear': {'name': '🐻 Медведь-Людоед', 'lvl': 10, 'hp': 120, 'str': 15, 'agi': 3, 'xp': 50, 'gold': 35, 'img': 'https://i.pinimg.com/564x/a4/09/8f/a4098f98e87490022723049282387342.jpg'},
    
    # Шахта
    'bat': {'name': '🦇 Пещерная Летучая Мышь', 'lvl': 2, 'hp': 30, 'str': 4, 'agi': 15, 'xp': 12, 'gold': 6, 'img': 'https://i.pinimg.com/564x/76/01/cc/7601cc3370e7e462d733230a84364024.jpg'},
    'kobold': {'name': '🦎 Кобольд-Шахтер', 'lvl': 4, 'hp': 45, 'str': 8, 'agi': 9, 'xp': 18, 'gold': 10, 'img': 'https://i.pinimg.com/564x/3b/22/e0/3b22e032f30663673c99092497640f8e.jpg'},
    'slime': {'name': '🟢 Кислотная Слизь', 'lvl': 6, 'hp': 80, 'str': 6, 'agi': 1, 'xp': 25, 'gold': 15, 'img': 'https://i.pinimg.com/564x/c3/84/04/c384048704207908b988f07094200673.jpg'},
    'dwarf_zombie': {'name': '🧟 Зомби-Дварф', 'lvl': 8, 'hp': 100, 'str': 14, 'agi': 2, 'xp': 40, 'gold': 25, 'img': 'https://i.pinimg.com/564x/e7/76/9b/e7769bf4772023023249497e84240742.jpg'},
    'golem': {'name': '🗿 Каменный Голем', 'lvl': 12, 'hp': 150, 'str': 20, 'agi': 0, 'xp': 65, 'gold': 50, 'img': 'https://i.pinimg.com/564x/24/76/8f/24768f00030026e99279743936934c20.jpg'},
}

# Магазин
SHOP_ITEMS = {
    'small_hp': {'name': '💊 Зелье HP (+50)', 'price': 30, 'effect': 50},
    'small_mp': {'name': '🔮 Зелье MP (+30)', 'price': 30, 'effect': 30},
}

# Состояния
CHOOSE_RACE, ENTER_NAME, MAIN_MENU, LOCATION_MENU, MOB_MENU, IN_BATTLE, SHOP_MENU, LEVEL_UP, INVENTORY_MENU = range(9)

# --- ЛОГИКА БОЯ ---

def calculate_attack(attacker_str, attacker_agi, defender_agi, is_magic=False, ability_bonus=False):
    """Сложная формула урона с вероятностями"""
    # 1. Точность (Hit Chance)
    # Если ловкость врага намного выше, шанс попасть падает
    hit_chance = 0.95 + ((attacker_agi - defender_agi) * 0.02)
    hit_chance = max(0.40, min(1.0, hit_chance)) # Не меньше 40%, не больше 100%
    
    if random.random() > hit_chance and not is_magic:
        return 0, "💨 *ПРОМАХ!* (Враг уклонился)"

    # 2. Крит (Crit Chance)
    crit_chance = attacker_agi * 0.02 # 2% за очко ловкости
    is_crit = random.random() < crit_chance

    # 3. Базовый урон
    multiplier = 1.5 if is_magic else 0.5
    base_dmg = attacker_str * multiplier
    
    # Разброс урона +/- 20%
    dmg = int(base_dmg * random.uniform(0.8, 1.2))
    
    if ability_bonus: dmg = int(dmg * 1.5) # Бонус расы

    status = ""
    if is_crit:
        dmg = int(dmg * 1.5)
        status = "💥 *КРИТ!*"
        
    return max(1, dmg), status

# --- МЕНЮ И ИНТЕРФЕЙС ---

def kb_main():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📜 Профиль", callback_data="profile"), InlineKeyboardButton("🎒 Мешок", callback_data="inv")],
        [InlineKeyboardButton("🗺 КАРТА МИРА (БОЙ)", callback_data="map")],
        [InlineKeyboardButton("🛖 Торговец", callback_data="shop"), InlineKeyboardButton("🏆 Доска почета", callback_data="top")],
        [InlineKeyboardButton("💤 Отдых (Реген)", callback_data="refresh")]
    ])

def kb_battle(race_ability_name):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚔️ Атака", callback_data="atk"), InlineKeyboardButton("🔥 Магия (15 MP)", callback_data="mag")],
        [InlineKeyboardButton("🛡 Блок", callback_data="def"), InlineKeyboardButton(f"✨ {race_ability_name}", callback_data="ult")],
        [InlineKeyboardButton("🏃 Попытаться сбежать", callback_data="run")]
    ])

# --- ХЕНДЛЕРЫ ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    char = database.get_character(user.id)
    if char:
        await update.message.reply_photo(
            "https://img.freepik.com/premium-photo/fantasy-medieval-village-tavern_360032-15.jpg", 
            caption=f"🍺 Таверна 'Пьяный Гоблин'\n\nС возвращением, {char['character_name']}! Твоя кружка полна.", 
            reply_markup=kb_main()
        )
        return MAIN_MENU
    
    kb = [[InlineKeyboardButton(f"{r['name']}", callback_data=f"race_{k}")] for k, r in database.RACES.items()]
    await update.message.reply_photo(
        "https://i.pinimg.com/564x/9e/7b/39/9e7b39920b72c9577732a392a5d29505.jpg",
        caption="🌑 *НАЧАЛО ПУТИ*\n\nТы стоишь перед зеркалом судьбы. Кто ты?",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return CHOOSE_RACE

async def choose_race(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    race_key = query.data.split('_')[1]
    context.user_data['race'] = race_key
    race = database.RACES[race_key]
    
    await query.edit_message_caption(
        caption=f"Выбрана раса: *{race['name']}*\n_{race['desc']}_\n\nКак тебя зовут, путник?",
        parse_mode='Markdown'
    )
    return ENTER_NAME

async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text[:20]
    user = update.effective_user
    database.create_character(user.id, user.username, name, context.user_data['race'])
    await update.message.reply_text("✅ Персонаж создан!", reply_markup=kb_main())
    return MAIN_MENU

# --- СИСТЕМА ЛОКАЦИЙ И ВЫБОРА БОЯ ---

async def show_map(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    char = database.get_character(query.from_user.id)
    
    # Фильтр локаций по рангу
    kb = []
    # Порядок рангов для сравнения
    ranks_priority = ['E', 'D', 'C', 'B', 'A', 'S']
    player_rank_idx = ranks_priority.index(char['rank'])
    
    for key, loc in LOCATIONS.items():
        loc_rank_idx = ranks_priority.index(loc['rank'])
        if loc_rank_idx <= player_rank_idx:
            status = "🔓 Открыто"
        else:
            status = "🔒 Закрыто"
            
        if loc_rank_idx <= player_rank_idx:
            kb.append([InlineKeyboardButton(f"{loc['name']} ({loc['rank']}-ранг)", callback_data=f"go_{key}")])
            
    kb.append([InlineKeyboardButton("🔙 В город", callback_data="main")])
    
    await query.edit_message_media(
        media=telegram.InputMediaPhoto(
            "https://i.pinimg.com/564x/4e/1c/0e/4e1c0e3e26703a553075253106362536.jpg", # Карта
            caption=f"🗺 *КАРТА КОРОЛЕВСТВА*\nТвой ранг: {char['rank']}\n\nКуда направимся?",
            parse_mode='Markdown'
        ),
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return LOCATION_MENU

async def show_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    loc_key = query.data.split('_')[1]
    loc = LOCATIONS[loc_key]
    
    # Список мобов в этой локации
    kb = []
    for mob_key in loc['mobs']:
        mob_info = MOBS[mob_key]
        kb.append([InlineKeyboardButton(f"{mob_info['name']} (Ур.{mob_info['lvl']})", callback_data=f"fight_{mob_key}")])
    
    kb.append([InlineKeyboardButton("🔙 На карту", callback_data="map")])
    
    await query.edit_message_media(
        media=telegram.InputMediaPhoto(
            loc['img'],
            caption=f"📍 *{loc['name']}*\n_{loc['desc']}_\n\nКого будем искать?",
            parse_mode='Markdown'
        ),
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return MOB_MENU

# --- ИНИЦИАЛИЗАЦИЯ БОЯ ---

async def start_fight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    mob_key = query.data.split('_')[1]
    mob_template = MOBS[mob_key]
    char = database.get_character(query.from_user.id)
    
    if char['health'] < 10:
        await query.answer("⚠️ Ты слишком ранен! Иди отдыхать.", show_alert=True)
        return MOB_MENU
        
    # Создаем экземпляр моба для боя
    mob = mob_template.copy()
    mob['max_hp'] = mob['hp']
    
    battle_sessions[query.from_user.id] = {
        'char': char,
        'mob': mob,
        'log': [f"⚔️ *{mob['name']}* выпрыгивает из тени!"],
        'turn': 1
    }
    
    await render_battle(query, query.from_user.id)
    return IN_BATTLE

async def render_battle(query, user_id):
    s = battle_sessions[user_id]
    c = s['char']
    m = s['mob']
    
    log = "\n".join(s['log'][-4:]) # Показываем 4 последние строки
    
    # Полоски здоровья
    hp_perc = int((c['health'] / c['max_health']) * 10)
    c_bar = "🟩" * hp_perc + "⬜" * (10 - hp_perc)
    
    m_hp_perc = int((m['hp'] / m['max_hp']) * 10)
    m_bar = "🟥" * m_hp_perc + "⬜" * (10 - m_hp_perc)
    
    text = (f"🔥 *БОЙ - Ход {s['turn']}*\n\n"
            f"👤 *{c['character_name']}*\n"
            f"{c_bar} ({c['health']} HP) 🧿 {c['mana']} MP\n\n"
            f"👺 *{m['name']}*\n"
            f"{m_bar} ({m['hp']} HP)\n\n"
            f"📜 *События:*\n{log}")
            
    race_ability = database.RACES[c['race']]['ability'].split(' ')[0]
    
    # Используем try/except чтобы не было ошибки, если текст не изменился
    try:
        await query.edit_message_media(
            media=telegram.InputMediaPhoto(m['img'], caption=text, parse_mode='Markdown'),
            reply_markup=kb_battle(race_ability)
        )
    except:
        await query.edit_message_caption(caption=text, parse_mode='Markdown', reply_markup=kb_battle(race_ability))

async def battle_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    act = query.data
    
    if uid not in battle_sessions:
        await query.message.reply_text("Бой устарел.")
        return MAIN_MENU
        
    s = battle_sessions[uid]
    c = s['char']
    m = s['mob']
    
    player_turn_done = False
    player_defending = False
    ability_used = False
    
    # --- ХОД ИГРОКА ---
    if act == "run":
        # Шанс сбежать зависит от разницы ловкости
        chance = 0.5 + ((c['agility'] - m['agi']) * 0.02)
        if random.random() < chance:
            del battle_sessions[uid]
            await query.edit_message_caption("🏃‍♂️ *Трусливо, но надежно... Вы сбежали.*", parse_mode='Markdown', reply_markup=kb_main())
            return MAIN_MENU
        else:
            s['log'].append("🚫 *Побег провалился!* Враг схватил вас.")
            player_turn_done = True

    elif act == "atk":
        dmg, status = calculate_attack(c['strength'], c['agility'], m['agi'])
        if dmg > 0:
            m['hp'] -= dmg
            s['log'].append(f"⚔️ Вы нанесли *{dmg}* урона. {status}")
        else:
            s['log'].append(status)
        player_turn_done = True
        
    elif act == "mag":
        if c['mana'] >= 15:
            c['mana'] -= 15
            # Магия почти всегда попадает
            dmg, status = calculate_attack(c['intelligence'], c['agility'] + 100, m['agi'], is_magic=True)
            m['hp'] -= dmg
            s['log'].append(f"🔥 Заклинание сожгло врага на *{dmg}*! {status}")
            player_turn_done = True
        else:
            s['log'].append("❌ *Нет маны!*")
            player_turn_done = False

    elif act == "ult":
        # Ультимативная способность (стоит 30 маны)
        if c['mana'] >= 30:
            c['mana'] -= 30
            race = c['race']
            if race == 'human': # Адаптивность (Защита + Хил)
                c['health'] = min(c['max_health'], c['health'] + 20)
                player_defending = True
                s['log'].append("🛡 *Адаптивность!* +20 HP и защита.")
            elif race == 'elf': # Меткий выстрел (Гарантированный крит)
                dmg = int(c['agility'] * 2.5)
                m['hp'] -= dmg
                s['log'].append(f"🏹 *Выстрел в глаз!* Нанесено {dmg} урона.")
            elif race == 'dwarf': # Каменная кожа
                c['health'] = min(c['max_health'], c['health'] + 40)
                s['log'].append("🏔 *Каменная кожа!* +40 HP.")
            elif race == 'orc': # Берсерк
                dmg = int(c['strength'] * 3)
                c['health'] -= 10
                m['hp'] -= dmg
                s['log'].append(f"🩸 *БЕРСЕРК!* -10 HP себе, врагу {dmg} урона.")
            
            player_turn_done = True
        else:
            s['log'].append("❌ *Нужно 30 маны для способности!*")
            player_turn_done = False

    elif act == "def":
        player_defending = True
        s['log'].append("🛡 Вы подняли щит.")
        player_turn_done = True

    # --- ПРОВЕРКА ПОБЕДЫ ---
    if m['hp'] <= 0:
        lvl_up, new_rank = database.add_rewards(uid, m['xp'], m['gold'])
        database.update_hp_mp(uid, c['health'], c['mana'])
        del battle_sessions[uid]
        
        txt = (f"🏆 *ПОБЕДА!*\n\n"
               f"Монстр повержен.\n"
               f"💰 +{m['gold']} золота\n"
               f"✨ +{m['xp']} опыта")
        
        if lvl_up: txt += "\n\n🆙 *НОВЫЙ УРОВЕНЬ!*"
        
        await query.edit_message_caption(caption=txt, parse_mode='Markdown', reply_markup=kb_main())
        return MAIN_MENU

    # --- ХОД ВРАГА (Только если жив и игрок закончил ход) ---
    if player_turn_done:
        dmg, status = calculate_attack(m['str'], m['agi'], c['agility'])
        
        if dmg > 0:
            if player_defending:
                dmg = dmg // 2
                status += " (Блок)"
            c['health'] -= dmg
            s['log'].append(f"💔 {m['name']} ударил на *{dmg}*. {status}")
        else:
            s['log'].append(f"💨 {m['name']} промахнулся!")
            
        s['turn'] += 1

    # --- ПРОВЕРКА ПОРАЖЕНИЯ ---
    if c['health'] <= 0:
        database.update_hp_mp(uid, 1, c['mana']) # Оставляем 1 хп
        del battle_sessions[uid]
        await query.edit_message_caption("☠️ *ТЕМНОТА...*\nВас нашли без сознания и оттащили в лагерь.", parse_mode='Markdown', reply_markup=kb_main())
        return MAIN_MENU

    database.update_hp_mp(uid, c['health'], c['mana'])
    await render_battle(query, uid)
    return IN_BATTLE

# --- ОСТАЛЬНЫЕ ХЕНДЛЕРЫ (Профиль, Магазин и т.д.) ---

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    char = database.get_character(query.from_user.id)
    
    race_info = database.RACES[char['race']]
    needed = (char['level'] * (char['level'] + 1) * 150) // 2
    
    txt = (f"📜 *Досье Героя*\n\n"
           f"👤 Имя: *{char['character_name']}*\n"
           f"🎭 Раса: {race_info['name']}\n"
           f"🎖 Ранг: *{char['rank']}*\n"
           f"⭐ Уровень: {char['level']} (Опыт: {char['experience']}/{needed})\n\n"
           f"❤️ Здоровье: {char['health']}/{char['max_health']}\n"
           f"🧿 Мана: {char['mana']}/{char['max_mana']}\n"
           f"💰 Золото: {char['gold']}\n\n"
           f"💪 Сила: {char['strength']}  🦶 Ловкость: {char['agility']}\n"
           f"🧠 Интеллект: {char['intelligence']}  🛡 Живучесть: {char['vitality']}")
           
    kb = kb_main().inline_keyboard
    if char['stat_points'] > 0:
        kb.insert(0, [InlineKeyboardButton(f"🌟 ПРОКАЧАТЬ ({char['stat_points']})", callback_data="level_up")])
    
    await query.edit_message_media(
        media=telegram.InputMediaPhoto("https://i.pinimg.com/564x/e3/37/29/e337296068eb4c434997033784033333.jpg", caption=txt, parse_mode='Markdown'),
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return MAIN_MENU

async def level_up(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = [
        [InlineKeyboardButton("💪 Сила", callback_data="up_strength"), InlineKeyboardButton("🦶 Ловкость", callback_data="up_agility")],
        [InlineKeyboardButton("🧠 Интеллект", callback_data="up_intelligence"), InlineKeyboardButton("🛡 Живучесть", callback_data="up_vitality")],
        [InlineKeyboardButton("🔙 Назад", callback_data="profile")]
    ]
    await query.edit_message_caption("Выберите, что улучшить:", reply_markup=InlineKeyboardMarkup(kb))
    return LEVEL_UP

async def stat_up(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    stat = query.data.split('_')[1]
    database.add_stat_point(query.from_user.id, stat)
    await query.answer("Характеристика повышена!")
    await profile(update, context)
    return MAIN_MENU

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = [[InlineKeyboardButton(f"{v['name']} ({v['price']}g)", callback_data=f"buy_{k}")] for k, v in SHOP_ITEMS.items()]
    kb.append([InlineKeyboardButton("🔙 Назад", callback_data="main")])
    
    await query.edit_message_media(
        media=telegram.InputMediaPhoto(IMAGES['shop'], caption="🛒 *Лавка Древностей*\nЗдесь можно купить зелья.", parse_mode='Markdown'),
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return SHOP_MENU

async def buy_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    item_key = query.data.split('_')[1]
    item = SHOP_ITEMS[item_key]
    res, msg = database.buy_item(query.from_user.id, item_key, item['name'], item['price'], item['effect'])
    await query.answer(msg, show_alert=not res)
    return SHOP_MENU

async def inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    items = database.get_inventory(query.from_user.id)
    
    txt = "🎒 *Ваш рюкзак:*\n"
    kb = []
    if items:
        for i in items:
            txt += f"\n📦 {i['item_name']} (x{i['quantity']})"
            kb.append([InlineKeyboardButton(f"Использовать {i['item_name']}", callback_data=f"use_{i['id']}")])
    else:
        txt += "\n_Здесь только пыль..._"
        
    kb.append([InlineKeyboardButton("🔙 Назад", callback_data="main")])
    await query.edit_message_caption(caption=txt, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
    return INVENTORY_MENU

async def use_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    item_id = query.data.split('_')[1]
    res, msg = database.use_inventory_item(query.from_user.id, item_id)
    await query.answer(msg)
    await inventory(update, context)
    return INVENTORY_MENU

async def show_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    top = database.get_top_players()
    txt = "🏆 *ДОСКА ГЕРОЕВ*\n\n"
    for i, p in enumerate(top, 1):
        txt += f"{i}. {p['character_name']} (Ранг {p['rank']}) - {p['gold']}g\n"
    kb = [[InlineKeyboardButton("🔙 Назад", callback_data="main")]]
    await query.edit_message_caption(caption=txt, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
    return MAIN_MENU

async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await update.message.reply_text("Главное меню", reply_markup=kb_main())
    return MAIN_MENU

async def refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Отдыхаем...")
    # Просто перерисовываем профиль, реген сработает внутри get_character
    await profile(update, context)
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
                CallbackQueryHandler(profile, pattern='^profile$'),
                CallbackQueryHandler(inventory, pattern='^inv$'),
                CallbackQueryHandler(show_map, pattern='^map$'), # Переход к карте
                CallbackQueryHandler(shop, pattern='^shop$'),
                CallbackQueryHandler(show_top, pattern='^top$'),
                CallbackQueryHandler(refresh, pattern='^refresh$')
            ],
            LOCATION_MENU: [
                CallbackQueryHandler(show_location, pattern='^go_'),
                CallbackQueryHandler(back_main, pattern='^main$')
            ],
            MOB_MENU: [
                CallbackQueryHandler(start_fight, pattern='^fight_'),
                CallbackQueryHandler(show_map, pattern='^map$')
            ],
            IN_BATTLE: [CallbackQueryHandler(battle_action, pattern='^(atk|mag|def|run|ult)')],
            SHOP_MENU: [
                CallbackQueryHandler(buy_item, pattern='^buy_'),
                CallbackQueryHandler(back_main, pattern='^main$')
            ],
            INVENTORY_MENU: [
                CallbackQueryHandler(use_item, pattern='^use_'),
                CallbackQueryHandler(back_main, pattern='^main$')
            ],
            LEVEL_UP: [
                CallbackQueryHandler(stat_up, pattern='^up_'),
                CallbackQueryHandler(profile, pattern='^profile$')
            ]
        },
        fallbacks=[CommandHandler('start', start)]
    )
    
    app.add_handler(conv)
    print("Бот запущен...")
    app.run_polling()

if __name__ == '__main__':
    main()
