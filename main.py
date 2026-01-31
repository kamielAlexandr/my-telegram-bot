# bot.py
import telebot
from telebot import types
import os
import sqlite3
import datetime
import random
import time
import requests
import logging
from database import Database

try:
    from config import BOT_TOKEN, DB_PATH
except ImportError:
    # Если config.py не существует, используем значения по умолчанию
    BOT_TOKEN = os.environ.get('BOT_TOKEN')
    DB_PATH = 'game_bot.db'
# ================== ИЗОБРАЖЕНИЯ ==================
# Ссылки на изображения (можно заменить на свои)

# Изображения рас
# Изображения рас (используем российские хостинги)
RACE_IMAGES = {
    'human': 'https://i126.fastpic.org/thumb/2026/0130/2c/_d2515d33e45fa7ffb5246cacabdaba2c.jpeg',  # Воин-человек
    'elf': 'https://i126.fastpic.org/thumb/2026/0130/81/_d3d94be5aa45b9239aeb5adc41443081.jpeg',    # Эльф-лучник
    'orc': 'https://i126.fastpic.org/thumb/2026/0130/20/_b8c1f666bd21bb415e8fb35145eb3e20.jpeg',    # Орк-берсерк
    'dwarf': 'https://i126.fastpic.org/thumb/2026/0130/5b/_c188fac4eb6d205bd9fc0486c9b9355b.jpeg'   # Гном-воин
}

# Изображения монстров (русские хостинги)
MONSTER_IMAGES = {
    'rat': 'https://storage.yandexcloud.net/game-bot-images/monsters/rat.png',    # Крыса
    'wolf': 'https://storage.yandexcloud.net/game-bot-images/monsters/wolf.png',   # Волк
    'boar': 'https://sun9-55.userapi.com/impg/boar_image_hash/photo.jpg',   # Кабан
    'bear': 'https://avatars.mds.yandex.net/get-images-cbir/789012/bear_image/orig',   # Медведь
    'dragon': 'https://storage.yandexcloud.net/game-bot-images/monsters/dragon.png'  # Дракон
}

# Изображения результатов боя
BATTLE_IMAGES = {
    'victory': 'https://sun9-29.userapi.com/impg/victory_image/photo.jpg?size=800x600',  # Победа
    'defeat': 'https://sun9-12.userapi.com/impg/defeat_image/photo.jpg?size=800x600',   # Поражение
    'level_up': 'https://avatars.mds.yandex.net/get-images-cbir/level_up_image/orig'  # Повышение уровня
}

# Изображения для меню
MENU_IMAGES = {
    'main': 'https://storage.yandexcloud.net/game-bot-images/menu/main.jpg',      # Главное меню
    'profile': 'https://sun9-47.userapi.com/impg/profile_image/photo.jpg',   # Профиль
    'shop': 'https://avatars.mds.yandex.net/get-images-cbir/shop_image/orig',      # Магазин
    'inventory': 'https://storage.yandexcloud.net/game-bot-images/menu/inventory.png', # Инвентарь
    'training': 'https://sun9-33.userapi.com/impg/training_image/photo.jpg',  # Тренировка
    'rest': 'https://avatars.mds.yandex.net/get-images-cbir/rest_image/orig'       # Отдых
}

# ================== БЕЗОПАСНЫЙ ЗАПУСК ==================
def safe_bot_start(token):
    """Безопасный запуск бота с предотвращением конфликтов"""
    
    try:
        delete_url = f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true"
        response = requests.get(delete_url, timeout=10)
        print(f"🗑️ Удаление вебхуков: {response.status_code}")
        time.sleep(1)
    except Exception as e:
        print(f"⚠️ Ошибка при удалении вебхуков: {e}")
    
    try:
        test_url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(test_url, timeout=10)
        if response.status_code == 200:
            print("✅ Соединение с Telegram API установлено")
    except Exception as e:
        print(f"❌ Ошибка проверки соединения: {e}")
    
    bot = telebot.TeleBot(token)
    return bot

# ================== НАСТРОЙКИ ==================
# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Проверка токена
if not BOT_TOKEN:
    print("❌ КРИТИЧЕСКАЯ ОШИБКА: Переменная BOT_TOKEN не установлена.")
    print("   Установите переменную окружения или создайте файл config.py")
    exit(1)

# Создаем экземпляр базы данных
print("=" * 60)
print("🚀 ПОДГОТОВКА К ЗАПУСКУ БОТА")
print("=" * 60)
print(f"📁 Путь к базе данных: {DB_PATH}")
db = Database(DB_PATH)

# Создаем бота
bot = telebot.TeleBot(BOT_TOKEN)

# ================== БАЗА ДАННЫХ SQLite ==================

