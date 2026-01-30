import telebot
from telebot import types
import json
import os
import datetime
import traceback
import logging
import time
# ================== НАСТРОЙКИ ==================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
# ================== НАСТРОЙКИ ==================
# Используем переменную окружения
#try:
#   from flask import Flask
 #   from threading import Thread
#
 #   app = Flask('')

 #   @app.route('/')
#    def home():
  #      return "✅ Бот активен! 🎮 Прокачка Героя работает!"

   # def run():
    #    app.run(host='0.0.0.0', port=8080)
#

# ================== НАСТРОЙКИ ==================
# Получаем токен из переменных окружения Replit

BOT_TOKEN = os.environ.get('BOT_TOKEN')

# КРИТИЧЕСКИ ВАЖНО: если токена нет, бот должен остановиться с понятной ошибкой
if BOT_TOKEN is None or BOT_TOKEN == "":
    print("❌ КРИТИЧЕСКАЯ ОШИБКА: Переменная окружения 'BOT_TOKEN' не найдена или пуста.")
    print("   Убедитесь, что вы добавили её в настройки проекта Railway (вкладка Variables).")
    exit(1)  # Завершаем выполнение с кодом ошибки

# Если мы здесь, токен есть
print("✅ Токен бота успешно загружен из переменных окружения.")
bot = telebot.TeleBot(BOT_TOKEN)

# ================== БАЗА ДАННЫХ ==================
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get_user_data(user_id):
    data = load_data()
    user_id_str = str(user_id)

    # Если пользователь новый - создаем для него запись
    if user_id_str not in data:
        data[user_id_str] = {
            'name': 'Новичок',
            'level': 1,
            'max_health': 100,      # Максимальное здоровье
            'current_health': 100,   # Текущее здоровье
            'attack': 10,
            'defense': 5,
            'points': 5,
            'gold': 100,
            'experience': 0,
            'exp_to_next_level': 50,
            'daily_battles': 10,
            'battles_used': 0,
            'last_battle_date': None,
            'inventory': {           # Инвентарь для еды
                'малое зелье': 0,
                'среднее зелье': 0,
                'большое зелье': 0
            }
        }
        save_data(data)
    else:
        # Для существующих пользователей обновляем структуру
        user_record = data[user_id_str]

        # Миграция: если есть старое поле 'health', преобразуем его
        if 'health' in user_record and 'max_health' not in user_record:
            user_record['max_health'] = user_record['health']
            user_record['current_health'] = user_record['health']
            del user_record['health']

        # Добавляем недостающие поля
        if 'max_health' not in user_record:
            user_record['max_health'] = 100
        if 'current_health' not in user_record:
            user_record['current_health'] = user_record.get('max_health', 100)
        if 'inventory' not in user_record:
            user_record['inventory'] = {
                'малое зелье': 0,
                'среднее зелье': 0,
                'большое зелье': 0
            }

        # Стандартные проверки других полей
        if 'daily_battles' not in user_record:
            user_record['daily_battles'] = 10
        if 'battles_used' not in user_record:
            user_record['battles_used'] = 0
        if 'last_battle_date' not in user_record:
            user_record['last_battle_date'] = None

        save_data(data)

    return data[user_id_str]
def update_user_data(user_id, new_data):
    data = load_data()
    data[str(user_id)] = new_data
    save_data(data)


def check_daily_limit(user_id, user_data):
    """Проверяет и сбрасывает дневной лимит сражений при смене дня."""
    today = datetime.datetime.now().strftime('%Y-%m-%d')

    # Гарантируем, что поле существует
    if 'last_battle_date' not in user_data:
        user_data['last_battle_date'] = None

    # Если это первый бой сегодня или сменился день
    if user_data['last_battle_date'] != today:
        user_data['battles_used'] = 0
        user_data['last_battle_date'] = today
        # Сохраняем изменения в базу
        update_user_data(user_id, user_data)

    return user_data


