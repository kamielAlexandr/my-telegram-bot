import os
import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters
import database as db

logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

CHOOSE_RACE, ENTER_NAME, MAIN_MENU, BATTLE_MENU, IN_BATTLE, INVENTORY_MENU, SHOP_MENU = range(7)

# --- КЛАВИАТУРЫ ---
def get_main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📜 Профиль", callback_data='profile'), InlineKeyboardButton("🎒 Рюкзак", callback_data='inventory')],
        [InlineKeyboardButton("⚔️ В БОЙ", callback_data='battle_menu'), InlineKeyboardButton("🛍 Лавка", callback_data='shop')],
        [InlineKeyboardButton("🔄 Рестарт", callback_data='restart')]
    ])

def get_battle_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚔️ УДАР", callback_data='attack'), InlineKeyboardButton("🛡️ БЛОК", callback_data='defend')],
        [InlineKeyboardButton("💊 ЗЕЛЬЕ", callback_data='use_potion'), InlineKeyboardButton("🏃 ПОБЕГ", callback_data='flee')]
    ])

# --- ЛОГИКА ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.init_db()
    char = db.get_character(update.effective_user.id)
    if char:
        await update.message.reply_text(f"С возвращением, {char['character_name']}!", reply_markup=get_main_menu_keyboard())
        return MAIN_MENU
    await update.message.reply_text("Выбери расу:", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("Человек", callback_data='race_human'), InlineKeyboardButton("Эльф", callback_data='race_elf')],
        [InlineKeyboardButton("Дварф", callback_data='race_dwarf'), InlineKeyboardButton("Орк", callback_data='race_orc')]
    ]))
    return CHOOSE_RACE

async def race_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['selected_race'] = query.data.replace('race_', '')
    await query.message.reply_text("Как назовем героя?")
    return ENTER_NAME

async def name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text[:20]
    db.create_character(update.effective_user.id, name, context.user_data['selected_race'])
    await update.message.reply_text(f"Герой {name} создан!", reply_markup=get_main_menu_keyboard())
    return MAIN_MENU

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id

    if query.data == 'profile':
        c = db.get_character(uid)
        await query.message.reply_text(f"👤 {c['character_name']}\n⭐ Лвл: {c['level']}\n💪 Сила: {c['strength']}+{c['equip_str']}\n🏹 Ловкость: {c['agility']}\n❤️ HP: {c['health']}/{c['max_health']}\n💰 Золото: {c['gold']}", reply_markup=get_main_menu_keyboard())
    
    elif query.data == 'inventory':
        inv = db.get_inventory(uid)
        if not inv: 
            await query.message.reply_text("Пусто!", reply_markup=get_main_menu_keyboard())
            return MAIN_MENU
        kb = [[InlineKeyboardButton(f"{'✅' if i['is_equipped'] else ''} {i['name']}", callback_data=f"eq_{i['id']}")] for i in inv]
        kb.append([InlineKeyboardButton("🔙 Назад", callback_data='back')])
        await query.message.edit_text("Твои вещи:", reply_markup=InlineKeyboardMarkup(kb))
        return INVENTORY_MENU

    elif query.data == 'shop':
        items = db.get_shop_items()
        kb = [[InlineKeyboardButton(f"{i['name']} ({i['price']}💰)", callback_data=f"buy_{i['id']}")] for i in items]
        kb.append([InlineKeyboardButton("🔙 Назад", callback_data='back')])
        await query.message.edit_text("Лавка:", reply_markup=InlineKeyboardMarkup(kb))
        return SHOP_MENU

    elif query.data == 'battle_menu':
        kb = [[InlineKeyboardButton("🐺 Волк", callback_data='btl_wolf')], [InlineKeyboardButton("🔙 Назад", callback_data='back')]]
        await query.message.edit_text("Выбери врага:", reply_markup=InlineKeyboardMarkup(kb))
        return BATTLE_MENU
    
    return MAIN_MENU