class Database:
    def __init__(self, db_path='data/game_bot.db'):
        self.db_path = db_path
        self.data_dir = os.path.dirname(db_path)
        
        # Создаем папку для данных, если ее нет
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            print(f"📁 Создана папка для данных: {self.data_dir}")
        
        # Инициализируем БД
        self.init_db()
        
        # Создаем резервную копию ПОСЛЕ инициализации
        self.create_backup()
    
    def create_backup(self):
        """Создание резервной копии базы данных"""
        try:
            if os.path.exists(self.db_path) and os.path.getsize(self.db_path) > 0:
                # Создаем папку для бэкапов
                backup_dir = 'backups'
                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir)
                
                # Формируем имя файла
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"{backup_dir}/game_bot_{timestamp}.db"
                
                # Копируем файл
                shutil.copy2(self.db_path, backup_name)
                print(f"✅ Резервная копия создана: {backup_name}")
                
                # Удаляем старые бэкапы (оставляем последние 5)
                self.cleanup_old_backups(backup_dir)
                
                return backup_name
        except Exception as e:
            print(f"⚠️ Не удалось создать резервную копию: {e}")
        return None
    
    def cleanup_old_backups(self, backup_dir, keep_last=5):
        """Удаление старых резервных копий"""
        try:
            # Получаем все файлы бэкапов, начинающиеся с game_bot_
            backup_files = glob.glob(f"{backup_dir}/game_bot_*.db")
            
            # Сортируем по времени создания
            backup_files.sort(key=os.path.getmtime)
            
            # Удаляем старые, оставляя только keep_last последних
            if len(backup_files) > keep_last:
                files_to_delete = backup_files[:-keep_last]
                for file in files_to_delete:
                    try:
                        os.remove(file)
                        print(f"🗑️ Удален старый бэкап: {os.path.basename(file)}")
                    except Exception as e:
                        print(f"⚠️ Не удалось удалить бэкап {file}: {e}")
        except Exception as e:
            print(f"⚠️ Не удалось очистить старые бэкапы: {e}")
    
    def get_connection(self):
        """Создаем соединение с базой данных"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Инициализация базы данных"""
        conn = None  # Объявляем переменную заранее
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
                    exp_to_next_level INTEGER DEFAULT 100,
                    skill_points INTEGER DEFAULT 0,
                    coins INTEGER DEFAULT 100,
                    health INTEGER DEFAULT 100,
                    max_health INTEGER DEFAULT 100,
                    attack INTEGER DEFAULT 10,
                    defense INTEGER DEFAULT 5,
                    daily_hunts INTEGER DEFAULT 0,
                    last_hunt_date DATE DEFAULT CURRENT_DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица инвентаря
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    item_type TEXT,
                    item_name TEXT,
                    quantity INTEGER DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
                )
            ''')
            
            conn.commit()
            
            # Проверяем состояние БД
            cursor.execute('SELECT COUNT(*) as count FROM users')
            user_count = cursor.fetchone()[0]
            
            file_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            print(f"✅ База данных инициализирована")
            print(f"   📊 Пользователей: {user_count}")
            print(f"   📏 Размер файла: {file_size} байт")
            
        except Exception as e:
            print(f"❌ Ошибка при инициализации БД: {e}")
            import traceback
            traceback.print_exc()
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
            return dict(user) if user else None
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
                (user_id, username, first_name, last_name, exp_to_next_level) 
                VALUES (?, ?, ?, ?, 100)
            ''', (user_id, username, first_name, last_name))
            conn.commit()
            print(f"👤 Создан новый пользователь: {user_id}")
            return True
        except sqlite3.IntegrityError:
            # Пользователь уже существует
            return True
        except Exception as e:
            print(f"❌ Ошибка при создании пользователя: {e}")
            return False
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
            return dict(user) if user else None
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
                (user_id, username, first_name, last_name, exp_to_next_level) 
                VALUES (?, ?, ?, ?, 100)
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
        """Завершение создания персонажа"""
        try:
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
                    max_health=100 + bonus['health'],
                    coins=100
                )
            return self.update_user(user_id, character_name=character_name, race=race)
        except Exception as e:
            print(f"❌ Ошибка при создании персонажа: {e}")
            return False
    
    def add_exp(self, user_id, exp_amount):
        """Добавление опыта и проверка уровня"""
        try:
            user = self.get_user(user_id)
            if not user:
                return False
            
            new_exp = user['exp'] + exp_amount
            new_level = user['level']
            skill_points_gained = 0
            
            # Проверяем повышение уровня
            while new_exp >= user['exp_to_next_level']:
                new_exp -= user['exp_to_next_level']
                new_level += 1
                skill_points_gained += 1
                exp_to_next = int(100 * (1.5 ** (new_level - 1)))
                
                self.update_user(
                    user_id,
                    level=new_level,
                    exp=new_exp,
                    exp_to_next_level=exp_to_next,
                    skill_points=user['skill_points'] + skill_points_gained
                )
                user = self.get_user(user_id)
            
            if exp_amount > 0 and skill_points_gained == 0:
                return self.update_user(user_id, exp=new_exp)
            
            return skill_points_gained > 0
        except Exception as e:
            print(f"❌ Ошибка при добавлении опыта: {e}")
            return False
    
    def add_coins(self, user_id, coins_amount):
        """Добавление монет пользователю"""
        try:
            user = self.get_user(user_id)
            if not user:
                return False
            
            new_coins = max(0, user['coins'] + coins_amount)
            return self.update_user(user_id, coins=new_coins)
        except Exception as e:
            print(f"❌ Ошибка при добавлении монет: {e}")
            return False
    
    def can_hunt_today(self, user_id):
        """Проверка, может ли пользователь охотиться сегодня"""
        try:
            user = self.get_user(user_id)
            if not user:
                return False, 0, 5
            
            today = datetime.date.today().isoformat()
            last_hunt_date = user['last_hunt_date']
            
            if last_hunt_date != today:
                self.update_user(user_id, daily_hunts=0, last_hunt_date=today)
                return True, 0, 5
            
            return user['daily_hunts'] < 5, user['daily_hunts'], 5
        except Exception as e:
            print(f"❌ Ошибка при проверке охоты: {e}")
            return False, 0, 5
    
    def increment_daily_hunts(self, user_id):
        """Увеличиваем счетчик охот за день"""
        try:
            user = self.get_user(user_id)
            if not user:
                return False
            
            today = datetime.date.today().isoformat()
            
            if user['last_hunt_date'] != today:
                return self.update_user(user_id, daily_hunts=1, last_hunt_date=today)
            
            return self.update_user(user_id, daily_hunts=user['daily_hunts'] + 1)
        except Exception as e:
            print(f"❌ Ошибка при увеличении счетчика охот: {e}")
            return False
    
    def use_skill_point(self, user_id, stat):
        """Использование очка навыка"""
        try:
            user = self.get_user(user_id)
            if not user or user['skill_points'] < 1:
                return False
            
            improvements = {
                'attack': {'attack': user['attack'] + 2},
                'defense': {'defense': user['defense'] + 2},
                'health': {'max_health': user['max_health'] + 15, 'health': min(user['health'] + 15, user['max_health'] + 15)}
            }
            
            if stat not in improvements:
                return False
            
            improvement = improvements[stat]
            improvement['skill_points'] = user['skill_points'] - 1
            
            return self.update_user(user_id, **improvement)
        except Exception as e:
            print(f"❌ Ошибка при использовании очка навыка: {e}")
            return False
    
    def add_to_inventory(self, user_id, item_type, item_name, quantity=1):
        """Добавление предмета в инвентарь"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, quantity FROM inventory 
                WHERE user_id = ? AND item_type = ? AND item_name = ?
            ''', (user_id, item_type, item_name))
            
            existing = cursor.fetchone()
            
            if existing:
                new_quantity = existing['quantity'] + quantity
                cursor.execute('''
                    UPDATE inventory SET quantity = ? 
                    WHERE id = ?
                ''', (new_quantity, existing['id']))
            else:
                cursor.execute('''
                    INSERT INTO inventory (user_id, item_type, item_name, quantity)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, item_type, item_name, quantity))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Ошибка при добавлении в инвентарь: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_inventory(self, user_id):
        """Получение инвентаря пользователя"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT item_type, item_name, quantity 
                FROM inventory 
                WHERE user_id = ? AND quantity > 0
                ORDER BY item_type, item_name
            ''', (user_id,))
            
            items = cursor.fetchall()
            return [dict(item) for item in items]
        except Exception as e:
            print(f"❌ Ошибка при получении инвентаря: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def use_item(self, user_id, item_type, item_name):
        """Использование предмета из инвентаря"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, quantity FROM inventory 
                WHERE user_id = ? AND item_type = ? AND item_name = ?
            ''', (user_id, item_type, item_name))
            
            item = cursor.fetchone()
            if not item or item['quantity'] < 1:
                return False
            
            if item['quantity'] == 1:
                cursor.execute('DELETE FROM inventory WHERE id = ?', (item['id'],))
            else:
                cursor.execute('''
                    UPDATE inventory SET quantity = quantity - 1 
                    WHERE id = ?
                ''', (item['id'],))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Ошибка при использовании предмета: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_race_description(self, race):
        """Получить описание расы"""
        descriptions = {
            'human': "👨 *Человек* - ⚖️ Сбалансированная раса\n+2 к атаке, +2 к защите, +20 к здоровью",
            'elf': "🧝 *Эльф* - 🏹 Мастера стрельбы\n+5 к атаке, +10 к здоровью",
            'orc': "👹 *Орк* - ⚔️ Сильные воины\n+8 к атаке, +3 к защите, +30 к здоровью",
            'dwarf': "🧙 *Гном* - 🛡️ Непробиваемые защитники\n+3 к атаке, +8 к защите, +25 к здоровью"
        }
        return descriptions.get(race, "Неизвестная раса")
    
    def calculate_health_regeneration(self, user_data):
        """Рассчитывает регенерацию здоровья на основе времени"""
        try:
            last_active = datetime.datetime.strptime(user_data['last_active'], '%Y-%m-%d %H:%M:%S')
            now = datetime.datetime.now()
            time_diff = (now - last_active).total_seconds() / 3600
            
            # Регенерация: 2% от макс. здоровья в час, максимум до 50% от макс. здоровья
            max_regeneration_percent = 0.5
            regeneration_per_hour = 0.02
            
            regen_amount = min(
                user_data['max_health'] * regeneration_per_hour * time_diff,
                user_data['max_health'] * max_regeneration_percent
            )
            
            if regen_amount > 0:
                new_health = min(user_data['health'] + regen_amount, user_data['max_health'])
                return int(new_health), int(regen_amount)
            
            return user_data['health'], 0
        except:
            return user_data['health'], 0
    
    def apply_health_regeneration(self, user_id):
        """Применяет регенерацию здоровья"""
        try:
            user = self.get_user(user_id)
            if not user:
                return False, 0
            
            new_health, regen_amount = self.calculate_health_regeneration(user)
            
            if regen_amount > 0:
                self.update_user(user_id, health=new_health)
                return True, regen_amount
            
            return False, 0
        except Exception as e:
            print(f"❌ Ошибка при регенерации здоровья: {e}")
            return False, 0
    
    def get_top_players(self, limit=5):
        """Получение топа игроков по уровню и опыту"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT character_name, race, level, exp, coins, attack, defense
                FROM users 
                WHERE character_name IS NOT NULL 
                ORDER BY level DESC, exp DESC, coins DESC
                LIMIT ?
            ''', (limit,))
            
            top_players = cursor.fetchall()
            return [dict(player) for player in top_players]
        except Exception as e:
            print(f"❌ Ошибка при получении топа игроков: {e}")
            return []
        finally:
            if conn:
                conn.close()

print(f"📁 Путь к базе данных: data/game_bot.db")
db = Database('data/game_bot.db')

# Хранилище временных данных
temp_user_data = {}

# ================== КЛАВИАТУРЫ ==================
def get_main_menu():
    """Клавиатура главного меню"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton('🎮 Профиль')
    btn2 = types.KeyboardButton('⚔️ Охота')
    btn3 = types.KeyboardButton('🏋️ Улучшения')
    btn4 = types.KeyboardButton('🛍️ Инвентарь')
    btn5 = types.KeyboardButton('🛒 Магазин')
    btn6 = types.KeyboardButton('💤 Отдых')
    btn7 = types.KeyboardButton('📊 Статистика')
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7)
    return markup

