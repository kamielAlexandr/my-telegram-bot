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

try:
    from config import BOT_TOKEN, DB_PATH
except ImportError:
    # Если config.py не существует, используем значения по умолчанию
    BOT_TOKEN = os.environ.get('BOT_TOKEN')
    DB_PATH = 'game_bot.db'

# ================== ИЗОБРАЖЕНИЯ ==================
RACE_IMAGES = {
    'human': 'https://i126.fastpic.org/thumb/2026/0130/2c/_d2515d33e45fa7ffb5246cacabdaba2c.jpeg',
    'elf': 'https://i126.fastpic.org/thumb/2026/0130/81/_d3d94be5aa45b9239aeb5adc41443081.jpeg',
    'orc': 'https://i126.fastpic.org/thumb/2026/0130/20/_b8c1f666bd21bb415e8fb35145eb3e20.jpeg',
    'dwarf': 'https://i126.fastpic.org/thumb/2026/0130/5b/_c188fac4eb6d205bd9fc0486c9b9355b.jpeg'
}

MONSTER_IMAGES = {
    'rat': 'https://i126.fastpic.org/thumb/2026/0131/e9/a82df7379d77b0006066c011474d16e9.jpeg',
    'wolf': 'https://i126.fastpic.org/thumb/2026/0131/38/ce2b3221d3076bcb3db2dedfff33fa38.jpeg',
    'boar': 'https://i126.fastpic.org/thumb/2026/0131/25/317fa1bb5307624d5546b7ca5e173725.jpeg',
    'bear': 'https://i126.fastpic.org/thumb/2026/0131/45/2db4265909ceb3e92fc77ab6297b9045.jpeg',
    'spider': 'https://i126.fastpic.org/thumb/2026/0131/c2/df5fb497f92b3f7578ca0a0ab53c8ac2.jpeg'
}

BATTLE_IMAGES = {
    'victory': 'https://sun9-29.userapi.com/impg/victory_image/photo.jpg?size=800x600',
    'defeat': 'https://sun9-12.userapi.com/impg/defeat_image/photo.jpg?size=800x600',
    'level_up': 'https://avatars.mds.yandex.net/get-images-cbir/level_up_image/orig'
}

MENU_IMAGES = {
    'main': 'https://storage.yandexcloud.net/game-bot-images/menu/main.jpg',
    'profile': 'https://sun9-47.userapi.com/impg/profile_image/photo.jpg',
    'shop': 'https://avatars.mds.yandex.net/get-images-cbir/shop_image/orig',
    'inventory': 'https://storage.yandexcloud.net/game-bot-images/menu/inventory.png',
    'training': 'https://sun9-33.userapi.com/impg/training_image/photo.jpg',
    'rest': 'https://avatars.mds.yandex.net/get-images-cbir/rest_image/orig'
}