# ================== КОМАНДЫ БОТА ==================
@bot.message_handler(commands=['start', 'старт'])
def send_welcome(message):
    user_id = message.from_user.id

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton('👤 Мой персонаж')
    btn2 = types.KeyboardButton('⚔️ Прокачка')
    btn3 = types.KeyboardButton('🎮 Сразиться с монстром')
    btn4 = types.KeyboardButton('🍖 Использовать зелье')  # Новая кнопка
    btn5 = types.KeyboardButton('🛒 Магазин')            # Новая кнопка
    btn6 = types.KeyboardButton('🏆 Топ игроков')
    btn7 = types.KeyboardButton('🆘 Помощь')
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7)

    welcome_text = """
🎮 Добро пожаловать в игру «Прокачка Героя»!

Создан ваш первый персонаж!
Используйте кнопки ниже для управления игрой.

✨ Доступные команды:
• 👤 Мой персонаж - показать характеристики
• ⚔️ Прокачка - улучшить характеристики
• 🎮 Сразиться с монстром - заработать опыт и золото
• 🏆 Топ игроков - посмотреть лучших игроков
• 🆘 Помощь - справка по игре

У вас есть 5 очков улучшения. Улучшайте своего героя!
    """

    get_user_data(user_id)

    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)


@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
🆘 Помощь по игре:

👤 Мой персонаж - показать характеристики персонажа
⚔️ Прокачка - улучшить характеристики (здоровье, атаку, защиту)
🎮 Сразиться с монстром - сразиться с монстром, чтобы получить опыт и золото
🏆 Топ игроков - посмотреть топ-5 игроков по уровню

📊 Характеристики:
• ❤️ Здоровье - сколько урона может получить персонаж
• ⚔️ Атака - сколько урона наносит персонаж
• 🛡️ Защита - снижает получаемый урон
• ⭐ Уровень - чем выше уровень, тем сильнее монстры
• 💰 Золото - нужно для улучшений
• 🎯 Опыт - для повышения уровня

Каждое повышение уровня дает 3 очка улучшения!
    """
    bot.reply_to(message, help_text)



#ФУНКЦИЯ ПО ТОПУ ИГРОКОВ
@bot.message_handler(func=lambda message: message.text == '🏆 Топ игроков')
def show_top_players(message):
    """Показывает топ-5 игроков."""
    try:
        data = load_data()

        if not data:
            bot.send_message(message.chat.id, "📭 Пока нет игроков в рейтинге!")
            return

        players_list = []
        for user_id_str, player_data in data.items():
            try:
                # Безопасное извлечение данных
                level = player_data.get('level', 1)

                # Определяем отображение здоровья
                if 'current_health' in player_data and 'max_health' in player_data:
                    health_display = f"{player_data['current_health']}/{player_data['max_health']}"
                elif 'health' in player_data:
                    health_display = str(player_data['health'])
                else:
                    health_display = "0/100"

                players_list.append({
                    'level': level,
                    'health': health_display,
                    'attack': player_data.get('attack', 0),
                    'defense': player_data.get('defense', 0),
                    'gold': player_data.get('gold', 0),
                    'experience': player_data.get('experience', 0),
                    'exp_to_next_level': player_data.get('exp_to_next_level', 50)
                })
            except:
                continue  # Пропускаем игроков с некорректными данными

        # Сортируем по уровню и опыту
        sorted_players = sorted(
            players_list,
            key=lambda x: (x['level'], x['experience']),
            reverse=True
        )[:5]

        if not sorted_players:
            bot.send_message(message.chat.id, "📭 Пока нет игроков в рейтинге!")
            return

        top_text = "🏆 *Топ-5 игроков*\n\n"

        for i, player in enumerate(sorted_players, 1):
            top_text += f"{i}. Уровень {player['level']} | ❤️ {player['health']}\n"
            top_text += f"   ⚔️ {player['attack']} | 🛡️ {player['defense']} | 💰 {player['gold']} золота\n\n"

        bot.send_message(message.chat.id, top_text, parse_mode='Markdown')

    except Exception as e:
        print(f"Ошибка в show_top_players: {e}")
        bot.send_message(message.chat.id, "⚠️ Произошла ошибка при загрузке рейтинга. Попробуйте позже.")



# ================== ОСНОВНЫЕ ФУНКЦИИ ==================
@bot.message_handler(func=lambda message: message.text == '👤 Мой персонаж')
def show_character(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)

    user_data = check_daily_limit(user_id, user_data)  # <-- ИСПРАВЛЕНО
    update_user_data(user_id, user_data)

    exp_progress = min(
        100,
        int((user_data['experience'] / user_data['exp_to_next_level']) * 100))
    progress_bar = "▓" * (exp_progress // 10) + "░" * (10 - exp_progress // 10)

    battles_used = user_data['battles_used']
    daily_battles = user_data['daily_battles']
    battles_bar = "▓" * (battles_used) + "░" * (daily_battles - battles_used)

    character_text = f"""
    👤 *Ваш персонаж: {user_data['name']}*

    📊 *Характеристики:*
    • ⭐ Уровень: {user_data['level']}
    • ❤️ Здоровье: {user_data['current_health']}/{user_data['max_health']}
    • ⚔️ Атака: {user_data['attack']}
    • 🛡️ Защита: {user_data['defense']}

    🎯 *Опыт:* {user_data['experience']}/{user_data['exp_to_next_level']}
    {progress_bar} ({exp_progress}%)

    ⚔️ *Сражения сегодня:* {battles_used}/{daily_battles}
    {battles_bar}

    💰 *Золото:* {user_data['gold']}
    🎁 *Очки улучшений:* {user_data['points']}

    *Инвентарь зелий:* {sum(user_data['inventory'].values())} шт.
    """

    bot.send_message(message.chat.id, character_text, parse_mode='Markdown')





@bot.message_handler(func=lambda message: message.text == '⚔️ Прокачка')
def upgrade_menu(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)

    if user_data['points'] <= 0:
        bot.send_message(
            message.chat.id,
            "❌ У вас нет очков улучшения!\n\nЗаработайте опыт, сражаясь с монстрами."
        )
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton(f'❤️ Здоровье (+10) - 1 очко',
                                      callback_data='upgrade_health')
    btn2 = types.InlineKeyboardButton(f'⚔️ Атака (+5) - 1 очко',
                                      callback_data='upgrade_attack')
    btn3 = types.InlineKeyboardButton(f'🛡️ Защита (+3) - 1 очко',
                                      callback_data='upgrade_defense')
    btn4 = types.InlineKeyboardButton(f'❌ Отмена',
                                      callback_data='cancel_upgrade')
    markup.add(btn1, btn2, btn3, btn4)

    upgrade_text = f"""