async def shop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'back': return await start(update, context)
    item_id = query.data.split('_')[1]
    success, msg = db.buy_item(query.from_user.id, item_id)
    await query.message.reply_text(msg, reply_markup=get_main_menu_keyboard())
    return MAIN_MENU

async def inv_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'back': return await start(update, context)
    db.equip_item(query.from_user.id, query.data.split('_')[1])
    await query.message.reply_text("Снаряжение изменено!", reply_markup=get_main_menu_keyboard())
    return MAIN_MENU

# --- БИТВА ---
async def battle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    char = db.get_character(uid)
    
    # Масштабирование врага под уровень игрока
    lvl = char['level']
    enemy = {'name': 'Монстр', 'hp': 30 + (lvl * 10), 'dmg': (3 + lvl, 7 + lvl), 'exp': 20 + lvl, 'gold': 15 + lvl}
    
    context.user_data['btl'] = {'e_hp': enemy['hp'], 'c_hp': char['health'], 'e': enemy}
    await query.message.reply_text(f"⚔️ Бой с {enemy['name']} (Lvl {lvl})!", reply_markup=get_battle_keyboard())
    return IN_BATTLE

async def battle_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    btl = context.user_data['btl']
    char = db.get_character(uid)
    log = []

    if query.data == 'use_potion':
        success, heal = db.use_healing_potion(uid)
        if success: 
            btl['c_hp'] = min(char['max_health'], btl['c_hp'] + heal)
            log.append(f"💊 Восстановил {heal} HP")
        else: log.append("❌ Нет зелий!")
    
    elif query.data == 'attack':
        # Критический удар (шанс зависит от ловкости)
        crit = 2 if random.random() < (char['agility'] / 100) else 1
        dmg = random.randint(char['strength'] // 2, char['strength'] + char['equip_str']) * crit
        btl['e_hp'] -= dmg
        log.append(f"{'⚡️ КРИТ! ' if crit > 1 else ''}Ты ударил на {dmg}")

    if btl['e_hp'] > 0:
        e_dmg = random.randint(*btl['e']['dmg'])
        actual_dmg = max(1, e_dmg - char['equip_def'])
        btl['c_hp'] -= actual_dmg
        log.append(f"👹 Враг ударил на {actual_dmg}")

    if btl['c_hp'] <= 0:
        db.update_character_stats(uid, health=1, battle_losses=char['battle_losses']+1)
        await query.message.edit_text("💀 Ты проиграл!", reply_markup=get_main_menu_keyboard())
        return MAIN_MENU
    
    if btl['e_hp'] <= 0:
        lvl_up = db.add_experience(uid, btl['e']['exp'])
        db.add_gold(uid, btl['e']['gold'])
        db.update_character_stats(uid, health=btl['c_hp'], battle_wins=char['battle_wins']+1)
        txt = f"🏆 Победа! +{btl['e']['exp']} XP, +{btl['e']['gold']}💰"
        if lvl_up: txt += "\n🌟 НОВЫЙ УРОВЕНЬ!"
        await query.message.edit_text(txt, reply_markup=get_main_menu_keyboard())
        return MAIN_MENU

    await query.message.edit_text(f"❤️ Твое HP: {btl['c_hp']}\n👹 HP Врага: {btl['e_hp']}\n\n" + "\n".join(log), reply_markup=get_battle_keyboard())
    return IN_BATTLE

def main():
    app = Application.builder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSE_RACE: [CallbackQueryHandler(race_callback)],
            ENTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_handler)],
            MAIN_MENU: [CallbackQueryHandler(menu_handler)],
            INVENTORY_MENU: [CallbackQueryHandler(inv_callback)],
            SHOP_MENU: [CallbackQueryHandler(shop_callback)],
            BATTLE_MENU: [CallbackQueryHandler(battle_start)],
            IN_BATTLE: [CallbackQueryHandler(battle_logic)],
        },
        fallbacks=[CommandHandler('start', start)]
    )
    app.add_handler(conv)
    app.run_polling()

if __name__ == '__main__':
    main()