# ================== БАЗА ДАННЫХ ==================
class Database:
    def __init__(self, db_path='game_bot.db'):
        self.db_path = db_path
        
        # Извлекаем директорию из пути
        self.data_dir = os.path.dirname(db_path)
        
        # Если указана директория и она не пустая строка, создаем её
        if self.data_dir and not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir, exist_ok=True)
            print(f"📁 Создана папка для данных: {self.data_dir}")
        
        # Инициализируем БД
        self.init_db()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
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
            print("✅ База данных инициализирована")
            
        except Exception as e:
            print(f"❌ Ошибка при инициализации БД: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if conn:
                conn.close()
    
    def get_user(self, user_id):
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
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO users 
                (user_id, username, first_name, last_name, exp_to_next_level) 
                VALUES (?, ?, ?, ?, 100)
            ''', (user_id, username, first_name, last_name))
            conn.commit()
            print(f"👤 Создан/обновлен пользователь: {user_id}")
            return True
        except Exception as e:
            print(f"❌ Ошибка при создании пользователя: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def update_user(self, user_id, **kwargs):
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
        try:
            user = self.get_user(user_id)
            if not user:
                return False
            
            new_exp = user['exp'] + exp_amount
            new_level = user['level']
            skill_points_gained = 0
            
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
        descriptions = {
            'human': "👨 *Человек* - ⚖️ Сбалансированная раса\n+2 к атаке, +2 к защите, +20 к здоровью",
            'elf': "🧝 *Эльф* - 🏹 Мастера стрельбы\n+5 к атаке, +10 к здоровью",
            'orc': "👹 *Орк* - ⚔️ Сильные воины\n+8 к атаке, +3 к защите, +30 к здоровью",
            'dwarf': "🧙 *Гном* - 🛡️ Непробиваемые защитники\n+3 к атаке, +8 к защите, +25 к здоровью"
        }
        return descriptions.get(race, "Неизвестная раса")
    
    def get_top_players(self, limit=5):
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

# ================== НАСТРОЙКИ ==================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

if not BOT_TOKEN:
    print("❌ КРИТИЧЕСКАЯ ОШИБКА: Переменная BOT_TOKEN не установлена.")
    print("   Установите переменную окружения или создайте файл config.py")
    exit(1)

db = Database('game_bot.db')
bot = telebot.TeleBot(BOT_TOKEN)

# Хранилище временных данных
temp_user_data = {}

# ================== КЛАВИАТУРЫ ==================
def get_main_menu():
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
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton('👨 Человек', callback_data='race_human')
    btn2 = types.InlineKeyboardButton('🧝 Эльф', callback_data='race_elf')
    btn3 = types.InlineKeyboardButton('👹 Орк', callback_data='race_orc')
    btn4 = types.InlineKeyboardButton('🧙 Гном', callback_data='race_dwarf')
    markup.add(btn1, btn2, btn3, btn4)
    return markup

def get_hunt_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton('🐀 Крыса', callback_data='hunt_rat')
    btn2 = types.InlineKeyboardButton('🐺 Волк', callback_data='hunt_wolf')
    btn3 = types.InlineKeyboardButton('🐗 Кабан', callback_data='hunt_boar')
    btn4 = types.InlineKeyboardButton('🐻 Медведь', callback_data='hunt_bear')
    btn5 = types.InlineKeyboardButton('🕷️ Паук', callback_data='hunt_spider')
    markup.add(btn1, btn2, btn3, btn4, btn5)
    return markup

def get_battle_keyboard(battle_state):
    """Клавиатура для интерактивного боя"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # Базовые действия
    btn1 = types.InlineKeyboardButton('🗡️ Атаковать', callback_data='battle_attack')
    btn2 = types.InlineKeyboardButton('🛡️ Блокировать', callback_data='battle_block')
    btn3 = types.InlineKeyboardButton('💥 Супер-удар', callback_data='battle_super')
    
    # Отображение супер-удара в зависимости от энергии
    energy_emoji = '⚡' * battle_state['energy'] + '○' * (3 - battle_state['energy'])
    btn3.text = f'{energy_emoji} Супер-удар'
    
    # Если энергии нет, делаем кнопку неактивной
    if battle_state['energy'] < 3:
        btn3.callback_data = 'battle_no_energy'
    
    markup.add(btn1, btn2, btn3)
    
    # Дополнительные действия
    btn4 = types.InlineKeyboardButton('🧪 Исп. зелье', callback_data='battle_potion')
    btn5 = types.InlineKeyboardButton('🏃 Бежать', callback_data='battle_flee')
    markup.add(btn4, btn5)
    
    return markup

def get_upgrade_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton('🗡️ Атака (+2)', callback_data='upgrade_attack')
    btn2 = types.InlineKeyboardButton('🛡️ Защита (+2)', callback_data='upgrade_defense')
    btn3 = types.InlineKeyboardButton('❤️ Здоровье (+15)', callback_data='upgrade_health')
    btn4 = types.InlineKeyboardButton('⬅️ Назад', callback_data='back_to_main')
    markup.add(btn1, btn2, btn3)
    markup.add(btn4)
    return markup

def get_shop_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton('❤️ Малое зелье (30 HP)', callback_data='buy_small_potion')
    btn2 = types.InlineKeyboardButton('💖 Большое зелье (60 HP)', callback_data='buy_big_potion')
    btn3 = types.InlineKeyboardButton('🍗 Еда (восст. 10 HP)', callback_data='buy_food')
    btn4 = types.InlineKeyboardButton('⬅️ Назад', callback_data='back_to_main')
    markup.add(btn1, btn2, btn3)
    markup.add(btn4)
    return markup

def get_inventory_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton('❤️ Исп. малое зелье', callback_data='use_small_potion')
    btn2 = types.InlineKeyboardButton('💖 Исп. большое зелье', callback_data='use_big_potion')
    btn3 = types.InlineKeyboardButton('🍗 Съесть еду', callback_data='use_food')
    btn4 = types.InlineKeyboardButton('⬅️ Назад', callback_data='back_to_main')
    markup.add(btn1, btn2, btn3)
    markup.add(btn4)
    return markup

def get_rest_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton('💤 Короткий отдых (10 HP)', callback_data='rest_short')
    btn2 = types.InlineKeyboardButton('🛌 Долгий отдых (30 HP)', callback_data='rest_long')
    btn3 = types.InlineKeyboardButton('🏕️ Ночлег (50 HP)', callback_data='rest_night')
    btn4 = types.InlineKeyboardButton('⬅️ Назад', callback_data='back_to_main')
    markup.add(btn1, btn2, btn3)
    markup.add(btn4)
    return markup

# ================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==================
def get_race_ability_description(race):
    """Получить описание расовой способности"""
    abilities = {
        'human': "👑 *Сокрушительный удар:* двойной урон от атаки",
        'elf': "🎯 *Точный выстрел:* игнорирует защиту врага, высокий урон",
        'orc': "💢 *Ярость орка:* тройной урон, но вы теряете HP",
        'dwarf': "⚒️ *Удар молота:* урон = атака + защита, оглушает врага"
    }
    return abilities.get(race, "Неизвестная способность")

def update_battle_message(call, battle_state, log_text=""):
    """Обновление сообщения с текущим состоянием боя"""
    user_id = call.from_user.id
    user_data = db.get_user(user_id)
    monster = battle_state['monster']
    
    # Создаем текст состояния
    health_bar_player = "❤️" * max(1, int((battle_state['player_health'] / battle_state['player_max_health']) * 10))
    health_bar_monster = "❤️" * max(1, int((battle_state['monster_health'] / monster['health']) * 10))
    
    energy_bar = "⚡" * battle_state['energy'] + "○" * (3 - battle_state['energy'])
    
    status_text = f"""
⚔️ *РАУНД {battle_state['round']}*

👤 *{user_data['character_name']}* ({user_data['race'].capitalize()})
{health_bar_player} {battle_state['player_health']}/{battle_state['player_max_health']}

VS

🎯 *{monster['name']}*
{health_bar_monster} {battle_state['monster_health']}/{monster['health']}

🌀 *Энергия:* {energy_bar} ({battle_state['energy']}/3)

"""
    
    # Добавляем лог последнего раунда
    if log_text:
        status_text += f"{log_text}\n"
    
    status_text += "\n*Выберите действие:*"
    
    # Обновляем сообщение
    try:
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=status_text,
            parse_mode='Markdown',
            reply_markup=get_battle_keyboard(battle_state)
        )
    except Exception as e:
        print(f"Ошибка обновления сообщения: {e}")

def process_battle_action(call, battle_state, action):
    """Обработка одного действия в бою"""
    user_id = call.from_user.id
    user_data = db.get_user(user_id)
    monster = battle_state['monster']
    
    battle_log = []
    
    # === ХОД ИГРОКА ===
    if action == 'attack':
        # Базовая атака
        damage = max(1, battle_state['player_attack'] + random.randint(-3, 7))
        damage = max(1, damage - monster['defense'] // 3)
        
        # Критический удар игрока (15% шанс)
        if random.random() < 0.15:
            damage = int(damage * 1.8)
            battle_log.append(f"🎯 *КРИТИЧЕСКИЙ УДАР!* {damage} урона!")
        else:
            battle_log.append(f"🗡️ *Вы атакуете:* {damage} урона")
        
        battle_state['monster_health'] -= damage
        battle_state['energy'] = min(3, battle_state['energy'] + 1)  # Получаем энергию
        
    elif action == 'block':
        # Блок - уменьшает урон от следующей атаки врага
        block_power = battle_state['player_defense'] // 2 + random.randint(0, 5)
        battle_state['last_action'] = 'block'
        battle_log.append(f"🛡️ *Вы готовитесь к защите:* +{block_power} к блоку")
        battle_state['energy'] = min(3, battle_state['energy'] + 1)
        
    elif action == 'super':
        # Супер-удар в зависимости от расы
        if battle_state['energy'] < 3:
            return 'continue', "❌ Недостаточно энергии!"
        
        race = battle_state['player_race']
        damage = 0
        
        if race == 'human':
            # Человек: двойная атака
            damage = battle_state['player_attack'] * 2
            battle_log.append(f"👑 *СОКРУШИТЕЛЬНЫЙ УДАР ЧЕЛОВЕКА:* {damage} урона!")
            
        elif race == 'elf':
            # Эльф: точный выстрел (игнорирует защиту)
            damage = battle_state['player_attack'] + random.randint(10, 20)
            battle_log.append(f"🎯 *ТОЧНЫЙ ВЫСТРЕЛ ЭЛЬФА:* {damage} урона (игнорирует защиту)!")
            
        elif race == 'orc':
            # Орк: ярость (огромный урон, но теряет здоровье)
            damage = battle_state['player_attack'] * 3
            self_damage = battle_state['player_attack'] // 2
            battle_state['player_health'] -= self_damage
            battle_log.append(f"💢 *ЯРОСТЬ ОРКА:* {damage} урона! (вы теряете {self_damage} HP)")
            
        elif race == 'dwarf':
            # Гном: удар молота (оглушение + урон)
            damage = battle_state['player_attack'] + battle_state['player_defense']
            battle_log.append(f"⚒️ *УДАР МОЛОТА ГНОМА:* {damage} урона! (оглушение)")
            battle_state['monster_stunned'] = True
        
        battle_state['monster_health'] -= damage
        battle_state['energy'] = 0  # Тратим всю энергию
        battle_state['last_action'] = 'super'
        
    elif action == 'potion':
        # Использование зелья
        inventory = db.get_inventory(user_id)
        potions = [item for item in inventory if 'зелье' in item['item_name'].lower()]
        
        if not potions:
            battle_log.append("❌ В инвентаре нет зелий!")
        else:
            # Используем первое малое зелье
            for potion in potions:
                if 'малое' in potion['item_name'].lower():
                    db.use_item(user_id, potion['item_type'], potion['item_name'])
                    heal = 30
                    battle_state['player_health'] = min(
                        battle_state['player_max_health'],
                        battle_state['player_health'] + heal
                    )
                    battle_log.append(f"🧪 *Вы используете Малое зелье:* +{heal} HP")
                    break
        
        battle_state['energy'] = min(3, battle_state['energy'] + 1)
        
    elif action == 'flee':
        # Попытка бегства
        flee_chance = 0.4 + (battle_state['player_health'] / battle_state['player_max_health']) * 0.3
        
        if random.random() < flee_chance:
            battle_log.append("🏃 *Вы успешно сбежали!*")
            return 'fled', "\n".join(battle_log)
        else:
            battle_log.append("❌ *Не удалось сбежать!* Монстр атакует вас в спину!")
            # Монстр получает бонус к атаке при неудачном побеге
            monster_damage = int(monster['attack'] * 1.5)
            battle_state['player_health'] -= max(1, monster_damage - battle_state['player_defense'] // 2)
            battle_log.append(f"💢 *Атака в спину:* {monster_damage} урона")
    
    # Проверяем, жив ли монстр
    if battle_state['monster_health'] <= 0:
        battle_log.append(f"🎉 *{monster['name']} побежден!*")
        return 'player_win', "\n".join(battle_log)
    
    # === ХОД МОНСТРА ===
    # Если монстр оглушен, пропускает ход
    if battle_state.get('monster_stunned'):
        battle_log.append(f"😵 *{monster['name']} оглушен и пропускает ход!*")
        battle_state['monster_stunned'] = False
    else:
        # Монстр может атаковать или использовать спецспособность
        monster_action = random.choice(['attack', 'attack', 'attack', 'special'])
        
        if monster_action == 'attack':
            monster_damage = max(1, monster['attack'] + random.randint(-2, 5))
            
            # Если игрок блокировал в предыдущем ходу
            if battle_state.get('last_action') == 'block':
                block_reduction = battle_state['player_defense'] + random.randint(0, 10)
                monster_damage = max(1, monster_damage - block_reduction)
                battle_log.append(f"🛡️ *Ваш блок поглощает* {block_reduction} урона!")
            
            # Вычитаем защиту игрока
            monster_damage = max(1, monster_damage - battle_state['player_defense'] // 2)
            
            # Критический удар монстра
            if random.random() < 0.1:
                monster_damage = int(monster_damage * 1.7)
                battle_log.append(f"💀 *КРИТИЧЕСКИЙ удар врага:* {monster_damage} урона!")
            else:
                battle_log.append(f"💥 *{monster['name']} атакует:* {monster_damage} урона")
            
            battle_state['player_health'] -= monster_damage
            
        elif monster_action == 'special':
            # Спецспособности монстров
            if battle_state['monster_type'] == 'wolf':
                # Волк: двойная атака
                attacks = 2
                total_damage = 0
                for _ in range(attacks):
                    dmg = max(1, monster['attack'] // 2 + random.randint(0, 3))
                    dmg = max(1, dmg - battle_state['player_defense'] // 3)
                    total_damage += dmg
                
                battle_state['player_health'] -= total_damage
                battle_log.append(f"🐺 *Быстрая атака волка:* {attacks} удара, {total_damage} урона")
                
            elif battle_state['monster_type'] == 'spider':
                # Паук: яд (урон в течение 3 ходов)
                poison_damage = 5
                battle_state['poison'] = battle_state.get('poison', 0) + poison_damage
                battle_state['poison_rounds'] = 3
                battle_log.append(f"🕷️ *{monster['name']} кусает:* яд наносит {poison_damage} урона в раунд")
            
            elif battle_state['monster_type'] == 'bear':
                # Медведь: оглушение
                stun_chance = 0.3
                if random.random() < stun_chance:
                    battle_state['player_stunned'] = True
                    battle_log.append(f"🐻 *Рев медведя:* вы оглушены на следующий ход!")
    
    # Применяем эффекты (яд, оглушение)
    if battle_state.get('poison', 0) > 0 and battle_state.get('poison_rounds', 0) > 0:
        poison_damage = battle_state['poison']
        battle_state['player_health'] -= poison_damage
        battle_state['poison_rounds'] -= 1
        battle_log.append(f"☠️ *Яд наносит* {poison_damage} урона (осталось: {battle_state['poison_rounds']} раундов)")
        
        if battle_state['poison_rounds'] <= 0:
            battle_state['poison'] = 0
    
    # Проверяем, жив ли игрок
    if battle_state['player_health'] <= 0:
        battle_log.append("💀 *Вы пали в бою!*")
        return 'monster_win', "\n".join(battle_log)
    
    # Увеличиваем раунд
    battle_state['round'] += 1
    
    # Сбрасываем последнее действие
    battle_state['last_action'] = None
    
    return 'continue', "\n".join(battle_log)

def end_battle(call, battle_state, result, log_text=""):
    """Завершение боя и начисление наград"""
    user_id = call.from_user.id
    user_data = db.get_user(user_id)
    monster = battle_state['monster']
    
    try:
        if result == 'player_win':
            # Победа игрока
            exp_gained = monster['exp']
            coins_gained = monster['coins']
            
            # Бонусы за быструю победу
            if battle_state['round'] <= 5:
                exp_gained = int(exp_gained * 1.3)
                coins_gained = int(coins_gained * 1.5)
            
            # Начисляем награды
            level_up = db.add_exp(user_id, exp_gained)
            db.add_coins(user_id, coins_gained)
            db.update_user(user_id, health=battle_state['player_health'])
            db.increment_daily_hunts(user_id)
            
            result_text = f"""
🎉 *ВЕЛИКАЯ ПОБЕДА!*

Вы победили *{monster['name']}* за {battle_state['round']} раундов!

🏆 *НАГРАДЫ:*
⭐ Опыт: +{exp_gained}
💰 Золото: +{coins_gained}
❤️ Осталось здоровья: {battle_state['player_health']}
"""
            
            if level_up:
                result_text += "\n✨ *УРОВЕНЬ ПОВЫШЕН!* ✨\n"
            
            # Отправляем изображение победы
            try:
                bot.send_photo(call.message.chat.id, BATTLE_IMAGES['victory'], 
                             caption=result_text, parse_mode='Markdown')
            except:
                bot.send_message(call.message.chat.id, result_text, parse_mode='Markdown')
            
        elif result == 'monster_win':
            # Поражение игрока
            coins_lost = min(30, user_data['coins'] // 3)
            recovered_health = max(1, user_data['max_health'] // 5)
            
            db.update_user(user_id, health=recovered_health)
            db.add_coins(user_id, -coins_lost)
            db.increment_daily_hunts(user_id)
            
            result_text = f"""
💀 *ГЕРОИЧЕСКОЕ ПОРАЖЕНИЕ!*

Вы пали в бою с *{monster['name']}* на {battle_state['round']} раунде.

📉 *ПОТЕРИ:*
💸 Золото: -{coins_lost}
❤️ Здоровье восстановлено до {recovered_health}

🏋️ *СОВЕТ:* Подготовьтесь лучше к следующей битве!
"""
            
            try:
                bot.send_photo(call.message.chat.id, BATTLE_IMAGES['defeat'], 
                             caption=result_text, parse_mode='Markdown')
            except:
                bot.send_message(call.message.chat.id, result_text, parse_mode='Markdown')
            
        elif result == 'fled':
            # Игрок сбежал
            health_lost = user_data['health'] - battle_state['player_health']
            db.update_user(user_id, health=battle_state['player_health'])
            db.increment_daily_hunts(user_id)
            
            result_text = f"""
🏃 *УСПЕШНОЕ БЕГСТВО!*

Вы сбежали от *{monster['name']}*!

💔 Потеряно здоровья: {health_lost}
❤️ Осталось здоровья: {battle_state['player_health']}

⚔️ *Живите, чтобы сражаться в другой день!*
"""
            
            bot.send_message(call.message.chat.id, result_text, parse_mode='Markdown')
        
        # Показываем детали боя
        if log_text:
            battle_details = f"*📜 ДЕТАЛИ БОЯ:*\n\n{log_text}"
            bot.send_message(call.message.chat.id, battle_details, parse_mode='Markdown')
        
        # Возвращаем в главное меню
        time.sleep(1)
        bot.send_message(
            call.message.chat.id,
            "🎮 *Возвращаемся в главное меню*",
            reply_markup=get_main_menu()
        )
        
    except Exception as e:
        print(f"❌ Ошибка при завершении боя: {e}")

# ================== ОБРАБОТЧИКИ КОМАНД ==================
@bot.message_handler(commands=['start'])
def start_command(message):
    user = message.from_user
    user_id = user.id
    
    user_data = db.get_user(user_id)
    
    if user_data:
        if user_data.get('character_name') and user_data.get('race'):
            race_ability = get_race_ability_description(user_data['race'])
            caption = f"""
🎮 Добро пожаловать обратно, *{user_data['character_name']}*!

Вы - *{user_data['race'].capitalize()}* {user_data['level']} уровня.

⚔️ *Расавая способность:*
{race_ability}

*Используйте меню ниже для управления героем!*
            """
            
            try:
                bot.send_photo(message.chat.id, RACE_IMAGES.get(user_data['race'], RACE_IMAGES['human']), 
                             caption=caption, parse_mode='Markdown', reply_markup=get_main_menu())
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
        
        bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown')
        temp_user_data[user_id] = {'step': 'waiting_name'}

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
🎮 *Hero's Path* - RPG игра в Telegram!

*Основные возможности:*
⚔️ *Охота* - интерактивные бои с монстрами
🏋️ *Улучшения* - тратьте очки навыков
🛍️ *Инвентарь* - используйте предметы
🛒 *Магазин* - покупайте зелья и еду
💤 *Отдых* - восстанавливайте здоровье
📊 *Профиль* - статистика персонажа

*Интерактивный бой:*
🗡️ *Атака* - обычная атака, накапливает энергию
🛡️ *Блок* - уменьшает урон от следующей атаки
⚡ *Супер-удар* - мощная расавая способность (требует 3 энергии)
🧪 *Зелье* - использование зелий во время боя
🏃 *Бегство* - попытка сбежать от монстра

*Используйте кнопки меню для игры!*
    """
    
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_text(message):
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
            
            race_text = f"""
*{character_name}, выберите свою расу:*

Каждая раса имеет уникальные характеристики и способности:
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
                if user_id in temp_user_data:
                    del temp_user_data[user_id]
                
                race_names = {
                    'human': '👨 Человек',
                    'elf': '🧝 Эльф',
                    'orc': '👹 Орк',
                    'dwarf': '🧙 Гном'
                }
                
                race_name_display = race_names.get(race, race.capitalize())
                race_ability = get_race_ability_description(race)
                
                welcome_text = f"""
🎉 *Персонаж создан!*

👤 *Имя:* {character_name}
🏹 *Раса:* {race_name_display}

{db.get_race_description(race)}

⚔️ *Расавая способность:*
{race_ability}

*Ваше эпическое приключение начинается!*
                """
                
                try:
                    bot.delete_message(chat_id, message_id)
                except:
                    pass
                
                try:
                    bot.send_photo(chat_id, RACE_IMAGES.get(race, RACE_IMAGES['human']), 
                                 caption=welcome_text, parse_mode='Markdown')
                except:
                    bot.send_message(chat_id, welcome_text, parse_mode='Markdown')
                
                time.sleep(1)
                bot.send_message(
                    chat_id,
                    "🎮 *Используйте кнопки меню для игры!*\n\n"
                    "⚔️ *Охота* - интерактивные бои с монстрами\n"
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
        
        elif call.data.startswith('battle_'):
            battle_callback_handler(call)
        
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
            
            bot.send_message(
                chat_id,
                "🎮 *Главное меню*\n\nВыберите действие:",
                reply_markup=get_main_menu()
            )
    
    except Exception as e:
        print(f"❌ Ошибка в callback_handler: {e}")
        bot.answer_callback_query(call.id, "❌ Произошла ошибка!")

def battle_callback_handler(call):
    """Обработчик действий в бою"""
    user_id = call.from_user.id
    battle_key = f'battle_{user_id}'
    
    if battle_key not in temp_user_data:
        bot.answer_callback_query(call.id, "❌ Бой завершен или не найден!")
        return
    
    battle_state = temp_user_data[battle_key]
    action = call.data.replace('battle_', '')
    
    if action == 'no_energy':
        bot.answer_callback_query(call.id, "❌ Недостаточно энергии для супер-удара!")
        return
    
    # Если игрок оглушен, может использовать только зелье или блок
    if battle_state.get('player_stunned') and action not in ['potion', 'block']:
        bot.answer_callback_query(call.id, "❌ Вы оглушены! Можете только блокировать или использовать зелье.")
        battle_state['player_stunned'] = False
        return
    
    # Обрабатываем действие
    result, log_text = process_battle_action(call, battle_state, action)
    
    if result == 'continue':
        # Обновляем сообщение боя
        update_battle_message(call, battle_state, log_text)
        temp_user_data[battle_key] = battle_state
    elif result in ['player_win', 'monster_win', 'fled']:
        # Завершаем бой
        end_battle(call, battle_state, result, log_text)
        if battle_key in temp_user_data:
            del temp_user_data[battle_key]
    else:
        bot.answer_callback_query(call.id, "❌ Неизвестный результат боя!")

# ================== ФУНКЦИИ МЕНЮ ==================
def show_profile(message):
    user_id = message.from_user.id
    
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
    
    # Описание расовой способности
    race_ability = get_race_ability_description(user_data.get('race', ''))
    
    profile_text = f"""
📊 *ПРОФИЛЬ ГЕРОЯ*

👤 *{user_data['character_name']}*
🏹 *Раса:* {user_data['race'].capitalize() if user_data['race'] else 'Не выбрана'}

{health_bar} {user_data['health']}/{user_data['max_health']}

⚔️ *Характеристики:*
📊 Уровень: {user_data['level']}
⭐ Опыт: {user_data['exp']}/{user_data['exp_to_next_level']}
🔶 Очки навыков: {user_data['skill_points']}
💰 Золото: {user_data['coins']}
🗡️ Атака: {user_data['attack']}
🛡️ Защита: {user_data['defense']}

🎯 *Охота сегодня:* {hunts_text}

⚡ *Расавая способность:*
{race_ability}
    """
    
    try:
        bot.send_photo(
            message.chat.id,
            RACE_IMAGES.get(user_data.get('race', 'human'), RACE_IMAGES['human']),
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

Выберите противника для интерактивного боя:

🐀 *Крыса* - слабый монстр, идеален для новичков
🐺 *Волк* - быстрый и опасный хищник
🐗 *Кабан* - мощный боец средней сложности
🐻 *Медведь* - сильный и выносливый враг
🕷️ *Паук* - легендарный босс, только для сильнейших!

🎯 *Охот сегодня:* {hunts_done}/{max_hunts}
⚡ *В бою используйте энергию для супер-удара!*
    """
    
    bot.send_message(
        message.chat.id,
        hunt_text,
        parse_mode='Markdown',
        reply_markup=get_hunt_keyboard()
    )

def hunt_monster(call, monster_type):
    """Начало интерактивного боя"""
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
    
    # Данные монстров
    monsters = {
        'rat': {
            'name': '🐀 Крыса', 
            'health': 25, 
            'attack': 8, 
            'defense': 2, 
            'exp': 10, 
            'coins': 5,
            'description': 'Маленькая, но опасная тварь из подземелий'
        },
        'wolf': {
            'name': '🐺 Волк', 
            'health': 50, 
            'attack': 15, 
            'defense': 5, 
            'exp': 20, 
            'coins': 12,
            'description': 'Быстрый и безжалостный хищник лесов'
        },
        'boar': {
            'name': '🐗 Кабан', 
            'health': 85, 
            'attack': 20, 
            'defense': 8, 
            'exp': 35, 
            'coins': 20,
            'description': 'Мощный зверь с острыми клыками'
        },
        'bear': {
            'name': '🐻 Медведь', 
            'health': 140, 
            'attack': 30, 
            'defense': 12, 
            'exp': 50, 
            'coins': 35,
            'description': 'Грозный хозяин леса, сокрушающий врагов'
        },
        'spider': {
            'name': '🕷️ Гигантский паук', 
            'health': 180, 
            'attack': 35, 
            'defense': 15, 
            'exp': 80, 
            'coins': 60,
            'description': 'Гигантский паук из тёмных пещер, опутывающий добычу паутиной'
        }
    }
    
    monster = monsters.get(monster_type, monsters['rat'])
    
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    
    # Создаем состояние боя
    battle_state = {
        'user_id': user_id,
        'monster_type': monster_type,
        'monster': monster,
        'player_health': user_data['health'],
        'monster_health': monster['health'],
        'player_max_health': user_data['max_health'],
        'player_attack': user_data['attack'],
        'player_defense': user_data['defense'],
        'player_race': user_data['race'],
        'round': 1,
        'energy': 0,  # Энергия для супер-удара
        'last_action': None
    }
    
    # Сохраняем состояние боя
    temp_user_data[f'battle_{user_id}'] = battle_state
    
    # Отправляем изображение монстра и клавиатуру боя
    monster_image_url = MONSTER_IMAGES.get(monster_type, MONSTER_IMAGES['rat'])
    battle_start_text = f"""
⚔️ *НАЧАЛО БИТВЫ!*

Вы встретили *{monster['name']}*!
{monster['description']}

*Характеристики врага:*
❤️ Здоровье: {monster['health']}
🗡️ Атака: {monster['attack']}
🛡️ Защита: {monster['defense']}

*Ваши характеристики:*
❤️ Здоровье: {user_data['health']}/{user_data['max_health']}
🗡️ Атака: {user_data['attack']}
🛡️ Защита: {user_data['defense']}
⚡ Энергия: ○○○ (0/3)

*Выберите действие для первого раунда:*
"""
    
    try:
        bot.send_photo(call.message.chat.id, monster_image_url, 
                      caption=battle_start_text, parse_mode='Markdown',
                      reply_markup=get_battle_keyboard(battle_state))
    except:
        bot.send_message(call.message.chat.id, battle_start_text, 
                       parse_mode='Markdown', reply_markup=get_battle_keyboard(battle_state))

def show_upgrade_menu(message):
    user_id = message.from_user.id
    
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
    
    bot.send_message(
        message.chat.id,
        upgrade_text,
        parse_mode='Markdown',
        reply_markup=get_upgrade_keyboard()
    )

def upgrade_stat(call, stat):
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
        
        bot.send_message(
            call.message.chat.id,
            result_text,
            parse_mode='Markdown'
        )
    else:
        bot.answer_callback_query(call.id, "❌ Ошибка при улучшении!")

def show_inventory(message):
    user_id = message.from_user.id
    
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
    
    bot.send_message(
        message.chat.id,
        inventory_text,
        parse_mode='Markdown'
    )
    
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
    user_id = message.from_user.id
    
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
    
    bot.send_message(
        message.chat.id,
        shop_text,
        parse_mode='Markdown',
        reply_markup=get_shop_keyboard()
    )

def buy_item(call, item):
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
        
        bot.send_message(
            call.message.chat.id,
            result_text,
            parse_mode='Markdown'
        )
    else:
        bot.answer_callback_query(call.id, "❌ Ошибка при покупке!")

def use_item(call, item):
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
        
        bot.send_message(
            call.message.chat.id,
            result_text,
            parse_mode='Markdown'
        )
    else:
        bot.answer_callback_query(call.id, "❌ У вас нет этого предмета!")

def show_rest_menu(message):
    user_id = message.from_user.id
    
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
    
    bot.send_message(
        message.chat.id,
        rest_text,
        parse_mode='Markdown',
        reply_markup=get_rest_keyboard()
    )

def rest_action(call, rest_type):
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
    
    bot.send_message(
        call.message.chat.id,
        result_text,
        parse_mode='Markdown'
    )

def show_stats(message):
    """Показать статистику сервера"""
    conn = None
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
        
    except Exception as e:
        print(f"❌ Ошибка в show_stats: {e}")
        bot.send_message(
            message.chat.id,
            "❌ Ошибка при получении статистики",
            reply_markup=get_main_menu()
        )
    finally:
        if conn:
            conn.close()

# ================== ЗАПУСК БОТА ==================
def main():
    print("=" * 50)
    print("🎮 БОТ 'Hero's Path' ЗАПУЩЕН")
    print("=" * 50)
    
   def start_polling():
        print("🔄 Запуск polling с защитой от конфликтов...")
        
        # Первая попытка - пропустить обновления
        try:
            bot.get_updates(offset=-1, timeout=1)
        except:
            pass  # Игнорируем ошибки
        
        # Запускаем polling с параметрами для Railway
        bot.infinity_polling(
            skip_pending=True,  # Важно!
            timeout=30,
            long_polling_timeout=5,
            logger_level="INFO",
            allowed_updates=None
        )
    
    return start_polling  # Возвращаем функцию для запуска

# В конце main.py вместо прямого вызова:
if __name__ == "__main__":
    start_func = main()
    start_func()
