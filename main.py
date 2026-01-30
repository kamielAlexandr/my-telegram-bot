import telebot
from telebot import types
import sqlite3
import os
import datetime
import logging
import sys

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
        conn.row_factory = sqlite3.Row  # Чтобы получать результаты как словари
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
                    level INTEGER DEFAULT 1,
                    exp INTEGER DEFAULT 0,
                    coins INTEGER DEFAULT 100,
                    health INTEGER DEFAULT 100,
                    attack INTEGER DEFAULT 10,
                    defense INTEGER DEFAULT 5,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица инвентаря (если понадобится)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    item_name TEXT,
                    item_type TEXT,
                    quantity INTEGER DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
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
                # Преобразуем Row в словарь
                return dict(user)
            
            # Если пользователя нет, создаем нового
            return None
            
        except Exception as e:
            print(f"❌ Ошибка при получении пользователя: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def create_user(self, user_id, username="", first_name="", last_name=""):
        """Создание нового пользователя"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO users 
                (user_id, username, first_name, last_name, level, exp, coins, health, attack, defense, last_active)
                VALUES (?, ?, ?, ?, 1, 0, 100, 100, 10, 5, CURRENT_TIMESTAMP)
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
            
            # Динамически формируем запрос UPDATE
            set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values())
            values.append(user_id)  # Для условия WHERE
            
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
    
    def add_exp(self, user_id, exp_amount):
        """Добавление опыта пользователю с проверкой уровня"""
        try:
            user = self.get_user(user_id)
            if not user:
                return False
            
            new_exp = user['exp'] + exp_amount
            new_level = user['level']
            
            # Проверяем, нужно ли повысить уровень
            exp_needed = new_level * 100  # Простая формула: для каждого уровня нужно 100 опыта
            
            while new_exp >= exp_needed:
                new_exp -= exp_needed
                new_level += 1
                exp_needed = new_level * 100
            
            # Обновляем данные
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

# Создаем экземпляр базы данных
db = Database()

# ================== НАСТРОЙКИ БОТА ==================
print("=== Railway Environment Debug ===")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

BOT_TOKEN = os.environ.get('BOT_TOKEN')

# КРИТИЧЕСКИ ВАЖНО: если токена нет, бот должен остановиться с понятной ошибкой
if not BOT_TOKEN:
    print("❌ КРИТИЧЕСКАЯ ОШИБКА: Переменная окружения 'BOT_TOKEN' не найдена.")
    print("Проверьте настройки в Railway:")
    print("1. Откройте вкладку Variables")
    print("2. Убедитесь, что есть переменная BOT_TOKEN")
    print("3. Перезапустите deployment")
    exit(1)

# Если мы здесь, токен есть
print(f"✅ Токен бота успешно загружен. Длина: {len(BOT_TOKEN)} символов")
bot = telebot.TeleBot(BOT_TOKEN)

# ================== КОМАНДЫ БОТА ==================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    try:
        user = message.from_user
        user_id = user.id
        
        print(f"🎮 Команда /start от пользователя {user_id}")
        
        # Проверяем, есть ли пользователь в базе
        user_data = db.get_user(user_id)
        
        if not user_data:
            # Создаем нового пользователя
            db.create_user(
                user_id=user_id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            user_data = db.get_user(user_id)
        
        # Формируем приветственное сообщение
        welcome_text = f"""
🎮 Добро пожаловать в игру "Прокачка Героя"!

👤 Привет, {user.first_name}!

Ваши характеристики:
📊 Уровень: {user_data['level']}
⭐ Опыт: {user_data['exp']}/{user_data['level'] * 100}
💰 Монеты: {user_data['coins']}

Характеристики героя:
❤️ Здоровье: {user_data['health']}
⚔️ Атака: {user_data['attack']}
🛡️ Защита: {user_data['defense']}

Доступные команды:
/start - Начать игру
/profile - Профиль
/hunt - Охота за монстрами
/shop - Магазин
/train - Тренировка
/stats - Статистика
        """
        
        bot.reply_to(message, welcome_text)
        
    except Exception as e:
        print(f"❌ Ошибка в send_welcome: {e}")
        import traceback
        traceback.print_exc()
        bot.reply_to(message, "⚠️ Произошла ошибка. Попробуйте снова.")

@bot.message_handler(commands=['profile'])
def show_profile(message):
    try:
        user_id = message.from_user.id
        user_data = db.get_user(user_id)
        
        if not user_data:
            bot.reply_to(message, "❌ Вы не зарегистрированы. Напишите /start")
            return
        
        # Форматируем дату
        last_active = datetime.datetime.strptime(user_data['last_active'], '%Y-%m-%d %H:%M:%S')
        created_at = datetime.datetime.strptime(user_data['created_at'], '%Y-%m-%d %H:%M:%S')
        
        profile_text = f"""
📊 ПРОФИЛЬ ИГРОКА

👤 Имя: {user_data['first_name'] or 'Не указано'}
📛 Username: @{user_data['username'] or 'нет'}

🎮 Игровая статистика:
📊 Уровень: {user_data['level']}
⭐ Опыт: {user_data['exp']}/{user_data['level'] * 100}
💰 Монеты: {user_data['coins']}

⚔️ Характеристики героя:
❤️ Здоровье: {user_data['health']}
⚔️ Атака: {user_data['attack']}
🛡️ Защита: {user_data['defense']}

📅 Дата регистрации: {created_at.strftime('%d.%m.%Y')}
🕐 Последняя активность: {last_active.strftime('%d.%m.%Y %H:%M')}
        """
        
        bot.reply_to(message, profile_text)
        
    except Exception as e:
        print(f"❌ Ошибка в show_profile: {e}")
        bot.reply_to(message, "⚠️ Произошла ошибка.")

@bot.message_handler(commands=['hunt'])
def hunt_monster(message):
    try:
        user_id = message.from_user.id
        user_data = db.get_user(user_id)
        
        if not user_data:
            bot.reply_to(message, "❌ Вы не зарегистрированы. Напишите /start")
            return
        
        import random
        
        # Генерируем случайного монстра
        monsters = [
            {"name": "Гоблин", "exp": 10, "coins": 5, "health": 30},
            {"name": "Орк", "exp": 20, "coins": 10, "health": 50},
            {"name": "Тролль", "exp": 30, "coins": 15, "health": 80},
            {"name": "Дракон", "exp": 50, "coins": 25, "health": 120},
            {"name": "Слайм", "exp": 5, "coins": 2, "health": 15}
        ]
        
        monster = random.choice(monsters)
        
        # Симуляция битвы
        player_damage = user_data['attack'] + random.randint(1, 10)
        monster_damage = random.randint(5, 15) - user_data['defense'] // 2
        monster_damage = max(1, monster_damage)  # Минимальный урон 1
        
        # Проверяем победу
        if player_damage >= monster['health']:
            # Игрок победил
            exp_gained = monster['exp']
            coins_gained = monster['coins']
            
            # Добавляем награды
            db.add_exp(user_id, exp_gained)
            db.add_coins(user_id, coins_gained)
            
            result_text = f"""
🎯 ОХОТА УСПЕШНА!

Вы встретили: {monster['name']}
⚔️ Ваш урон: {player_damage}
❤️ Здоровье монстра: {monster['health']}

🏆 ПОБЕДА!
⭐ Получено опыта: {exp_gained}
💰 Получено монет: {coins_gained}

Продолжайте в том же духе!
            """
        else:
            # Игрок проиграл
            health_lost = min(monster_damage, user_data['health'] - 1)  # Оставляем хотя бы 1 HP
            new_health = user_data['health'] - health_lost
            
            db.update_user(user_id, health=new_health)
            
            result_text = f"""
💀 ОХОТА ПРОВАЛЕНА!

Вы встретили: {monster['name']}
⚔️ Ваш урон: {player_damage}
❤️ Здоровье монстра: {monster['health']}

☠️ ПОРАЖЕНИЕ!
💔 Потеряно здоровья: {health_lost}
❤️ Ваше здоровье теперь: {new_health}

Отдохните и попробуйте снова!
            """
        
        bot.reply_to(message, result_text)
        
    except Exception as e:
        print(f"❌ Ошибка в hunt_monster: {e}")
        bot.reply_to(message, "⚠️ Произошла ошибка во время охоты.")

@bot.message_handler(commands=['train'])
def train_skills(message):
    try:
        user_id = message.from_user.id
        user_data = db.get_user(user_id)
        
        if not user_data:
            bot.reply_to(message, "❌ Вы не зарегистрированы. Напишите /start")
            return
        
        import random
        
        # Стоимость тренировки
        train_cost = 10
        
        if user_data['coins'] < train_cost:
            bot.reply_to(message, f"❌ Недостаточно монет для тренировки! Нужно {train_cost}💰")
            return
        
        # Случайное улучшение характеристики
        stat_to_improve = random.choice(['attack', 'defense', 'health'])
        improvement = random.randint(1, 3)
        
        # Вычитаем стоимость
        new_coins = user_data['coins'] - train_cost
        
        # Улучшаем характеристику
        new_value = user_data[stat_to_improve] + improvement
        
        # Обновляем данные
        update_data = {
            'coins': new_coins,
            stat_to_improve: new_value
        }
        
        db.update_user(user_id, **update_data)
        
        # Тексты характеристик
        stat_names = {
            'attack': '⚔️ Атаку',
            'defense': '🛡️ Защиту',
            'health': '❤️ Здоровье'
        }
        
        result_text = f"""
🏋️ ТРЕНИРОВКА ЗАВЕРШЕНА!

💸 Стоимость: {train_cost}💰
📈 Улучшена {stat_names[stat_to_improve]}
✨ +{improvement} к {stat_names[stat_to_improve].lower()}

💰 Осталось монет: {new_coins}
{stat_names[stat_to_improve].split()[1]}: {new_value}

Продолжайте тренировки!
        """
        
        bot.reply_to(message, result_text)
        
    except Exception as e:
        print(f"❌ Ошибка в train_skills: {e}")
        bot.reply_to(message, "⚠️ Произошла ошибка во время тренировки.")

@bot.message_handler(commands=['stats'])
def show_stats(message):
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Получаем общую статистику
        cursor.execute('SELECT COUNT(*) as total_users FROM users')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(coins) as total_coins FROM users')
        total_coins = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT SUM(level) as total_levels FROM users')
        total_levels = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT MAX(level) as max_level FROM users')
        max_level = cursor.fetchone()[0] or 0
        
        stats_text = f"""
📊 СТАТИСТИКА СЕРВЕРА

👥 Всего игроков: {total_users}
💰 Всего монет в игре: {total_coins}
📈 Суммарный уровень: {total_levels}
🏆 Максимальный уровень: {max_level}

🎮 Бот работает стабильно!
        """
        
        bot.reply_to(message, stats_text)
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка в show_stats: {e}")
        bot.reply_to(message, "⚠️ Произошла ошибка при получении статистики.")

# ================== ЗАПУСК БОТА ==================
def main():
    print("=" * 50)
    print("🎮 БОТ 'ПРОКАЧКА ГЕРОЯ' ЗАПУЩЕН")
    print(f"🤖 Используется SQLite база данных")
    print("=" * 50)
    
    try:
        # Проверяем работоспособность бота
        bot_info = bot.get_me()
        print(f"🤖 Бот: @{bot_info.username} (ID: {bot_info.id})")
        print(f"📝 Имя бота: {bot_info.first_name}")
        
        # Запускаем бота
        print("🔄 Бот запускает polling...")
        bot.infinity_polling()
        
    except Exception as e:
        print(f"❌ Критическая ошибка при запуске бота: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()