⚔️ *Улучшение характеристик*

У вас есть *{user_data['points']}* очков улучшения.

Выберите характеристику для улучшения:

• ❤️ Здоровье: {user_data['current_health']}/{user_data['max_health']}
• ⚔️ Атака: {user_data['attack']}
• 🛡️ Защита: {user_data['defense']}

Каждое улучшение стоит 1 очко.
    """

    bot.send_message(message.chat.id,
                     upgrade_text,
                     parse_mode='Markdown',
                     reply_markup=markup)






@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    user_data = get_user_data(user_id)

    # ===== ПОКУПКА ПРЕДМЕТОВ =====
    if call.data.startswith('buy_'):
        item_name = call.data[4:]  # Убираем 'buy_'

        # Стоимость и лечение для каждого предмета
        shop_items = {
            'малое зелье': {'price': 10, 'heal': 20},
            'среднее зелье': {'price': 50, 'heal': 50},
            'большое зелье': {'price': 100, 'heal': 100},
            'полное лечение': {'price': 200, 'heal': user_data['max_health']}
        }

        if item_name not in shop_items:
            bot.answer_callback_query(call.id, "❌ Такого предмета нет в магазине!")
            return

        item = shop_items[item_name]

        # Проверяем хватает ли золота
        if user_data['gold'] < item['price']:
            bot.answer_callback_query(call.id, f"❌ Недостаточно золота! Нужно {item['price']}💰")
            return

        # Покупаем предмет
        user_data['gold'] -= item['price']

        if item_name == 'полное лечение':
            # Немедленное лечение
            user_data['current_health'] = user_data['max_health']
            bot.answer_callback_query(call.id, f"✅ Вы полностью вылечились! Здоровье: {user_data['current_health']}/{user_data['max_health']}")
        else:
            # Добавляем зелье в инвентарь
            user_data['inventory'][item_name] += 1
            bot.answer_callback_query(call.id, f"✅ Куплено 1 {item_name}! Теперь у вас {user_data['inventory'][item_name]} шт.")

        update_user_data(user_id, user_data)

        # Обновляем сообщение магазина
        shop_text = f"""
✅ *Покупка успешна!*

*Ваши ресурсы:*
💰 Золото: {user_data['gold']}
❤️ Здоровье: {user_data['current_health']}/{user_data['max_health']}

*Инвентарь:*
🥫 Малое зелье: {user_data['inventory']['малое зелье']} шт.
🍖 Среднее зелье: {user_data['inventory']['среднее зелье']} шт.
🍗 Большое зелье: {user_data['inventory']['большое зелье']} шт.

