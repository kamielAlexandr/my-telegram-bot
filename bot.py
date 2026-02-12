import os
import logging
import random
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

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
battle_sessions = {}

# --- КОНТЕНТ (КАРТИНКИ И ОПИСАНИЯ) ---
IMAGES = {
    'start': 'https://img.freepik.com/premium-photo/fantasy-medieval-village-tavern_360032-15.jpg',
    'map': 'https://i.pinimg.com/564x/4e/1c/0e/4e1c0e3e26703a553075253106362536.jpg',
    'shop': 'https://i.pinimg.com/564x/1a/1a/1a/1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a.jpg',
    'profile': 'https://i.pinimg.com/564x/e3/37/29/e337296068eb4c434997033784033333.jpg',
    # Локации
    'forest': 'https://i.pinimg.com/736x/2d/7b/72/2d7b72522c009945030222079075727e.jpg',
    'mine': 'https://i.pinimg.com/736x/8a/34/06/8a340632b49673992224772863777722.jpg',
}

# Локации и мобы
LOCATIONS = {
    'forest': {
        'name': '🌲 Гнилой Лес', 'rank': 'E', 'img': IMAGES['forest'],
        'desc': 'Темная чаща, где деревья шепчут проклятия.',
        'mobs': ['rat', 'spider', 'wolf', 'bandit', 'bear']
    },
    'mine': {
        'name': '⛏ Заброшенная Шахта', 'rank': 'E', 'img': IMAGES['mine'],
        'desc': 'Старые туннели, кишащие подземными тварями.',
        'mobs': ['bat', 'kobold', 'slime', 'dwarf_zombie', 'golem']
    }
}

MOBS = {
    'rat': {'name': '🐀 Чумная Крыса', 'lvl': 1, 'hp': 25, 'str': 5, 'agi': 5, 'xp': 10, 'gold': 5, 'img': 'https://i.pinimg.com/564x/f3/d3/de/f3d3de7a56327344073f84307379766d.jpg'},
    'spider': {'name': '🕷 Лесной Паук', 'lvl': 3, 'hp': 35, 'str': 7, 'agi': 10, 'xp': 15, 'gold': 8, 'img': 'https://i.pinimg.com/564x/27/7f/73/277f73db0c202022464736f94793672d.jpg'},
    'wolf': {'name': '🐺 Серый Волк', 'lvl': 5, 'hp': 50, 'str': 10, 'agi': 8, 'xp': 20, 'gold': 12, 'img': 'https://i.pinimg.com/564x/c7/2b/9d/c72b9d034237d6929944372922442c7f.jpg'},
    'bandit': {'name': '🗡 Разбойник', 'lvl': 7, 'hp': 70, 'str': 12, 'agi': 7, 'xp': 30, 'gold': 20, 'img': 'https://i.pinimg.com/564x/7d/87/40/7d8740d2492d52927233267232230206.jpg'},
    'bear': {'name': '🐻 Медведь-Людоед', 'lvl': 10, 'hp': 120, 'str': 15, 'agi': 3, 'xp': 50, 'gold': 35, 'img': 'https://i.pinimg.com/564x/a4/09/8f/a4098f98e87490022723049282387342.jpg'},
    'bat': {'name': '🦇 Летучая Мышь', 'lvl': 2, 'hp': 30, 'str': 4, 'agi': 15, 'xp': 12, 'gold': 6, 'img': 'https://i.pinimg.com/564x/76/01/cc/7601cc3370e7e462d733230a84364024.jpg'},
    'kobold': {'name': '🦎 Кобольд', 'lvl': 4, 'hp': 45, 'str': 8, 'agi': 9, 'xp': 18, 'gold': 10, 'img': 'https://i.pinimg.com/564x/3b/22/e0/3b22e032f30663673c99092497640f8e.jpg'},
    'slime': {'name': '🟢 Слизь', 'lvl': 6, 'hp': 80, 'str': 6, 'agi': 1, 'xp': 25, 'gold': 15, 'img': 'https://i.pinimg.com/564x/c3/84/04/c384048704207908b988f07094200673.jpg'},
    'dwarf_zombie': {'name': '🧟 Зомби-Дварф', 'lvl': 8, 'hp': 100, 'str': 14, 'agi': 2, 'xp': 40, 'gold': 25, 'img': 'https://i.pinimg.com/564x/e7/76/9b/e7769bf4772023023249497e84240742.jpg'},
    'golem': {'name': '🗿 Голем', 'lvl': 12, 'hp': 150, 'str': 20, 'agi': 0, 'xp': 65, 'gold': 50, 'img': 'https://i.pinimg.com/564x/24/76/8f/24768f00030026e99279743936934c20.jpg'},
}