def get_race_keyboard():
    """Клавиатура выбора расы"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton('👨 Человек', callback_data='race_human')
    btn2 = types.InlineKeyboardButton('🧝 Эльф', callback_data='race_elf')
    btn3 = types.InlineKeyboardButton('👹 Орк', callback_data='race_orc')
    btn4 = types.InlineKeyboardButton('🧙 Гном', callback_data='race_dwarf')
    markup.add(btn1, btn2, btn3, btn4)
    return markup

def get_hunt_keyboard():
    """Клавиатура охоты"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton('🐀 Крыса', callback_data='hunt_rat')
    btn2 = types.InlineKeyboardButton('🐺 Волк', callback_data='hunt_wolf')
    btn3 = types.InlineKeyboardButton('🐗 Кабан', callback_data='hunt_boar')
    btn4 = types.InlineKeyboardButton('🐻 Медведь', callback_data='hunt_bear')
    btn5 = types.InlineKeyboardButton('🐉 Дракон', callback_data='hunt_dragon')
    markup.add(btn1, btn2, btn3, btn4, btn5)
    return markup

def get_upgrade_keyboard():
    """Клавиатура улучшений"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton('🗡️ Атака (+2)', callback_data='upgrade_attack')
    btn2 = types.InlineKeyboardButton('🛡️ Защита (+2)', callback_data='upgrade_defense')
    btn3 = types.InlineKeyboardButton('❤️ Здоровье (+15)', callback_data='upgrade_health')
    btn4 = types.InlineKeyboardButton('⬅️ Назад', callback_data='back_to_main')
    markup.add(btn1, btn2, btn3)
    markup.add(btn4)
    return markup

def get_shop_keyboard():
    """Клавиатура магазина"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton('❤️ Малое зелье (30 HP)', callback_data='buy_small_potion')
    btn2 = types.InlineKeyboardButton('💖 Большое зелье (60 HP)', callback_data='buy_big_potion')
    btn3 = types.InlineKeyboardButton('🍗 Еда (восст. 10 HP)', callback_data='buy_food')
    btn4 = types.InlineKeyboardButton('⬅️ Назад', callback_data='back_to_main')
    markup.add(btn1, btn2, btn3)
    markup.add(btn4)
    return markup

def get_inventory_keyboard():
    """Клавиатура инвентаря"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton('❤️ Исп. малое зелье', callback_data='use_small_potion')
    btn2 = types.InlineKeyboardButton('💖 Исп. большое зелье', callback_data='use_big_potion')
    btn3 = types.InlineKeyboardButton('🍗 Съесть еду', callback_data='use_food')
    btn4 = types.InlineKeyboardButton('⬅️ Назад', callback_data='back_to_main')
    markup.add(btn1, btn2, btn3)
    markup.add(btn4)
    return markup

def get_rest_keyboard():
    """Клавиатура отдыха"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton('💤 Короткий отдых (10 HP)', callback_data='rest_short')
    btn2 = types.InlineKeyboardButton('🛌 Долгий отдых (30 HP)', callback_data='rest_long')
    btn3 = types.InlineKeyboardButton('🏕️ Ночлег (50 HP)', callback_data='rest_night')
    btn4 = types.InlineKeyboardButton('⬅️ Назад', callback_data='back_to_main')
    markup.add(btn1, btn2, btn3)
    markup.add(btn4)
    return markup

# ================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==================
def auto_regenerate_health(user_id):
    """Автоматическая регенерация здоровья при любом действии"""
    try:
        regenerated, regen_amount = db.apply_health_regeneration(user_id)
        return regenerated, regen_amount
    except:
        return False, 0