Используйте кнопку '🍖 Использовать зелье' для лечения.
        """

        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=shop_text,
                parse_mode='Markdown',
                reply_markup=call.message.reply_markup  # Сохраняем кнопки магазина
            )
        except:
            pass  # Если не удалось обновить сообщение - ничего страшного

    # ===== ИСПОЛЬЗОВАНИЕ ЗЕЛЬЯ =====
    elif call.data.startswith('use_'):
        item_name = call.data[4:]  # Убираем 'use_'

        if item_name not in user_data['inventory']:
            bot.answer_callback_query(call.id, "❌ У вас нет такого зелья!")
            return

        if user_data['inventory'][item_name] <= 0:
            bot.answer_callback_query(call.id, "❌ У вас нет такого зелья!")
            return

        # Определяем сколько лечит зелье
        heal_amount = {
            'малое зелье': 20,
            'среднее зелье': 50,
            'большое зелье': 100
        }[item_name]

        # Применяем зелье
        user_data['inventory'][item_name] -= 1
        new_health = min(user_data['current_health'] + heal_amount, user_data['max_health'])
        health_gained = new_health - user_data['current_health']
        user_data['current_health'] = new_health

        update_user_data(user_id, user_data)

        bot.answer_callback_query(call.id, f"✅ Использовано {item_name}! +{health_gained} HP")

        # Показываем обновленный инвентарь
        inv_text = f"""
🍖 *Использование зелья*

✅ Использовано *{item_name}* (+{health_gained} HP)

❤️ *Текущее здоровье:* {user_data['current_health']}/{user_data['max_health']}

*Ваш инвентарь:*
🥫 Малое зелье: {user_data['inventory']['малое зелье']} шт.
🍖 Среднее зелье: {user_data['inventory']['среднее зелье']} шт.
🍗 Большое зелье: {user_data['inventory']['большое зелье']} шт.

Что вы хотите сделать дальше?
        """

        markup = types.InlineKeyboardMarkup()
        if user_data['inventory']['малое зелье'] > 0:
            markup.add(types.InlineKeyboardButton('🥫 Использовать малое зелье', callback_data='use_малое зелье'))
        if user_data['inventory']['среднее зелье'] > 0:
            markup.add(types.InlineKeyboardButton('🍖 Использовать среднее зелье', callback_data='use_среднее зелье'))
        if user_data['inventory']['большое зелье'] > 0:
            markup.add(types.InlineKeyboardButton('🍗 Использовать большое зелье', callback_data='use_большое зелье'))
        markup.add(types.InlineKeyboardButton('🛒 Купить еще зелий', callback_data='open_shop'))
        markup.add(types.InlineKeyboardButton('❌ Закрыть', callback_data='close_inventory'))

        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=inv_text,
                parse_mode='Markdown',
                reply_markup=markup
            )
        except:
            pass

    # ===== ОТКРЫТЬ МАГАЗИН =====
    elif call.data == 'open_shop':
        bot.answer_callback_query(call.id, "🛒 Открываем магазин...")
        shop_menu(call.message)

    # ===== ЗАКРЫТЬ МАГАЗИН =====
    elif call.data == 'close_shop' or call.data == 'close_inventory':
        bot.answer_callback_query(call.id, "❌ Закрыто")
        bot.delete_message(call.message.chat.id, call.message.message_id)

    # ===== СТАРЫЕ ОБРАБОТЧИКИ (улучшение характеристик) =====
    elif call.data == 'upgrade_health':
        if user_data['points'] <= 0:
            bot.answer_callback_query(call.id, "❌ У вас нет очков улучшения!")
            return

        user_data['points'] -= 1
        user_data['max_health'] += 20  # Увеличиваем максимальное здоровье
        user_data['current_health'] += 20  # И текущее тоже увеличиваем
        update_user_data(user_id, user_data)

        bot.answer_callback_query(call.id, "✅ Макс. здоровье улучшено на 20 единиц!")
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"✅ Здоровье улучшено!\n\n❤️ Теперь у вас {user_data['current_health']}/{user_data['max_health']} здоровья.\n🎁 Осталось очков: {user_data['points']}",
            reply_markup=None
        )

    elif call.data == 'upgrade_attack':
        if user_data['points'] <= 0:
            bot.answer_callback_query(call.id, "❌ У вас нет очков улучшения!")
            return

        user_data['points'] -= 1
        user_data['attack'] += 5
        update_user_data(user_id, user_data)

        bot.answer_callback_query(call.id, "✅ Атака улучшена на 5 единиц!")
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=
            f"✅ Атака улучшена!\n\nТеперь у вас {user_data['attack']} атаки.\nОсталось очков: {user_data['points']}",
            reply_markup=None)

    elif call.data == 'upgrade_defense':
        if user_data['points'] <= 0:
            bot.answer_callback_query(call.id, "❌ У вас нет очков улучшения!")
            return

        user_data['points'] -= 1
        user_data['defense'] += 3
        update_user_data(user_id, user_data)

        bot.answer_callback_query(call.id, "✅ Защита улучшена на 3 единицы!")
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=
            f"✅ Защита улучшена!\n\nТеперь у вас {user_data['defense']} защиты.\nОсталось очков: {user_data['points']}",
            reply_markup=None)

    elif call.data == 'cancel_upgrade':
        bot.answer_callback_query(call.id, "❌ Улучшение отменено")
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=
            "❌ Улучшение отменено.\n\nВы можете вернуться к улучшениям позже.",
            reply_markup=None)






@bot.message_handler(func=lambda message: message.text == '🍖 Использовать зелье')
def use_potion_menu(message):
    """Показывает инвентарь для использования зелий."""
    user_id = message.from_user.id
    user_data = get_user_data(user_id)

    # Проверяем, есть ли зелья
    total_potions = sum(user_data['inventory'].values())
    if total_potions == 0:
        bot.send_message(message.chat.id, "🍃 Ваш инвентарь пуст! Зайдите в 🛒 Магазин, чтобы купить зелья.")
        return

    markup = types.InlineKeyboardMarkup()

    # Создаем кнопки только для тех зелий, которые есть в инвентаре
    potions = [
        ('🥫 Малое зелье', 'малое зелье', 20),
        ('🍖 Среднее зелье', 'среднее зелье', 50),
        ('🍗 Большое зелье', 'большое зелье', 100)
    ]

    for emoji, name, heal in potions:
        if user_data['inventory'][name] > 0:
            btn = types.InlineKeyboardButton(
                f'{emoji} {name} (+{heal} HP) - {user_data["inventory"][name]} шт.', 
                callback_data=f'use_{name}'
            )
            markup.add(btn)

    markup.add(types.InlineKeyboardButton('🛒 Купить еще зелий', callback_data='open_shop'))
    markup.add(types.InlineKeyboardButton('❌ Закрыть', callback_data='close_inventory'))

    inventory_text = f"""