SHOP_ITEMS = {
    'small_hp': {'name': '💊 Зелье HP (+50)', 'price': 30, 'effect': 50},
    'small_mp': {'name': '🔮 Зелье MP (+30)', 'price': 30, 'effect': 30},
}

# Состояния
CHOOSE_RACE, ENTER_NAME, MAIN_MENU, LOCATION_MENU, MOB_MENU, IN_BATTLE, SHOP_MENU, LEVEL_UP, INVENTORY_MENU = range(9)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def calculate_attack(attacker_str, attacker_agi, defender_agi, is_magic=False):
    """Считает урон с шансом попадания и крита"""
    # Шанс попасть: База 90% + разница в ловкости
    hit_chance = 0.90 + ((attacker_agi - defender_agi) * 0.02)
    hit_chance = max(0.40, min(1.0, hit_chance))
    
    if random.random() > hit_chance and not is_magic:
        return 0, "💨 *ПРОМАХ!* (Уклонение)"

    # Шанс крита
    crit_chance = attacker_agi * 0.02
    is_crit = random.random() < crit_chance

    # Урон
    base = attacker_str * (1.5 if is_magic else 0.5)
    dmg = int(base * random.uniform(0.85, 1.15))
    
    status = ""
    if is_crit:
        dmg = int(dmg * 1.5)
        status = "💥 *КРИТ!*"
        
    return max(1, dmg), status

def create_mob(key, player_lvl):
    base = MOBS[key].copy()
    scale = 1 + (player_lvl * 0.05) # +5% статов за уровень игрока
    
    mob = base.copy()
    mob['hp'] = int(base['hp'] * scale)
    mob['max_hp'] = mob['hp']
    mob['str'] = int(base['str'] * scale)
    mob['agi'] = int(base['agi'] * scale)
    mob['exp'] = int(base['xp'] * scale)
    mob['gold'] = int(base['gold'] * scale)
    return mob

async def safe_edit_media(query, media, keyboard):
    """Безопасно меняет картинку. Если старое сообщение было текстом - удаляет и шлет новое."""
    try:
        await query.edit_message_media(media=media, reply_markup=keyboard)
    except Exception:
        # Если старое сообщение не было медиа или устарело
        try:
            await query.delete_message()
        except:
            pass
        await query.message.reply_photo(photo=media.media, caption=media.caption, parse_mode='Markdown', reply_markup=keyboard)

# --- КЛАВИАТУРЫ ---
def kb_main():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📜 Профиль", callback_data="profile"), InlineKeyboardButton("🎒 Мешок", callback_data="inv")],
        [InlineKeyboardButton("🗺 КАРТА МИРА (БОЙ)", callback_data="map")],
        [InlineKeyboardButton("🛖 Торговец", callback_data="shop"), InlineKeyboardButton("🏆 Топ", callback_data="top")],
        [InlineKeyboardButton("💤 Отдых (Реген)", callback_data="refresh")]
    ])

def kb_battle(race_ability):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚔️ Удар", callback_data="atk"), InlineKeyboardButton("🔥 Магия (15 MP)", callback_data="mag")],
        [InlineKeyboardButton("🛡 Блок", callback_data="def"), InlineKeyboardButton(f"✨ {race_ability}", callback_data="ult")],
        [InlineKeyboardButton("🏃 Бежать", callback_data="run")]
    ])