def send_race_image(chat_id, race, caption):
    """Отправка изображения расы"""
    try:
        image_url = RACE_IMAGES.get(race, RACE_IMAGES['human'])
        bot.send_photo(chat_id, image_url, caption=caption, parse_mode='Markdown')
        return True
    except Exception as e:
        print(f"❌ Ошибка при отправке изображения расы: {e}")
        bot.send_message(chat_id, caption, parse_mode='Markdown')
        return False

def send_monster_image(chat_id, monster_type, caption):
    """Отправка изображения монстра"""
    try:
        image_url = MONSTER_IMAGES.get(monster_type, MONSTER_IMAGES['rat'])
        bot.send_photo(chat_id, image_url, caption=caption, parse_mode='Markdown')
        return True
    except Exception as e:
        print(f"❌ Ошибка при отправке изображения монстра: {e}")
        bot.send_message(chat_id, caption, parse_mode='Markdown')
        return False

def send_battle_result_image(chat_id, result_type, caption):
    """Отправка изображения результата боя"""
    try:
        image_url = BATTLE_IMAGES.get(result_type, BATTLE_IMAGES['victory'])
        bot.send_photo(chat_id, image_url, caption=caption, parse_mode='Markdown')
        return True
    except Exception as e:
        print(f"❌ Ошибка при отправке изображения результата: {e}")
        bot.send_message(chat_id, caption, parse_mode='Markdown')
        return False

def send_menu_image(chat_id, menu_type, caption):
    """Отправка изображения для меню"""
    try:
        image_url = MENU_IMAGES.get(menu_type, MENU_IMAGES['main'])
        bot.send_photo(chat_id, image_url, caption=caption, parse_mode='Markdown')
        return True
    except Exception as e:
        print(f"❌ Ошибка при отправке изображения меню: {e}")
        bot.send_message(chat_id, caption, parse_mode='Markdown')
        return False