🍖 *Использование зелья*

❤️ *Текущее здоровье:* {user_data['current_health']}/{user_data['max_health']}

*Ваш инвентарь:*
🥫 Малое зелье: {user_data['inventory']['малое зелье']} шт.
🍖 Среднее зелье: {user_data['inventory']['среднее зелье']} шт.
🍗 Большое зелье: {user_data['inventory']['большое зелье']} шт.

Выберите зелье для использования:
    """

    bot.send_message(message.chat.id, inventory_text, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == '🛒 Магазин')
def shop_menu(message):
    """Показывает магазин с едой для лечения."""
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # Предметы для покупки: название, лечение, цена
    items = [
        ('🥫 Малое зелье', 'малое зелье', 10, 20),
        ('🍖 Среднее зелье', 'среднее зелье', 25, 50),
        ('🍗 Большое зелье', 'большое зелье', 50, 100),
        ('❤️ Полное лечение', 'полное лечение', user_data['max_health'], 200)
    ]
    
    for emoji, name, heal, price in items:
        btn = types.InlineKeyboardButton(
            f'{emoji} {name} (+{heal} HP) - {price}💰', 
            callback_data=f'buy_{name}'
        )
        markup.add(btn)
    
    markup.add(types.InlineKeyboardButton('❌ Закрыть магазин', callback_data='close_shop'))
    
    shop_text = f"""
🛒 *Магазин лечебных предметов*

*Ваши ресурсы:*
💰 Золото: {user_data['gold']}
❤️ Здоровье: {user_data['current_health']}/{user_data['max_health']}

*Инвентарь:*
🥫 Малое зелье: {user_data['inventory']['малое зелье']} шт.
🍖 Среднее зелье: {user_data['inventory']['среднее зелье']} шт.
🍗 Большое зелье: {user_data['inventory']['большое зелье']} шт.

