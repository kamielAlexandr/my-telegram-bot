import telebot
from telebot import types
import sqlite3
import os
import datetime
import logging
import sys
import random

# ================== НАСТРОЙКИ ==================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ================== БАЗА ДАННЫХ SQLite ==================
class Database:
    def __init__(self, db_name='game_bot.db'):
        self.db_name = db_name
        self.init_db()
    
    def get_connection(self):
        """Создаем соединение с базой данных"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Инициализация базы данных и создание таблиц"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    character_name TEXT,
                    race TEXT,
                    level INTEGER DEFAULT 1,
                    exp INTEGER DEFAULT 0,
                    coins INTEGER DEFAULT 100,
                    health INTEGER DEFAULT 100,
                    max_health INTEGER DEFAULT 100,
                    attack INTEGER DEFAULT 10,
                    defense INTEGER DEFAULT 5,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            print(f"✅ База данных инициализирована: {self.db_name}")
            
        except Exception as e:
            print(f"❌ Ошибка при инициализации БД: {e}")
        finally:
            if conn:
                conn.close()
    
    def get_user(self, user_id):
        """Получение данных пользователя"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            user = cursor.fetchone()
            
            if user:
                return dict(user)
            return None
            
        except Exception as e:
            print(f"❌ Ошибка при получении пользователя: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def create_user(self, user_id, username="", first_name="", last_name=""):
        """Создание нового пользователя с базовыми значениями"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO users 
                (user_id, username, first_name, last_name, level, exp, coins, health, max_health, attack, defense, last_active)
                VALUES (?, ?, ?, ?, 1, 0, 100, 100, 100, 10, 5, CURRENT_TIMESTAMP)
            ''', (user_id, username, first_name, last_name))
            
            conn.commit()
            print(f"👤 Создан новый пользователь: {user_id}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при создании пользователя: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def update_user(self, user_id, **kwargs):
        """Обновление данных пользователя"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if not kwargs:
                return False
            
            set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values())
            values.append(user_id)
            
            cursor.execute(f'''
                UPDATE users 
                SET {set_clause}, last_active = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', values)
            
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            print(f"❌ Ошибка при обновлении пользователя: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def complete_character_creation(self, user_id, character_name, race):
        """Завершение создания персонажа с именем и расой"""
        try:
            # Бонусы в зависимости от расы
            race_bonuses = {
                'human': {'attack': 2, 'defense': 2, 'health': 20},
                'elf': {'attack': 5, 'defense': 0, 'health': 10},
                'orc': {'attack': 8, 'defense': 3, 'health': 30},
                'dwarf': {'attack': 3, 'defense': 8, 'health': 25}
            }
            
            if race in race_bonuses:
                bonus = race_bonuses[race]
                return self.update_user(
                    user_id,
                    character_name=character_name,
                    race=race,
                    attack=10 + bonus['attack'],
                    defense=5 + bonus['defense'],
                    health=100 + bonus['health'],
                    max_health=100 + bonus['health']
                )
            else:
                return self.update_user(
                    user_id,
                    character_name=character_name,
                    race=race
                )
                
        except Exception as e:
            print(f"❌ Ошибка при завершении создания персонажа: {e}")
            return False
    
    def add_exp(self, user_id, exp_amount):
        """Добавление опыта пользователю с проверкой уровня"""
        try:
            user = self.get_user(user_id)
            if not user:
                return False
            
            new_exp = user['exp'] + exp_amount
            new_level = user['level']
            
            exp_needed = new_level * 100
            
            while new_exp >= exp_needed:
                new_exp -= exp_needed
                new_level += 1
                exp_needed = new_level * 100
            
            return self.update_user(user_id, exp=new_exp, level=new_level)
            
        except Exception as e:
            print(f"❌ Ошибка при добавлении опыта: {e}")
            return False
    
    def add_coins(self, user_id, coins_amount):
        """Добавление монет пользователю"""
        try:
            user = self.get_user(user_id)
            if not user:
                return False
            
            new_coins = user['coins'] + coins_amount
            return self.update_user(user_id, coins=new_coins)
            
        except Exception as e:
            print(f"❌ Ошибка при добавлении монет: {e}")
            return False
    
    def get_race_description(race):
    """Получить описание расы"""
    descriptions = {
        'human': "👨 *Человек* - ⚖️ Сбалансированная раса\n+2 к атаке, +2 к защите, +20 к здоровью",
        'elf': "🧝 *Эльф* - 🏹 Мастера стрельбы\n+5 к атаке, +10 к здоровью",
        'orc': "👹 *Орк* - ⚔️ Сильные воины\n+8 к атаке, +3 к защите, +30 к здоровью",
        'dwarf': "🧙 *Гном* - 🛡️ Непробиваемые защитники\n+3 к атаке, +8 к защите, +25 к здоровью"
    }
    return descriptions.get(race, "Неизвестная раса")

# Создаем экземпляр базы данных
db = Database()

# ================== НАСТРОЙКИ БОТА ==================
print("=== Railway Environment Debug ===")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

BOT_TOKEN = os.environ.get('BOT_TOKEN')

if not BOT_TOKEN:
    print("❌ КРИТИЧЕСКАЯ ОШИБКА: Переменная окружения 'BOT_TOKEN' не найдена.")
    exit(1)

print(f"✅ Токен бота успешно загружен. Длина: {len(BOT_TOKEN)} символов")
bot = telebot.TeleBot(BOT_TOKEN)

# Хранилище временных данных для создания персонажа
temp_user_data = {}

# ================== КЛАВИАТУРЫ ==================
def get_main_menu():
    """Клавиатура главного меню"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton('🎮 Профиль')
    btn2 = types.KeyboardButton('⚔️ Охота')
    btn3 = types.KeyboardButton('🏋️ Тренировка')
    btn4 = types.KeyboardButton('🛒 Магазин')
    btn5 = types.KeyboardButton('📊 Статистика')
    btn6 = types.KeyboardButton('ℹ️ Помощь')
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    return markup

def get_race_keyboard():
    """Клавиатура выбора расы"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton('👨 Человек', callback_data='race_human')
    btn2 = types.InlineKeyboardButton('🧝 Эльф', callback_data='race_elf')
    btn3 = types.InlineKeyboardButton('👹 Орк', callback_data='race_orc')
    btn4 = types.InlineKeyboardButton('🧙 Гном', callback_data='race_dwarf')
    markup.add(btn1, btn2, btn3, btn4)  # <-- ДОБАВЬТЕ ЭТУ СТРОКУ
    return markup

def get_hunt_keyboard():
    """Клавиатура охоты"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton('🐺 Легкая охота', callback_data='hunt_easy')
    btn2 = types.InlineKeyboardButton('🐗 Средняя охота', callback_data='hunt_medium')
    btn3 = types.InlineKeyboardButton('🐉 Сложная охота', callback_data='hunt_hard')
    btn4 = types.InlineKeyboardButton('🏆 Босс', callback_data='hunt_boss')
    btn5 = types.InlineKeyboardButton('⬅️ Назад', callback_data='back_to_main')
    markup.add(btn1, btn2, btn3, btn4)
    markup.add(btn5)  # Отдельный ряд для кнопки "Назад"
    return markup

def get_training_keyboard():
    """Клавиатура тренировки"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton('💪 Сила (+Атака)', callback_data='train_attack')
    btn2 = types.InlineKeyboardButton('🛡️ Защита', callback_data='train_defense')
    btn3 = types.InlineKeyboardButton('❤️ Выносливость', callback_data='train_health')
    btn4 = types.InlineKeyboardButton('⬅️ Назад', callback_data='back_to_main')
    markup.add(btn1, btn2, btn3)
    markup.add(btn4)  # Отдельный ряд для кнопки "Назад"
    return markup


def get_shop_keyboard():
    """Клавиатура магазина"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton('⚔️ Меч (+5 атаки)', callback_data='buy_sword')
    btn2 = types.InlineKeyboardButton('🛡️ Щит (+5 защиты)', callback_data='buy_shield')
    btn3 = types.InlineKeyboardButton('❤️ Зелье здоровья', callback_data='buy_potion')
    btn4 = types.InlineKeyboardButton('⬅️ Назад', callback_data='back_to_main')
    markup.add(btn1, btn2, btn3)
    markup.add(btn4)  # Отдельный ряд для кнопки "Назад"
    return markup

# ================== ОБРАБОТЧИКИ КОМАНД ==================
@bot.message_handler(commands=['start'])
def start_command(message):
    """Обработчик команды /start"""
    user = message.from_user
    user_id = user.id
    
    user_data = db.get_user(user_id)
    
    if user_data:
        if user_data.get('character_name') and user_data.get('race'):
            # Персонаж уже создан
            welcome_text = f"""
🎮 Добро пожаловать обратно, {user_data['character_name']}!

Вы - {user_data['race'].capitalize()} {user_data['level']} уровня.
Используйте меню ниже для управления персонажем!
            """
            bot.send_message(
                message.chat.id, 
                welcome_text, 
                reply_markup=get_main_menu()
            )
        else:
            # Персонаж не до конца создан
            bot.send_message(
                message.chat.id,
                "Давайте завершим создание вашего персонажа! Как его зовут?",
                reply_markup=types.ReplyKeyboardRemove()
            )
            temp_user_data[user_id] = {'step': 'waiting_name'}
    else:
        # Новый пользователь
        db.create_user(
            user_id=user_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        welcome_text = """
🎮 Добро пожаловать в игру "Прокачка Героя"!

Для начала нужно создать персонажа.
Как будут звать вашего героя?
(Введите имя персонажа)
        """
        
        bot.send_message(
            message.chat.id, 
            welcome_text,
            reply_markup=types.ReplyKeyboardRemove()
        )
        temp_user_data[user_id] = {'step': 'waiting_name'}

@bot.message_handler(commands=['help'])
def help_command(message):
    """Обработчик команды /help"""
    help_text = """
🎮 *Прокачка Героя* - RPG игра в Telegram!

*Основные возможности:*
⚔️ *Охота* - сражайтесь с монстрами, получайте опыт и золото
🏋️ *Тренировка* - улучшайте характеристики персонажа
🛒 *Магазин* - покупайте снаряжение и зелья
📊 *Профиль* - просматривайте статистику персонажа

*Расы персонажа:*
👨 *Человек* - сбалансированная раса
🧝 *Эльф* - высокая атака, низкая защита
👹 *Орк* - очень высокая атака и здоровье
🧙 *Гном* - высокая защита

Используйте кнопки меню для игры!
    """
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

# ================== ОБРАБОТЧИКИ ТЕКСТОВЫХ СООБЩЕНИЙ ==================
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    """Обработка текстовых сообщений"""
    user_id = message.from_user.id
    
    if user_id in temp_user_data:
        step = temp_user_data[user_id]['step']
        
        if step == 'waiting_name':
            # Получаем имя персонажа
            character_name = message.text.strip()
            
            if len(character_name) < 2:
                bot.send_message(message.chat.id, "Имя должно быть не короче 2 символов. Попробуйте еще раз:")
                return
            
            if len(character_name) > 20:
                bot.send_message(message.chat.id, "Имя должно быть не длиннее 20 символов. Попробуйте еще раз:")
                return
            
            # Сохраняем имя
            temp_user_data[user_id]['character_name'] = character_name
            temp_user_data[user_id]['step'] = 'waiting_race'
            
            # Предлагаем выбрать расу
            race_text = f"""
Отлично, {character_name}! Теперь выберите расу:

{db.get_race_description('human')}
{db.get_race_description('elf')}
{db.get_race_description('orc')}
{db.get_race_description('dwarf')}

Выберите расу с помощью кнопок ниже:
            """
            
            bot.send_message(
                message.chat.id,
                race_text,
                reply_markup=get_race_keyboard()
            )
            return
    
    # Если сообщение не связано с созданием персонажа
    text = message.text
    
    if text == '🎮 Профиль':
        show_profile(message)
    elif text == '⚔️ Охота':
        show_hunt_menu(message)
    elif text == '🏋️ Тренировка':
        show_training_menu(message)
    elif text == '🛒 Магазин':
        show_shop_menu(message)
    elif text == '📊 Статистика':
        show_stats(message)
    elif text == 'ℹ️ Помощь':
        help_command(message)
    else:
        bot.send_message(
            message.chat.id,
            "Используйте кнопки меню для навигации!",
            reply_markup=get_main_menu()
        )

# ================== ОБРАБОТЧИКИ CALLBACK ==================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    """Обработчик нажатий на inline-кнопки"""
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    try:
        if call.data.startswith('race_'):
            # Выбор расы
            race = call.data.replace('race_', '')
            
            # Проверяем, есть ли данные пользователя
            if user_id not in temp_user_data:
                bot.answer_callback_query(call.id, "❌ Ошибка: данные сессии потеряны. Начните с /start")
                return
                
            character_name = temp_user_data[user_id].get('character_name', 'Герой')
            
            # Завершаем создание персонажа
            if db.complete_character_creation(user_id, character_name, race):
                # Удаляем временные данные
                if user_id in temp_user_data:
                    del temp_user_data[user_id]
                
                # Показываем приветствие
                race_names = {
                    'human': '👨 Человек',
                    'elf': '🧝 Эльф',
                    'orc': '👹 Орк',
                    'dwarf': '🧙 Гном'
                }
                
                race_name_display = race_names.get(race, race.capitalize())
                
                welcome_text = f"""
🎉 Персонаж создан!

👤 Имя: {character_name}
🏹 Раса: {race_name_display}

{db.get_race_description(race)}

Ваше путешествие начинается!
Используйте меню ниже для управления персонажем.
                """
                
                # Удаляем старое сообщение с кнопками
                try:
                    bot.delete_message(chat_id, message_id)
                except:
                    pass
                
                # Отправляем новое сообщение
                bot.send_message(
                    chat_id,
                    welcome_text,
                    reply_markup=get_main_menu()
                )
                
                # Отправляем подсказку
                time.sleep(1)
                bot.send_message(
                    chat_id,
                    "🎮 *Используйте кнопки меню для игры!*\n\n"
                    "⚔️ *Охота* - сражайтесь с монстрами\n"
                    "🏋️ *Тренировка* - улучшайте характеристики\n"
                    "🛒 *Магазин* - покупайте снаряжение\n"
                    "📊 *Профиль* - просматривайте статистику",
                    parse_mode='Markdown'
                )
            else:
                bot.answer_callback_query(call.id, "❌ Ошибка при создании персонажа!")
        elif call.data.startswith('hunt_'):
            # Охота
            difficulty = call.data.replace('hunt_', '')
            hunt_monster(call, difficulty)
        
        elif call.data.startswith('train_'):
            # Тренировка
            stat = call.data.replace('train_', '')
            train_skill(call, stat)
        
        elif call.data.startswith('buy_'):
            # Покупка в магазине
            item = call.data.replace('buy_', '')
            buy_item(call, item)
        
        elif call.data == 'back_to_main':
            # Возврат в главное меню
            bot.edit_message_text(
                "Главное меню",
                chat_id,
                message_id
            )
            bot.send_message(
                chat_id,
                "Выберите действие:",
                reply_markup=get_main_menu()
            )
    
    except Exception as e:
        print(f"❌ Ошибка в callback_handler: {e}")
        bot.answer_callback_query(call.id, "❌ Произошла ошибка!")

# ================== ФУНКЦИИ МЕНЮ ==================
def show_profile(message):
    """Показать профиль игрока"""
    user_id = message.from_user.id
    user_data = db.get_user(user_id)
    
    if not user_data or not user_data.get('character_name'):
        bot.send_message(
            message.chat.id,
            "Сначала создайте персонажа командой /start",
            reply_markup=get_main_menu()
        )
        return
    
    # Расчет процента здоровья
    health_percent = (user_data['health'] / user_data['max_health']) * 100
    health_bar = "❤️" * int(health_percent / 20) + "♡" * (5 - int(health_percent / 20))
    
    profile_text = f"""
📊 *ПРОФИЛЬ ПЕРСОНАЖА*

👤 *{user_data['character_name']}*
🏹 *Раса:* {user_data['race'].capitalize() if user_data['race'] else 'Не выбрана'}

{health_bar} {user_data['health']}/{user_data['max_health']}

⚔️ *Характеристики:*
📊 Уровень: {user_data['level']}
⭐ Опыт: {user_data['exp']}/{user_data['level'] * 100}
💰 Золото: {user_data['coins']}
🗡️ Атака: {user_data['attack']}
🛡️ Защита: {user_data['defense']}

📅 Зарегистрирован: {user_data['created_at'][:10]}
    """
    
    bot.send_message(
        message.chat.id,
        profile_text,
        parse_mode='Markdown',
        reply_markup=get_main_menu()
    )

def show_hunt_menu(message):
    """Показать меню охоты"""
    hunt_text = """
⚔️ *Меню охоты*

Выберите сложность охоты:

🐺 *Легкая* - слабые монстры, маленькая награда
🐗 *Средняя* - обычные монстры, средняя награда
🐉 *Сложная* - сильные монстры, большая награда
🏆 *Босс* - очень сложно, но награда огромная!

Рискните своей удачей!
    """
    
    bot.send_message(
        message.chat.id,
        hunt_text,
        parse_mode='Markdown',
        reply_markup=get_hunt_keyboard()
    )

def show_training_menu(message):
    """Показать меню тренировки"""
    user_data = db.get_user(message.from_user.id)
    
    if not user_data:
        return
    
    train_text = f"""
🏋️ *Меню тренировки*

Улучшайте характеристики персонажа:

💪 *Сила* (+1 к атаке) - 20💰
🛡️ *Защита* (+1 к защите) - 20💰
❤️ *Выносливость* (+10 к макс. здоровью) - 30💰

Ваши текущие характеристики:
🗡️ Атака: {user_data['attack']}
🛡️ Защита: {user_data['defense']}
❤️ Макс. здоровье: {user_data['max_health']}
💰 Ваши монеты: {user_data['coins']}
    """
    
    bot.send_message(
        message.chat.id,
        train_text,
        parse_mode='Markdown',
        reply_markup=get_training_keyboard()
    )

def show_shop_menu(message):
    """Показать меню магазина"""
    user_data = db.get_user(message.from_user.id)
    
    if not user_data:
        return
    
    shop_text = f"""
🛒 *Магазин снаряжения*

Здесь можно купить полезные предметы:

⚔️ *Меч* (+5 к атаке) - 150💰
🛡️ *Щит* (+5 к защите) - 150💰
❤️ *Зелье здоровья* (восстанавливает 50 HP) - 50💰

💰 Ваши монеты: {user_data['coins']}
    """
    
    bot.send_message(
        message.chat.id,
        shop_text,
        parse_mode='Markdown',
        reply_markup=get_shop_keyboard()
    )

# ================== ИГРОВЫЕ ФУНКЦИИ ==================
def hunt_monster(call, difficulty):
    """Охота на монстра"""
    user_id = call.from_user.id
    user_data = db.get_user(user_id)
    
    if not user_data:
        bot.answer_callback_query(call.id, "❌ Персонаж не найден!")
        return
    
    # Настройки сложности
    difficulty_settings = {
        'easy': {'name': '🐺 Легкая', 'exp': 10, 'coins': 5, 'health': 20, 'damage': 5},
        'medium': {'name': '🐗 Средняя', 'exp': 25, 'coins': 15, 'health': 50, 'damage': 15},
        'hard': {'name': '🐉 Сложная', 'exp': 50, 'coins': 30, 'health': 100, 'damage': 25},
        'boss': {'name': '🏆 Босс', 'exp': 100, 'coins': 60, 'health': 200, 'damage': 40}
    }
    
    settings = difficulty_settings.get(difficulty, difficulty_settings['easy'])
    
    # Симуляция боя
    player_damage = user_data['attack'] + random.randint(1, 10)
    monster_damage = max(1, settings['damage'] - (user_data['defense'] // 3))
    
    # Шанс победы зависит от сложности
    win_chance = {
        'easy': 0.9,
        'medium': 0.7,
        'hard': 0.5,
        'boss': 0.3
    }.get(difficulty, 0.5)
    
    if random.random() < win_chance:
        # Победа
        db.add_exp(user_id, settings['exp'])
        db.add_coins(user_id, settings['coins'])
        
        result_text = f"""
🎉 *ПОБЕДА!*

Вы победили {settings['name']} монстра!

🏆 *Награды:*
⭐ Опыт: +{settings['exp']}
💰 Золото: +{settings['coins']}

⚔️ Нанесенный урон: {player_damage}
        """
    else:
        # Поражение
        health_lost = min(monster_damage, user_data['health'] - 1)
        new_health = user_data['health'] - health_lost
        
        db.update_user(user_id, health=new_health)
        
        result_text = f"""
💀 *ПОРАЖЕНИЕ!*

{settings['name']} монстр оказался сильнее!

💔 Потеряно здоровья: {health_lost}
❤️ Осталось здоровья: {new_health}

💸 Вы потеряли 10💰
        """
        
        # Штраф за поражение
        if user_data['coins'] >= 10:
            db.add_coins(user_id, -10)
    
    bot.edit_message_text(
        result_text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode='Markdown'
    )

def train_skill(call, stat):
    """Тренировка навыка"""
    user_id = call.from_user.id
    user_data = db.get_user(user_id)
    
    if not user_data:
        bot.answer_callback_query(call.id, "❌ Персонаж не найден!")
        return
    
    # Стоимость тренировки
    costs = {
        'attack': 20,
        'defense': 20,
        'health': 30
    }
    
    cost = costs.get(stat, 20)
    
    if user_data['coins'] < cost:
        bot.answer_callback_query(call.id, f"❌ Недостаточно монет! Нужно {cost}💰")
        return
    
    # Улучшение характеристики
    improvements = {
        'attack': {'attack': user_data['attack'] + 1},
        'defense': {'defense': user_data['defense'] + 1},
        'health': {'max_health': user_data['max_health'] + 10, 'health': min(user_data['health'] + 10, user_data['max_health'] + 10)}
    }
    
    improvement = improvements.get(stat, {})
    
    if improvement:
        # Списываем монеты
        new_coins = user_data['coins'] - cost
        improvement['coins'] = new_coins
        
        # Применяем улучшение
        if db.update_user(user_id, **improvement):
            stat_names = {
                'attack': '🗡️ Атаку',
                'defense': '🛡️ Защиту',
                'health': '❤️ Максимальное здоровье'
            }
            
            result_text = f"""
🏋️ *ТРЕНИРОВКА ЗАВЕРШЕНА!*

Вы улучшили {stat_names[stat]}!

💸 Стоимость: {cost}💰
💰 Осталось монет: {new_coins}

Продолжайте тренировки!
            """
            
            bot.edit_message_text(
                result_text,
                call.message.chat.id,
                call.message.message_id,
                parse_mode='Markdown'
            )
        else:
            bot.answer_callback_query(call.id, "❌ Ошибка при тренировке!")
    else:
        bot.answer_callback_query(call.id, "❌ Неизвестный навык!")

def buy_item(call, item):
    """Покупка предмета в магазине"""
    user_id = call.from_user.id
    user_data = db.get_user(user_id)
    
    if not user_data:
        bot.answer_callback_query(call.id, "❌ Персонаж не найден!")
        return
    
    # Стоимость предметов
    items = {
        'sword': {'name': '⚔️ Меч', 'cost': 150, 'bonus': {'attack': 5}},
        'shield': {'name': '🛡️ Щит', 'cost': 150, 'bonus': {'defense': 5}},
        'potion': {'name': '❤️ Зелье здоровья', 'cost': 50, 'bonus': {'health': min(user_data['health'] + 50, user_data['max_health'])}}
    }
    
    item_data = items.get(item)
    
    if not item_data:
        bot.answer_callback_query(call.id, "❌ Предмет не найден!")
        return
    
    if user_data['coins'] < item_data['cost']:
        bot.answer_callback_query(call.id, f"❌ Недостаточно монет! Нужно {item_data['cost']}💰")
        return
    
    # Покупка
    new_coins = user_data['coins'] - item_data['cost']
    item_data['bonus']['coins'] = new_coins
    
    if db.update_user(user_id, **item_data['bonus']):
        result_text = f"""
🛒 *ПОКУПКА УСПЕШНА!*

Вы купили {item_data['name']}!

💸 Стоимость: {item_data['cost']}💰
💰 Осталось монет: {new_coins}

Предмет добавлен в инвентарь!
        """
        
        bot.edit_message_text(
            result_text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode='Markdown'
        )
    else:
        bot.answer_callback_query(call.id, "❌ Ошибка при покупке!")

def show_stats(message):
    """Показать статистику сервера"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as total_users FROM users')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(coins) as total_coins FROM users')
        total_coins = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT MAX(level) as max_level FROM users')
        max_level = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT race, COUNT(*) as count FROM users WHERE race IS NOT NULL GROUP BY race')
        races = cursor.fetchall()
        
        race_stats = ""
        for race in races:
            race_name = {
                'human': '👨 Люди',
                'elf': '🧝 Эльфы',
                'orc': '👹 Орки',
                'dwarf': '🧙 Гномы'
            }.get(race['race'], race['race'])
            race_stats += f"{race_name}: {race['count']}\n"
        
        stats_text = f"""
📊 *СТАТИСТИКА СЕРВЕРА*

👥 Всего игроков: {total_users}
💰 Всего золота в игре: {total_coins}
🏆 Максимальный уровень: {max_level}

*Распределение рас:*
{race_stats}

🎮 Бот работает стабильно!
        """
        
        bot.send_message(
            message.chat.id,
            stats_text,
            parse_mode='Markdown',
            reply_markup=get_main_menu()
        )
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка в show_stats: {e}")
        bot.send_message(
            message.chat.id,
            "❌ Ошибка при получении статистики",
            reply_markup=get_main_menu()
        )

# ================== ЗАПУСК БОТА ==================
def main():
    print("=" * 50)
    print("🎮 БОТ 'ПРОКАЧКА ГЕРОЯ' ЗАПУЩЕН")
    print(f"🤖 Используется SQLite база данных")
    print("=" * 50)
    
    try:
        bot_info = bot.get_me()
        print(f"🤖 Бот: @{bot_info.username} (ID: {bot_info.id})")
        print(f"📝 Имя бота: {bot_info.first_name}")
        
        print("🔄 Бот запускает polling...")
        bot.infinity_polling()
        
    except Exception as e:
        print(f"❌ Критическая ошибка при запуске бота: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()