# --- ОБРАБОТЧИКИ ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    char = database.get_character(user.id)
    if char:
        await update.message.reply_photo(IMAGES['start'], caption=f"🍺 Таверна\n\nС возвращением, {char['character_name']}!", reply_markup=kb_main())
        return MAIN_MENU
    
    kb = [[InlineKeyboardButton(r['name'], callback_data=f"race_{k}")] for k, r in database.RACES.items()]
    await update.message.reply_photo(IMAGES['start'], caption="🌑 *НАЧАЛО ПУТИ*\n\nВыбери свое происхождение:", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
    return CHOOSE_RACE

async def choose_race(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    race = query.data.split('_')[1]
    context.user_data['race'] = race
    await query.edit_message_caption(caption=f"Раса: {database.RACES[race]['name']}\n\nКак тебя зовут?", parse_mode='Markdown')
    return ENTER_NAME

async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text[:20]
    user = update.effective_user
    database.create_character(user.id, user.username, name, context.user_data['race'])
    await update.message.reply_photo(IMAGES['start'], caption="✅ Герой создан! Вперед, к приключениям.", reply_markup=kb_main())
    return MAIN_MENU

# --- ОСНОВНЫЕ МЕНЮ ---

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await safe_edit_media(query, InputMediaPhoto(IMAGES['start'], caption="🍺 Главное меню"), kb_main())
    return MAIN_MENU

async def show_map(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    char = database.get_character(query.from_user.id)
    
    kb = []
    # Порядок рангов
    ranks = ['E', 'D', 'C', 'B', 'A', 'S']
    p_rank_idx = ranks.index(char['rank'])
    
    for key, loc in LOCATIONS.items():
        loc_rank_idx = ranks.index(loc['rank'])
        status = "🔓" if loc_rank_idx <= p_rank_idx else "🔒"
        
        if loc_rank_idx <= p_rank_idx:
            kb.append([InlineKeyboardButton(f"{status} {loc['name']}", callback_data=f"go_{key}")])
        else:
            kb.append([InlineKeyboardButton(f"{status} {loc['name']} (Нужен {loc['rank']})", callback_data="locked")])
            
    kb.append([InlineKeyboardButton("🔙 Назад", callback_data="main")])
    
    await safe_edit_media(query, 
        InputMediaPhoto(IMAGES['map'], caption=f"🗺 *КАРТА КОРОЛЕВСТВА*\nТвой ранг: {char['rank']}\n\nВыбери локацию:", parse_mode='Markdown'), 
        InlineKeyboardMarkup(kb))
    return LOCATION_MENU

async def show_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    loc_key = query.data.split('_')[1]
    loc = LOCATIONS[loc_key]
    
    kb = []
    for mob_key in loc['mobs']:
        mob = MOBS[mob_key]
        kb.append([InlineKeyboardButton(f"{mob['name']} (Ур.{mob['lvl']})", callback_data=f"fight_{mob_key}")])
    
    kb.append([InlineKeyboardButton("🔙 На карту", callback_data="map")])
    
    await safe_edit_media(query,
        InputMediaPhoto(loc['img'], caption=f"📍 *{loc['name']}*\n_{loc['desc']}_\n\nКого атакуем?", parse_mode='Markdown'),
        InlineKeyboardMarkup(kb))
    return MOB_MENU

# --- БОЕВАЯ СИСТЕМА ---

async def start_fight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    mob_key = query.data.split('_')[1]
    char = database.get_character(query.from_user.id)
    
    if char['health'] < 10:
        await query.answer("⚠️ Слишком мало здоровья! Иди спать.", show_alert=True)
        return MOB_MENU
        
    mob = create_mob(mob_key, char['level'])
    
    battle_sessions[query.from_user.id] = {
        'char': char, 'mob': mob, 'log': [f"⚔️ *{mob['name']}* заметил вас!"], 'turn': 1
    }
    
    await render_battle(query, query.from_user.id)
    return IN_BATTLE

async def render_battle(query, user_id):
    s = battle_sessions[user_id]
    c, m = s['char'], s['mob']
    
    # Визуализация HP
    c_hp = "🟩" * int((c['health']/c['max_health'])*10) + "⬜" * (10 - int((c['health']/c['max_health'])*10))
    m_hp = "🟥" * int((m['hp']/m['max_hp'])*10) + "⬜" * (10 - int((m['hp']/m['max_hp'])*10))
    
    log = "\n".join(s['log'][-4:])
    
    txt = (f"🔥 *БОЙ - Ход {s['turn']}*\n\n"
           f"👤 *{c['character_name']}* {c['health']} HP\n{c_hp}\n\n"
           f"👺 *{m['name']}* {m['hp']} HP\n{m_hp}\n\n"
           f"📜 {log}")
           
    race_abi = database.RACES[c['race']]['ability'].split(' ')[0]
    
    await safe_edit_media(query, InputMediaPhoto(m['img'], caption=txt, parse_mode='Markdown'), kb_battle(race_abi))

async def battle_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    act = query.data
    
    if uid not in battle_sessions:
        await query.message.reply_text("Бой не найден.")
        return MAIN_MENU
        
    s = battle_sessions[uid]
    c, m = s['char'], s['mob']
    log = s['log']
    
    player_turn_done = False
    player_def = False
    
    # --- ХОД ИГРОКА ---
    if act == "run":
        chance = 0.5 + ((c['agility'] - m['agi']) * 0.02)
        if random.random() < chance:
            del battle_sessions[uid]
            await safe_edit_media(query, InputMediaPhoto(IMAGES['start'], caption="🏃‍♂️ *Успешный побег!*"), kb_main())
            return MAIN_MENU
        else:
            log.append("🚫 Побег не удался!")
            player_turn_done = True
            
    elif act == "atk":
        dmg, stat = calculate_attack(c['strength'], c['agility'], m['agi'])
        if dmg > 0:
            m['hp'] -= dmg
            log.append(f"⚔️ Удар на *{dmg}*. {stat}")
        else:
            log.append(stat)
        player_turn_done = True
        
    elif act == "mag":
        if c['mana'] >= 15:
            c['mana'] -= 15
            dmg, stat = calculate_attack(c['intelligence'], c['agility'], m['agi']//2, is_magic=True)
            m['hp'] -= dmg
            log.append(f"🔥 Магия на *{dmg}*! {stat}")
            player_turn_done = True
        else:
            log.append("❌ Нет маны!")
            
    elif act == "def":
        player_def = True
        log.append("🛡 Защитная стойка.")
        player_turn_done = True
        
    elif act == "ult":
        if c['mana'] >= 30:
            c['mana'] -= 30
            # Упрощенная логика ульты
            m['hp'] -= c['strength'] * 2
            log.append("✨ *СУПЕРУДАР!*")
            player_turn_done = True
        else:
            log.append("❌ Нужно 30 MP!")

    # --- ПРОВЕРКА ПОБЕДЫ ---
    if m['hp'] <= 0:
        lvl, new_rank = database.add_rewards(uid, m['exp'], m['gold'])
        database.update_hp_mp(uid, c['health'], c['mana'])
        del battle_sessions[uid]
        
        txt = f"🏆 *ПОБЕДА!*\n\n💰 +{m['gold']} золота\n✨ +{m['exp']} опыта"
        if lvl: txt += "\n\n🆙 *НОВЫЙ УРОВЕНЬ!*"
        
        await safe_edit_media(query, InputMediaPhoto(IMAGES['start'], caption=txt, parse_mode='Markdown'), kb_main())
        return MAIN_MENU

    # --- ХОД ВРАГА ---
    if player_turn_done:
        dmg, stat = calculate_attack(m['str'], m['agi'], c['agility'])
        if dmg > 0:
            if player_def: dmg //= 2
            c['health'] -= dmg
            log.append(f"💔 Враг нанес *{dmg}*. {stat}")
        else:
            log.append("💨 Враг промахнулся!")
        s['turn'] += 1

    # --- ПРОВЕРКА ПОРАЖЕНИЯ ---
    if c['health'] <= 0:
        database.update_hp_mp(uid, 1, c['mana'])
        del battle_sessions[uid]
        await safe_edit_media(query, InputMediaPhoto(IMAGES['start'], caption="☠️ *ВЫ ПОГИБЛИ...*"), kb_main())
        return MAIN_MENU

    database.update_hp_mp(uid, c['health'], c['mana'])
    await render_battle(query, uid)
    return IN_BATTLE

# --- ПРОФИЛЬ, МАГАЗИН, ТОП ---

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    char = database.get_character(query.from_user.id)
    
    txt = (f"👤 *{char['character_name']}* | {char['rank']}-ранг\n"
           f"❤️ {char['health']}/{char['max_health']}  🧿 {char['mana']}/{char['max_mana']}\n"
           f"💰 {char['gold']}g  ⭐ Ур.{char['level']}\n\n"
           f"💪 {char['strength']} 🦶 {char['agility']} 🧠 {char['intelligence']} 🛡 {char['vitality']}")
           
    kb = kb_main().inline_keyboard
    if char['stat_points'] > 0: kb.insert(0, [InlineKeyboardButton(f"🌟 Прокачать ({char['stat_points']})", callback_data="levelup")])
    
    await safe_edit_media(query, InputMediaPhoto(IMAGES['profile'], caption=txt, parse_mode='Markdown'), InlineKeyboardMarkup(kb))
    return MAIN_MENU

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = [[InlineKeyboardButton(f"{v['name']} ({v['price']}g)", callback_data=f"buy_{k}")] for k, v in SHOP_ITEMS.items()]
    kb.append([InlineKeyboardButton("🔙 Назад", callback_data="main")])
    await safe_edit_media(query, InputMediaPhoto(IMAGES['shop'], caption="🛒 *Лавка*", parse_mode='Markdown'), InlineKeyboardMarkup(kb))
    return SHOP_MENU

async def buy_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    key = query.data.split('_')[1]
    item = SHOP_ITEMS[key]
    res, msg = database.buy_item(query.from_user.id, key, item['name'], item['price'], item['effect'])
    await query.answer(msg, show_alert=not res)
    return SHOP_MENU

async def level_up(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = [
        [InlineKeyboardButton("💪 Сила", callback_data="up_strength"), InlineKeyboardButton("🦶 Ловкость", callback_data="up_agility")],
        [InlineKeyboardButton("🧠 Интеллект", callback_data="up_intelligence"), InlineKeyboardButton("🛡 Живучесть", callback_data="up_vitality")],
        [InlineKeyboardButton("🔙 Назад", callback_data="profile")]
    ]
    await query.edit_message_caption("Что улучшаем?", reply_markup=InlineKeyboardMarkup(kb))
    return LEVEL_UP

async def stat_up(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    stat = query.data.split('_')[1]
    database.add_stat_point(query.from_user.id, stat)
    await query.answer("Готово!")
    await profile(update, context)
    return MAIN_MENU

async def inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    items = database.get_inventory(query.from_user.id)
    txt = "🎒 *Рюкзак:*\n" + ("_Пусто_" if not items else "")
    kb = []
    for i in items:
        txt += f"\n📦 {i['item_name']} (x{i['quantity']})"
        kb.append([InlineKeyboardButton(f"Юз {i['item_name']}", callback_data=f"use_{i['id']}")])
    kb.append([InlineKeyboardButton("🔙 Назад", callback_data="main")])
    await safe_edit_media(query, InputMediaPhoto(IMAGES['profile'], caption=txt, parse_mode='Markdown'), InlineKeyboardMarkup(kb))
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
    txt = "🏆 *ТОП ИГРОКОВ*\n\n"
    for i, p in enumerate(top, 1):
        txt += f"{i}. {p['character_name']} (Ранг {p['rank']}) - {p['gold']}g\n"
    kb = [[InlineKeyboardButton("🔙 Назад", callback_data="main")]]
    await safe_edit_media(query, InputMediaPhoto(IMAGES['start'], caption=txt, parse_mode='Markdown'), InlineKeyboardMarkup(kb))
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
                CallbackQueryHandler(show_map, pattern='^map$'),
                CallbackQueryHandler(shop, pattern='^shop$'),
                CallbackQueryHandler(inventory, pattern='^inv$'),
                CallbackQueryHandler(show_top, pattern='^top$'),
                CallbackQueryHandler(profile, pattern='^refresh$')
            ],
            LOCATION_MENU: [
                CallbackQueryHandler(show_location, pattern='^go_'),
                CallbackQueryHandler(back_to_main, pattern='^main$'),
                CallbackQueryHandler(lambda u,c: u.callback_query.answer("🔒 Ранг мал!", show_alert=True), pattern='^locked$')
            ],
            MOB_MENU: [
                CallbackQueryHandler(start_fight, pattern='^fight_'),
                CallbackQueryHandler(show_map, pattern='^map$')
            ],
            IN_BATTLE: [CallbackQueryHandler(battle_action, pattern='^(atk|mag|def|run|ult)')],
            SHOP_MENU: [CallbackQueryHandler(buy_item, pattern='^buy_'), CallbackQueryHandler(back_to_main, pattern='^main$')],
            INVENTORY_MENU: [CallbackQueryHandler(use_item, pattern='^use_'), CallbackQueryHandler(back_to_main, pattern='^main$')],
            LEVEL_UP: [CallbackQueryHandler(stat_up, pattern='^up_'), CallbackQueryHandler(profile, pattern='^profile$')]
        },
        fallbacks=[CommandHandler('start', start)]
    )
    
    app.add_handler(conv)
    print("Бот запущен...")
    app.run_polling()

if __name__ == '__main__':
    main()