Выберите предмет для покупки:
    """
    
    bot.send_message(message.chat.id, shop_text, parse_mode='Markdown', reply_markup=markup)
@bot.message_handler(func=lambda message: message.text == '🎮 Сразиться с монстром')
def battle_monster(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)

    # ПРОВЕРКА ЗДОРОВЬЯ ДОЛЖНА БЫТЬ ЗДЕСЬ, ПОСЛЕ ПОЛУЧЕНИЯ ДАННЫХ
    if user_data['current_health'] <= 0:
        user_data['current_health'] = 1  # Минимальное здоровье
        update_user_data(user_id, user_data)

    if user_data['current_health'] < 10:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('🍖 Лечиться перед боем', callback_data='open_shop'))

        bot.send_message(
            message.chat.id,
            f"⚠️ *Внимание!* Ваше здоровье слишком низкое для боя.\n\n"
            f"❤️ Здоровье: {user_data['current_health']}/{user_data['max_health']}\n"
            f"Рекомендуется восстановить здоровье перед сражением.",
            parse_mode='Markdown',
            reply_markup=markup
        )
        return

    # Проверяем дневной лимит
    user_data = check_daily_limit(user_id, user_data)

    # Проверяем, остались ли попытки
    if user_data['battles_used'] >= user_data['daily_battles']:
        bot.send_message(
            message.chat.id, 
            f"❌ Вы исчерпали лимит сражений на сегодня!\n\n"
            f"Использовано: {user_data['battles_used']}/{user_data['daily_battles']}\n"
            f"Новые попытки появятся после 00:00 по времени сервера."
        )
        return

    # Увеличиваем счетчик использованных сражений
    user_data['battles_used'] += 1

    # Генерируем монстра в зависимости от уровня игрока
    monster_level = max(1, user_data['level'] - 1 + (user_data['level'] % 3))
    monster_health = 30 + monster_level * 10
    monster_attack = 5 + monster_level * 3
    monster_gold = 10 + monster_level * 5
    monster_exp = 5 + monster_level * 3

    # Расчет боя (упрощенный)
    player_damage = max(1, user_data['attack'] - (monster_attack // 3))
    turns_to_kill = monster_health // player_damage
    damage_taken = max(1, monster_attack - user_data['defense']) * turns_to_kill

    # Проверяем, выживет ли игрок
    if damage_taken >= user_data['current_health']:
        result = "❌ Вы проиграли монстру! Ваше здоровье слишком низкое."
        gold_gained = 0
        exp_gained = 0
        # Игрок теряет здоровье, но не умирает
        user_data['current_health'] = max(1, user_data['current_health'] - damage_taken // 2)
    else:
        # Игрок побеждает
        user_data['current_health'] -= damage_taken // 3  # Часть урона
        user_data['gold'] += monster_gold
        user_data['experience'] += monster_exp

        gold_gained = monster_gold
        exp_gained = monster_exp
        result = f"✅ Вы победили монстра уровня {monster_level}!"

        # Проверка на повышение уровня
        if user_data['experience'] >= user_data['exp_to_next_level']:
            user_data['level'] += 1
            user_data['points'] += 3  # Даем очки за уровень
            user_data['experience'] = 0
            user_data['exp_to_next_level'] = 50 * user_data['level']
            result += f"\n\n🎉 Поздравляем! Вы достигли {user_data['level']}-го уровня! +3 очка улучшения!"

    # Сохраняем обновленные данные
    update_user_data(user_id, user_data)

    battle_text = f"""
🎮 *Бой с монстром* (Попытка {user_data['battles_used']}/{user_data['daily_battles']})

*Ваш противник:*
• 🐉 Монстр уровня {monster_level}
• ❤️ Здоровье: {monster_health}
• ⚔️ Атака: {monster_attack}
• 💰 Награда: {monster_gold} золота
• 🎯 Опыт: {monster_exp}

*Итог боя:*
{result}

*Ваши потери/награды:*
• ❤️ Потеряно здоровья: {damage_taken // 3 if 'победили' in result else damage_taken // 2}
• 💰 Золота получено: {gold_gained}
• 🎯 Опыта получено: {exp_gained}

*Осталось сражений сегодня:* {user_data['daily_battles'] - user_data['battles_used']}
*Текущее здоровье:* {user_data['current_health']}/{user_data['max_health']}
*Текущее золото:* {user_data['gold']}
    """

    bot.send_message(message.chat.id, battle_text, parse_mode='Markdown')
# ================== ЗАПУСК БОТА ==================
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(
        message,
        "🤖 Я не понимаю эту команду. Используйте кнопки меню или /help для справки."
    )


if __name__ == '__main__':
    while True:
        try:
            print("🎮 Бот игры 'Прокачка Героя' запущен...")
            bot.infinity_polling()
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            print("🔄 Перезапуск через 10 секунд...")
            time.sleep(10)