# ================== ОБРАБОТЧИКИ КОМАНД ==================
@bot.message_handler(commands=['start'])
def start_command(message):
    """Обработчик команды /start"""
    user = message.from_user
    user_id = user.id
    
    # Авто-регенерация
    auto_regenerate_health(user_id)
    
    user_data = db.get_user(user_id)
    
    if user_data:
        if user_data.get('character_name') and user_data.get('race'):
            # Отправляем изображение персонажа
            race_image = RACE_IMAGES.get(user_data['race'], RACE_IMAGES['human'])
            caption = f"""
🎮 Добро пожаловать обратно, *{user_data['character_name']}*!

Вы - *{user_data['race'].capitalize()}* {user_data['level']} уровня.
Используйте меню ниже для управления персонажем!
            """
            
            try:
                bot.send_photo(message.chat.id, race_image, caption=caption, 
                             parse_mode='Markdown', reply_markup=get_main_menu())
            except:
                bot.send_message(message.chat.id, caption, 
                               parse_mode='Markdown', reply_markup=get_main_menu())
        else:
            bot.send_message(
                message.chat.id,
                "🎮 *Создание персонажа*\n\nДавайте завершим создание вашего героя! Как его зовут?\n(Введите имя персонажа, 2-20 символов)",
                parse_mode='Markdown',
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
🎮 Добро пожаловать в игру *"Hero's Path"*!

*Создайте своего уникального героя:*
1. Выберите имя
2. Выберите расу
3. Начните своё приключение!

*Как будут звать вашего героя?*
(Введите имя персонажа, 2-20 символов)
        """
        
        # Отправляем изображение главного меню
        send_menu_image(message.chat.id, 'main', welcome_text)
        
        temp_user_data[user_id] = {'step': 'waiting_name'}

@bot.message_handler(commands=['help'])
def help_command(message):
    """Обработчик команды /help"""
    help_text = """
🎮 *Hero's Path* - RPG игра в Telegram!

*Основные возможности:*
⚔️ *Охота* - сражайтесь с монстрами, получайте опыт и золото
🏋️ *Улучшения* - тратьте очки навыков на прокачку характеристик
🛍️ *Инвентарь* - используйте купленные предметы
🛒 *Магазин* - покупайте зелья и еду за золото
💤 *Отдых* - восстанавливайте здоровье со временем
📊 *Профиль* - просматривайте статистику персонажа

*Расы персонажа:*
👨 *Человек* - сбалансированная раса
🧝 *Эльф* - высокая атака, низкая защита
👹 *Орк* - очень высокая атака и здоровье
🧙 *Гном* - высокая защита

*Используйте кнопки меню для игры!*
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
            character_name = message.text.strip()
            
            if len(character_name) < 2:
                bot.send_message(message.chat.id, "❌ Имя должно быть не короче 2 символов. Попробуйте еще раз:")
                return
            
            if len(character_name) > 20:
                bot.send_message(message.chat.id, "❌ Имя должно быть не длиннее 20 символов. Попробуйте еще раз:")
                return
            
            temp_user_data[user_id]['character_name'] = character_name
            temp_user_data[user_id]['step'] = 'waiting_race'
            
            # Отправляем изображение выбора расы с описанием
            race_text = f"""
*{character_name}, выберите свою расу:*

Каждая раса имеет уникальные характеристики и внешний вид:
            """
            
            bot.send_message(
                message.chat.id,
                race_text,
                parse_mode='Markdown',
                reply_markup=get_race_keyboard()
            )
            return
    
    text = message.text
    
    if text == '🎮 Профиль':
        show_profile(message)
    elif text == '⚔️ Охота':
        show_hunt_menu(message)
    elif text == '🏋️ Улучшения':
        show_upgrade_menu(message)
    elif text == '🛍️ Инвентарь':
        show_inventory(message)
    elif text == '🛒 Магазин':
        show_shop_menu(message)
    elif text == '💤 Отдых':
        show_rest_menu(message)
    elif text == '📊 Статистика':
        show_stats(message)
    else:
        bot.send_message(
            message.chat.id,
            "🎮 Используйте кнопки меню для навигации!",
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
            race = call.data.replace('race_', '')
            
            if user_id not in temp_user_data:
                bot.answer_callback_query(call.id, "❌ Ошибка: данные сессии потеряны. Начните с /start")
                return
                
            character_name = temp_user_data[user_id].get('character_name', 'Герой')
            
            if db.complete_character_creation(user_id, character_name, race):
                # Удаляем временные данные
                if user_id in temp_user_data:
                    del temp_user_data[user_id]
                
                # Отправляем изображение созданного персонажа
                race_names = {
                    'human': '👨 Человек',
                    'elf': '🧝 Эльф',
                    'orc': '👹 Орк',
                    'dwarf': '🧙 Гном'
                }
                
                race_name_display = race_names.get(race, race.capitalize())
                
                welcome_text = f"""
🎉 *Персонаж создан!*

👤 *Имя:* {character_name}
🏹 *Раса:* {race_name_display}

{db.get_race_description(race)}

*Ваше эпическое приключение начинается!*
Используйте меню ниже для управления героем.
                """
                
                try:
                    bot.delete_message(chat_id, message_id)
                except:
                    pass
                
                # Отправляем изображение расы
                send_race_image(chat_id, race, welcome_text)
                
                time.sleep(1)
                bot.send_message(
                    chat_id,
                    "🎮 *Используйте кнопки меню для игры!*\n\n"
                    "⚔️ *Охота* - сражайтесь с монстрами\n"
                    "🏋️ *Улучшения* - тратьте очки навыков\n"
                    "🛒 *Магазин* - покупайте предметы\n"
                    "💤 *Отдых* - восстанавливайте здоровье\n"
                    "📊 *Профиль* - просматривайте статистику",
                    parse_mode='Markdown',
                    reply_markup=get_main_menu()
                )
            else:
                bot.answer_callback_query(call.id, "❌ Ошибка при создании персонажа!")
        
        elif call.data.startswith('hunt_'):
            monster_type = call.data.replace('hunt_', '')
            hunt_monster(call, monster_type)
        
        elif call.data.startswith('upgrade_'):
            stat = call.data.replace('upgrade_', '')
            upgrade_stat(call, stat)
        
        elif call.data.startswith('buy_'):
            item = call.data.replace('buy_', '')
            buy_item(call, item)
        
        elif call.data.startswith('use_'):
            item = call.data.replace('use_', '')
            use_item(call, item)
        
        elif call.data.startswith('rest_'):
            rest_type = call.data.replace('rest_', '')
            rest_action(call, rest_type)
        
        elif call.data == 'back_to_main':
            try:
                bot.delete_message(chat_id, message_id)
            except:
                pass
            
            send_menu_image(chat_id, 'main', "🎮 *Главное меню*\n\nВыберите действие:")
            bot.send_message(
                chat_id,
                "Используйте кнопки меню:",
                reply_markup=get_main_menu()
            )
    
    except Exception as e:
        print(f"❌ Ошибка в callback_handler: {e}")
        bot.answer_callback_query(call.id, "❌ Произошла ошибка!")

# ================== ФУНКЦИИ МЕНЮ ==================
def show_profile(message):
    """Показать профиль игрока"""
    user_id = message.from_user.id
    
    # Авто-регенерация
    regenerated, regen_amount = auto_regenerate_health(user_id)
    
    user_data = db.get_user(user_id)
    
    if not user_data or not user_data.get('character_name'):
        bot.send_message(
            message.chat.id,
            "🎮 *Сначала создайте персонажа!*\n\nНапишите /start чтобы начать приключение.",
            parse_mode='Markdown',
            reply_markup=get_main_menu()
        )
        return
    
    # Расчет процента здоровья
    health_percent = (user_data['health'] / user_data['max_health']) * 100
    health_bar = "❤️" * int(health_percent / 20) + "♡" * (5 - int(health_percent / 20))
    
    # Проверяем доступность охоты
    can_hunt, hunts_done, max_hunts = db.can_hunt_today(user_id)
    hunts_text = f"{hunts_done}/{max_hunts}"
    
    # Информация о регенерации
    regen_text = ""
    if regenerated and regen_amount > 0:
        regen_text = f"🔄 *Регенерация:* +{regen_amount} HP\n"
    
    if health_percent < 100:
        hours_for_full_regen = (100 - health_percent) / 2
        regen_text += f"⏳ *До полного восстановления:* ~{hours_for_full_regen:.1f} часов"
    
    # Отправляем изображение профиля
    profile_text = f"""
📊 *ПРОФИЛЬ ГЕРОЯ*

👤 *{user_data['character_name']}*
🏹 *Раса:* {user_data['race'].capitalize() if user_data['race'] else 'Не выбрана'}

{health_bar} {user_data['health']}/{user_data['max_health']}
{regen_text}

⚔️ *Характеристики:*
📊 Уровень: {user_data['level']}
⭐ Опыт: {user_data['exp']}/{user_data['exp_to_next_level']}
🔶 Очки навыков: {user_data['skill_points']}
💰 Золото: {user_data['coins']}
🗡️ Атака: {user_data['attack']}
🛡️ Защита: {user_data['defense']}

🎯 *Охота сегодня:* {hunts_text}
📅 Зарегистрирован: {user_data['created_at'][:10]}
    """
    
    # Отправляем изображение расы с профилем
    race_image = RACE_IMAGES.get(user_data.get('race', 'human'), RACE_IMAGES['human'])
    
    try:
        bot.send_photo(
            message.chat.id,
            race_image,
            caption=profile_text,
            parse_mode='Markdown',
            reply_markup=get_main_menu()
        )
    except:
        bot.send_message(
            message.chat.id,
            profile_text,
            parse_mode='Markdown',
            reply_markup=get_main_menu()
        )

def show_hunt_menu(message):
    """Показать меню охоты"""
    user_id = message.from_user.id
    can_hunt, hunts_done, max_hunts = db.can_hunt_today(user_id)
    
    if not can_hunt:
        bot.send_message(
            message.chat.id,
            f"❌ *Лимит охоты исчерпан!*\n\n"
            f"Вы уже сходили на охоту {hunts_done} раз сегодня.\n"
            f"Лимит: {max_hunts} охот в день.\n"
            f"Приходите завтра!",
            parse_mode='Markdown',
            reply_markup=get_main_menu()
        )
        return
    
    hunt_text = f"""
⚔️ *МЕНЮ ОХОТЫ*

Выберите противника для битвы:

🐀 *Крыса* - слабый монстр, идеален для новичков
🐺 *Волк* - быстрый и опасный хищник
🐗 *Кабан* - мощный боец средней сложности
🐻 *Медведь* - сильный и выносливый враг
🐉 *Дракон* - легендарный босс, только для сильнейших!

🎯 *Охот сегодня:* {hunts_done}/{max_hunts}
💰 *Совет:* Начинайте с легких монстров и постепенно увеличивайте сложность!
    """
    
    # Отправляем изображение для меню охоты
    send_monster_image(message.chat.id, 'wolf', hunt_text)
    
    # Отправляем клавиатуру отдельно
    bot.send_message(
        message.chat.id,
        "Выберите монстра:",
        reply_markup=get_hunt_keyboard()
    )

def show_upgrade_menu(message):
    """Показать меню улучшений"""
    user_id = message.from_user.id
    auto_regenerate_health(user_id)
    
    user_data = db.get_user(message.from_user.id)
    
    if not user_data:
        return
    
    upgrade_text = f"""
🏋️ *МЕНЮ УЛУЧШЕНИЙ*

Используйте *очки навыков* для улучшения характеристик:

🗡️ *Атака* (+2 к атаке) - 1 очко
🛡️ *Защита* (+2 к защите) - 1 очко
❤️ *Здоровье* (+15 к макс. здоровью) - 1 очко

*Ваши текущие характеристики:*
🔶 *Очков навыков:* {user_data['skill_points']}
🗡️ *Атака:* {user_data['attack']}
🛡️ *Защита:* {user_data['defense']}
❤️ *Макс. здоровье:* {user_data['max_health']}
❤️ *Текущее здоровье:* {user_data['health']}

*💡 Как получить очки навыков?*
Повышайте уровень! За каждый новый уровень вы получаете 1 очко навыка.
    """
    
    # Отправляем изображение для меню улучшений
    send_menu_image(message.chat.id, 'training', upgrade_text)
    
    bot.send_message(
        message.chat.id,
        "Выберите улучшение:",
        reply_markup=get_upgrade_keyboard()
    )

def show_inventory(message):
    """Показать инвентарь"""
    user_id = message.from_user.id
    auto_regenerate_health(user_id)
    
    user_data = db.get_user(user_id)
    
    if not user_data:
        return
    
    inventory = db.get_inventory(user_id)
    
    inventory_text = "📦 *ВАШ ИНВЕНТАРЬ:*\n\n"
    if not inventory:
        inventory_text += "*Ваш инвентарь пуст!*\n🏪 Посетите *магазин*, чтобы купить полезные предметы."
    else:
        for item in inventory:
            emoji = "❤️" if "малое" in item['item_name'] else "💖" if "большое" in item['item_name'] else "🍗"
            inventory_text += f"{emoji} *{item['item_name']}:* {item['quantity']} шт.\n"
    
    inventory_text += f"\n💰 *Золото:* {user_data['coins']}"
    inventory_text += f"\n❤️ *Здоровье:* {user_data['health']}/{user_data['max_health']}"
    inventory_text += "\n\n🎒 *Совет:* Используйте предметы перед сложными битвами!"
    
    # Отправляем изображение для инвентаря
    send_menu_image(message.chat.id, 'inventory', inventory_text)
    
    if inventory:
        bot.send_message(
            message.chat.id,
            "Выберите предмет для использования:",
            reply_markup=get_inventory_keyboard()
        )
    else:
        bot.send_message(
            message.chat.id,
            "🛒 Посетите магазин, чтобы купить предметы!",
            reply_markup=get_main_menu()
        )

def show_shop_menu(message):
    """Показать меню магазина"""
    user_id = message.from_user.id
    auto_regenerate_health(user_id)
    
    user_data = db.get_user(message.from_user.id)
    
    if not user_data:
        return
    
    shop_text = f"""
🛒 *МАГАЗИН ПРИКЛЮЧЕНЦА*

Здесь можно купить полезные предметы для вашего героя:

❤️ *Малое зелье здоровья* - восстанавливает 30 HP
💰 Цена: *20 золота*

💖 *Большое зелье здоровья* - восстанавливает 60 HP
💰 Цена: *35 золота*

🍗 *Еда* - восстанавливает 10 HP, идеально для легких ран
💰 Цена: *5 золота*

*💰 Ваш баланс:* {user_data['coins']} золота

*🏪 Совет:* Всегда имейте запас зелий для опасных приключений!
    """
    
    # Отправляем изображение для магазина
    send_menu_image(message.chat.id, 'shop', shop_text)
    
    bot.send_message(
        message.chat.id,
        "Выберите товар:",
        reply_markup=get_shop_keyboard()
    )

def show_rest_menu(message):
    """Показать меню отдыха"""
    user_id = message.from_user.id
    auto_regenerate_health(user_id)
    
    user_data = db.get_user(message.from_user.id)
    
    if not user_data:
        return
    
    rest_text = f"""
💤 *МЕНЮ ОТДЫХА*

Ваше здоровье восстанавливается со временем:
• *Естественная регенерация:* 2% от макс. здоровья в час
• *Пассивное восстановление:* происходит при открытии профиля

*Быстрый отдых:*
💤 *Короткий отдых* - +10 HP (бесплатно, 1 раз в час)
🛌 *Долгий отдых* - +30 HP (стоимость: 10💰)
🏕️ *Ночлег* - +50 HP (стоимость: 20💰)

*Текущее здоровье:* {user_data['health']}/{user_data['max_health']}
*Ваши монеты:* {user_data['coins']}💰

Выберите тип отдыха:
    """
    
    # Отправляем изображение для отдыха
    send_menu_image(message.chat.id, 'rest', rest_text)
    
    bot.send_message(
        message.chat.id,
        "Выберите тип отдыха:",
        reply_markup=get_rest_keyboard()
    )

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
        
        # Получаем топ 5 игроков
        top_players = db.get_top_players(5)
        
        race_stats = ""
        for race in races:
            race_name = {
                'human': '👨 Люди',
                'elf': '🧝 Эльфы',
                'orc': '👹 Орки',
                'dwarf': '🧙 Гномы'
            }.get(race['race'], race['race'])
            race_stats += f"{race_name}: {race['count']}\n"
        
        # Формируем текст топа игроков
        top_players_text = ""
        if top_players:
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
            for i, player in enumerate(top_players):
                race_emoji = {
                    'human': '👨',
                    'elf': '🧝', 
                    'orc': '👹',
                    'dwarf': '🧙'
                }.get(player.get('race', 'human'), '👤')
                
                medal = medals[i] if i < len(medals) else f"{i+1}."
                top_players_text += f"{medal} {race_emoji} {player['character_name']} - {player['level']} ур. ({player['coins']}💰)\n"
        else:
            top_players_text = "Пока нет игроков в топе\n"
        
        stats_text = f"""
📊 *СТАТИСТИКА СЕРВЕРА*

👥 Всего игроков: {total_users}
💰 Всего золота в игре: {total_coins}
🏆 Максимальный уровень: {max_level}

*Распределение рас:*
{race_stats}

🏆 *ТОП-5 ИГРОКОВ:*
{top_players_text}
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

def hunt_monster(call, monster_type):
    """Охота на монстра"""
    user_id = call.from_user.id
    user_data = db.get_user(user_id)
    
    if not user_data:
        bot.answer_callback_query(call.id, "❌ Персонаж не найден!")
        return
    
    # Проверяем лимит охоты
    can_hunt, hunts_done, max_hunts = db.can_hunt_today(user_id)
    if not can_hunt:
        bot.answer_callback_query(call.id, f"❌ Лимит охоты исчерпан! ({hunts_done}/{max_hunts})")
        return
    
    monsters = {
        'rat': {
            'name': '🐀 Крыса', 
            'health': 20, 
            'attack': 5, 
            'defense': 1, 
            'exp': 5, 
            'coins': 3,
            'description': 'Маленькая, но опасная тварь из подземелий'
        },
        'wolf': {
            'name': '🐺 Волк', 
            'health': 40, 
            'attack': 10, 
            'defense': 3, 
            'exp': 10, 
            'coins': 8,
            'description': 'Быстрый и безжалостный хищник лесов'
        },
        'boar': {
            'name': '🐗 Кабан', 
            'health': 70, 
            'attack': 15, 
            'defense': 5, 
            'exp': 20, 
            'coins': 15,
            'description': 'Мощный зверь с острыми клыками'
        },
        'bear': {
            'name': '🐻 Медведь', 
            'health': 120, 
            'attack': 25, 
            'defense': 8, 
            'exp': 35, 
            'coins': 25,
            'description': 'Грозный хозяин леса, сокрушающий врагов'
        },
        'dragon': {
            'name': '🐉 Дракон', 
            'health': 200, 
            'attack': 40, 
            'defense': 15, 
            'exp': 60, 
            'coins': 50,
            'description': 'Легендарное чудовище, повелитель огня и страха'
        }
    }
    
    monster = monsters.get(monster_type, monsters['rat'])
    
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    
    # Симуляция боя с несколькими раундами
    player_health = user_data['health']
    monster_health = monster['health']
    
    battle_log = []
    rounds = 0
    
    while player_health > 0 and monster_health > 0 and rounds < 10:
        rounds += 1
        
        # Игрок атакует
        player_damage = max(1, user_data['attack'] + random.randint(-2, 5) - monster['defense'])
        monster_health -= player_damage
        
        # Критический урон с шансом 20%
        is_critical = random.random() < 0.2
        if is_critical:
            player_damage = int(player_damage * 1.5)
            battle_log.append(f"🎯 *Раунд {rounds}:* КРИТИЧЕСКИЙ УДАР! Вы нанесли {player_damage} урона! 💥")
        else:
            battle_log.append(f"🎯 *Раунд {rounds}:* Вы нанесли {player_damage} урона")
        
        if monster_health <= 0:
            break
        
        # Монстр атакует
        monster_damage = max(1, monster['attack'] + random.randint(-1, 3) - user_data['defense'])
        player_health -= monster_damage
        
        # Уклонение с шансом 15%
        if random.random() < 0.15:
            battle_log.append(f"🌀 *Раунд {rounds}:* Вы увернулись от атаки {monster['name']}! 🍃")
        else:
            battle_log.append(f"💥 *Раунд {rounds}:* {monster['name']} нанес {monster_damage} урона")
    
    # Определяем победителя
    if player_health > 0:
        # Победа
        exp_gained = monster['exp']
        coins_gained = monster['coins']
        health_lost = user_data['health'] - player_health
        
        # Начисляем награды
        level_up = db.add_exp(user_id, exp_gained)
        db.add_coins(user_id, coins_gained)
        db.update_user(user_id, health=player_health)
        db.increment_daily_hunts(user_id)
        
        result_text = f"""
🎉 *ВЕЛИКОЛЕПНАЯ ПОБЕДА!*

Вы победили {monster['name']} за {rounds} раундов!

🏆 *НАГРАДЫ ЗА ПОБЕДУ:*
⭐ Опыт: +{exp_gained}
💰 Золото: +{coins_gained}
💔 Потеряно здоровья: {health_lost}
❤️ Осталось здоровья: {player_health}
        """
        
        # if level_up:
        #     result_text += "\n\n✨ *УРОВЕНЬ ПОВЫШЕН!* ✨\nПолучено 1 очко навыка! 🏋️"
        #     # Отправляем изображение повышения уровня
        #     send_battle_result_image(call.message.chat.id, 'level_up', result_text)
        # else:
        #     # Отправляем изображение победы
        #     send_battle_result_image(call.message.chat.id, 'victory', result_text)
        
        # Добавляем лог боя
        battle_log_text = "\n\n*📜 ХРОНИКА БИТВЫ:*\n" + "\n".join(battle_log[:6])
        battle_log_text += f"\n\n🎯 *Охот сегодня:* {hunts_done + 1}/{max_hunts}"
        
        bot.send_message(
            call.message.chat.id,
            battle_log_text,
            parse_mode='Markdown'
        )
        
    else:
        # Поражение
        health_lost = user_data['health']
        coins_lost = min(20, user_data['coins'])
        
        db.update_user(user_id, health=1)
        db.add_coins(user_id, -coins_lost)
        db.increment_daily_hunts(user_id)
        
        result_text = f"""
💀 *ГЕРОИЧЕСКОЕ ПОРАЖЕНИЕ!*

{monster['name']} оказался слишком сильным!

⚔️ *ПОТЕРИ:*
💔 Потеряно здоровья: {health_lost}
💸 Потеряно золота: {coins_lost}
❤️ Ваше здоровье восстановлено до 1

📜 *МУДРОСТЬ:* Даже поражение дает опыт. Вернитесь сильнее!
        """
        
        # Отправляем изображение поражения
        send_battle_result_image(call.message.chat.id, 'defeat', result_text)
        
        battle_log_text = "\n\n*📜 ХРОНИКА БИТВЫ:*\n" + "\n".join(battle_log[:6])
        battle_log_text += f"\n\n🎯 *Охот сегодня:* {hunts_done + 1}/{max_hunts}"
        
        bot.send_message(
            call.message.chat.id,
            battle_log_text,
            parse_mode='Markdown'
        )

def upgrade_stat(call, stat):
    """Улучшение характеристики"""
    user_id = call.from_user.id
    user_data = db.get_user(user_id)
    
    if not user_data:
        bot.answer_callback_query(call.id, "❌ Персонаж не найден!")
        return
    
    if user_data['skill_points'] < 1:
        bot.answer_callback_query(call.id, "❌ Недостаточно очков навыков!")
        return
    
    if db.use_skill_point(user_id, stat):
        user_data = db.get_user(user_id)
        
        stat_names = {
            'attack': '🗡️ Атаку',
            'defense': '🛡️ Защиту',
            'health': '❤️ Максимальное здоровье'
        }
        
        result_text = f"""
✅ *УЛУЧШЕНИЕ УСПЕШНО!*

Вы улучшили {stat_names[stat]}!

🔶 *Осталось очков навыков:* {user_data['skill_points']}
🗡️ *Атака:* {user_data['attack']}
🛡️ *Защита:* {user_data['defense']}
❤️ *Макс. здоровье:* {user_data['max_health']}
❤️ *Текущее здоровье:* {user_data['health']}

🏋️ *Продолжайте тренировки, герой!*
        """
        
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        
        # Отправляем изображение расы с результатом улучшения
        race_image = RACE_IMAGES.get(user_data.get('race', 'human'), RACE_IMAGES['human'])
        
        try:
            bot.send_photo(
                call.message.chat.id,
                race_image,
                caption=result_text,
                parse_mode='Markdown'
            )
        except:
            bot.send_message(
                call.message.chat.id,
                result_text,
                parse_mode='Markdown'
            )
    else:
        bot.answer_callback_query(call.id, "❌ Ошибка при улучшении!")

def buy_item(call, item):
    """Покупка предмета в магазине"""
    user_id = call.from_user.id
    user_data = db.get_user(user_id)
    
    if not user_data:
        bot.answer_callback_query(call.id, "❌ Персонаж не найден!")
        return
    
    items = {
        'small_potion': {
            'name': 'Малое зелье здоровья', 
            'type': 'potion', 
            'price': 20, 
            'heal': 30,
            'emoji': '❤️'
        },
        'big_potion': {
            'name': 'Большое зелье здоровья', 
            'type': 'potion', 
            'price': 35, 
            'heal': 60,
            'emoji': '💖'
        },
        'food': {
            'name': 'Еда', 
            'type': 'food', 
            'price': 5, 
            'heal': 10,
            'emoji': '🍗'
        }
    }
    
    item_data = items.get(item)
    if not item_data:
        bot.answer_callback_query(call.id, "❌ Предмет не найден!")
        return
    
    if user_data['coins'] < item_data['price']:
        bot.answer_callback_query(call.id, f"❌ Недостаточно золота! Нужно {item_data['price']}💰")
        return
    
    # Покупка
    if db.add_to_inventory(user_id, item_data['type'], item_data['name']):
        db.add_coins(user_id, -item_data['price'])
        user_data = db.get_user(user_id)
        
        result_text = f"""
🛒 *ПОКУПКА УСПЕШНА!*

{item_data['emoji']} Вы купили *{item_data['name']}*!

💸 *Стоимость:* {item_data['price']}💰
💰 *Осталось золота:* {user_data['coins']}

🎒 Предмет добавлен в ваш инвентарь!

🏪 *Приходите еще, путник!*
        """
        
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        
        # Отправляем изображение магазина с результатом покупки
        send_menu_image(call.message.chat.id, 'shop', result_text)
    else:
        bot.answer_callback_query(call.id, "❌ Ошибка при покупке!")

def use_item(call, item):
    """Использование предмета"""
    user_id = call.from_user.id
    user_data = db.get_user(user_id)
    
    if not user_data:
        bot.answer_callback_query(call.id, "❌ Персонаж не найден!")
        return
    
    items = {
        'small_potion': {'name': 'Малое зелье здоровья', 'type': 'potion', 'heal': 30, 'emoji': '❤️'},
        'big_potion': {'name': 'Большое зелье здоровья', 'type': 'potion', 'heal': 60, 'emoji': '💖'},
        'food': {'name': 'Еда', 'type': 'food', 'heal': 10, 'emoji': '🍗'}
    }
    
    item_data = items.get(item)
    if not item_data:
        bot.answer_callback_query(call.id, "❌ Предмет не найден!")
        return
    
    # Использование предмета
    if db.use_item(user_id, item_data['type'], item_data['name']):
        old_health = user_data['health']
        new_health = min(old_health + item_data['heal'], user_data['max_health'])
        db.update_user(user_id, health=new_health)
        user_data = db.get_user(user_id)
        
        heal_amount = new_health - old_health
        
        result_text = f"""
✅ *ПРЕДМЕТ ИСПОЛЬЗОВАН!*

{item_data['emoji']} Вы использовали *{item_data['name']}*!

❤️ *Восстановлено здоровья:* +{heal_amount}
❤️ *Текущее здоровье:* {user_data['health']}/{user_data['max_health']}

⚔️ *Теперь вы готовы к новым подвигам!*
        """
        
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        
        # Отправляем изображение инвентаря с результатом
        send_menu_image(call.message.chat.id, 'inventory', result_text)
    else:
        bot.answer_callback_query(call.id, "❌ У вас нет этого предмета!")

def rest_action(call, rest_type):
    """Отдых для восстановления здоровья"""
    user_id = call.from_user.id
    user_data = db.get_user(user_id)
    
    if not user_data:
        bot.answer_callback_query(call.id, "❌ Персонаж не найден!")
        return
    
    # Проверяем лимиты на короткий отдых
    last_rest_key = f"last_rest_{user_id}"
    
    if rest_type == 'short':
        last_rest_time = temp_user_data.get(last_rest_key)
        if last_rest_time:
            time_since_last_rest = time.time() - last_rest_time
            if time_since_last_rest < 3600:
                wait_time = int((3600 - time_since_last_rest) / 60)
                bot.answer_callback_query(
                    call.id, 
                    f"❌ Короткий отдых доступен раз в час. Ждите еще {wait_time} мин."
                )
                return
        
        heal_amount = 10
        cost = 0
    
    elif rest_type == 'long':
        heal_amount = 30
        cost = 10
    
    elif rest_type == 'night':
        heal_amount = 50
        cost = 20
    
    else:
        bot.answer_callback_query(call.id, "❌ Неизвестный тип отдыха!")
        return
    
    if cost > 0 and user_data['coins'] < cost:
        bot.answer_callback_query(call.id, f"❌ Недостаточно золота! Нужно {cost}💰")
        return
    
    if user_data['health'] >= user_data['max_health']:
        bot.answer_callback_query(call.id, "❌ У вас уже полное здоровье!")
        return
    
    new_health = min(user_data['health'] + heal_amount, user_data['max_health'])
    actual_heal = new_health - user_data['health']
    
    if actual_heal <= 0:
        bot.answer_callback_query(call.id, "❌ Не удалось восстановить здоровье!")
        return
    
    if cost > 0:
        db.add_coins(user_id, -cost)
    
    db.update_user(user_id, health=new_health)
    
    if rest_type == 'short':
        temp_user_data[last_rest_key] = time.time()
    
    user_data = db.get_user(user_id)
    
    rest_names = {
        'short': '💤 Короткий отдых',
        'long': '🛌 Долгий отдых',
        'night': '🏕️ Ночлег'
    }
    
    result_text = f"""
✅ *ОТДЫХ ЗАВЕРШЕН!*

{rest_names[rest_type]} прошел успешно!

❤️ *Восстановлено здоровья:* +{actual_heal} HP
❤️ *Текущее здоровье:* {user_data['health']}/{user_data['max_health']}
"""
    
    if cost > 0:
        result_text += f"💰 *Потрачено золота:* {cost}💰\n"
    
    result_text += f"\n💰 *Осталось золота:* {user_data['coins']}💰"
    
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    
    # Отправляем изображение отдыха с результатом
    send_menu_image(call.message.chat.id, 'rest', result_text)

# ================== ЗАПУСК БОТА ==================
def main():
   # Проверяем состояние базы данных
    print("=" * 50)
    print("🔍 ПРОВЕРКА СОСТОЯНИЯ БАЗЫ ДАННЫХ")
    print("=" * 50)
    
    if os.path.exists('game_bot.db'):
        file_size = os.path.getsize('game_bot.db')
        file_mtime = datetime.datetime.fromtimestamp(os.path.getmtime('game_bot.db'))
        print(f"📁 Файл БД: game_bot.db")
        print(f"📏 Размер: {file_size} байт")
        print(f"🕐 Последнее изменение: {file_mtime}")
    else:
        print("⚠️ Внимание: файл БД не найден! Будет создан новый.")
    
    print("=" * 50)
    print("🎮 БОТ 'Hero's Path' ЗАПУЩЕН")
    print(f"🤖 Используется SQLite база данных")
    print("=" * 50)
    
    try:
        bot_info = bot.get_me()
        print(f"🤖 Бот: @{bot_info.username} (ID: {bot_info.id})")
        print(f"📝 Имя бота: {bot_info.first_name}")
        
        print("🔄 Бот запускает polling...")
        bot.infinity_polling(
            skip_pending=True,
            timeout=20,
            long_polling_timeout=5
        )
        
    except Exception as e:
        print(f"❌ Критическая ошибка при запуске бота: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()
